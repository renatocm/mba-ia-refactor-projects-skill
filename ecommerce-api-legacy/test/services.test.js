const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const { randomBytes } = require('node:crypto');
const { createApp } = require('../src/create-app');
const { loadConfig } = require('../src/config');
const { hashPassword, verifyPassword } = require('../src/security/passwords');
const { authService } = require('../src/services/auth');
const { userRepository } = require('../src/repositories/users');
const { sessionRepository } = require('../src/repositories/sessions');
const { reportRepository } = require('../src/repositories/reports');
const { report } = require('../src/presenters');
const { createDatabase } = require('../src/database');

let runtime;
const password = 'senha-segura-para-teste';
const data = (email = 'student@example.test', courseId = 1) => ({ usr: 'Pessoa Teste', eml: email, pwd: password, c_id: courseId, card: '4111222233334444' });
beforeEach(async () => { runtime = await createApp({ config: loadConfig({}), logger: { error() {} } }); });
afterEach(() => runtime.close());
const status = code => error => error.status === code;
function counts() {
    return ['users', 'enrollments', 'payments', 'audit_logs'].map(table => runtime.db.get(`SELECT COUNT(*) AS n FROM ${table}`).n);
}

test('scrypt has random salts, verifies passwords and rejects legacy pseudo-hashes', async () => {
    const one = await hashPassword(password), two = await hashPassword(password);
    assert.notEqual(one, two);
    assert.equal(await verifyPassword(password, one), true);
    assert.equal(await verifyPassword('outra-senha', one), false);
    assert.equal(await verifyPassword(password, 'c2c2c2c2c2'), false);
    assert.equal(one.includes(password), false);
});

test('checkout creates consistent records and validates identity for existing email', async () => {
    const result = await runtime.services.checkout.execute(data());
    assert.equal(result.paymentMode, 'demo');
    assert.deepEqual(counts(), [1, 1, 1, 1]);
    const user = runtime.db.get('SELECT * FROM users');
    assert.equal(await verifyPassword(password, user.password_hash), true);
    await assert.rejects(runtime.services.checkout.execute({ ...data(undefined, 2), pwd: 'outra-senha' }), status(401));
    await runtime.services.checkout.execute(data(undefined, 2));
    assert.deepEqual(counts(), [1, 2, 2, 2]);
    await assert.rejects(runtime.services.checkout.execute(data()), status(409));
    assert.deepEqual(counts(), [1, 2, 2, 2]);
});

test('all malformed checkout inputs are rejected before data access', async () => {
    const original = runtime.db.get;
    let reads = 0;
    runtime.db.get = (...args) => { reads++; return original(...args); };
    const variants = [null, [], 1, {}, ...[
        { card: 4111222233334444 }, { card: true }, { card: '4' }, { card: {} }, { card: null },
        { pwd: true }, { pwd: null }, { pwd: '123' }, { pwd: 'a'.repeat(1025) },
        { c_id: '1' }, { c_id: 0 }, { c_id: -1 }, { c_id: 1.5 }, { c_id: true }, { c_id: Number.MAX_SAFE_INTEGER + 1 },
        { usr: null }, { usr: 'a' }, { eml: 'invalid' }, { eml: {} }
    ].map(change => ({ ...data(), ...change }))];
    for (const input of variants) await assert.rejects(runtime.services.checkout.execute(input), status(400));
    assert.equal(reads, 0);
});

test('denied payment and missing/inactive courses cause no writes', async () => {
    await assert.rejects(runtime.services.checkout.execute({ ...data(), card: '5111222233334444' }), status(400));
    await assert.rejects(runtime.services.checkout.execute(data(undefined, 999)), status(404));
    runtime.db.run('UPDATE courses SET active=0 WHERE id=1');
    await assert.rejects(runtime.services.checkout.execute(data()), status(404));
    assert.deepEqual(counts(), [0, 0, 0, 0]);
});

test('rollback after each checkout write leaves no partial data and next operation succeeds', async () => {
    const original = runtime.db.run;
    for (const table of ['users', 'enrollments', 'payments', 'audit_logs']) {
        runtime.db.run = (sql, args) => {
            const result = original(sql, args);
            if (sql.startsWith(`INSERT INTO ${table}(`)) throw new Error('failure after write');
            return result;
        };
        await assert.rejects(runtime.services.checkout.execute(data()), /failure after write/);
        runtime.db.run = original;
        assert.deepEqual(counts(), [0, 0, 0, 0]);
    }
    await runtime.services.checkout.execute(data());
    assert.deepEqual(counts(), [1, 1, 1, 1]);
});

test('concurrent same-email checkouts create only one user and enrollment', async () => {
    const results = await Promise.allSettled([runtime.services.checkout.execute(data()), runtime.services.checkout.execute(data())]);
    assert.equal(results.filter(r => r.status === 'fulfilled').length, 1);
    assert.equal(results.find(r => r.status === 'rejected').reason.status, 409);
    assert.deepEqual(counts(), [1, 1, 1, 1]);
});

test('concurrent different accounts are isolated when one checkout fails', async () => {
    const original = runtime.db.run;
    let inserted = 0;
    runtime.db.run = (sql, args) => {
        const result = original(sql, args);
        if (sql.startsWith('INSERT INTO audit_logs') && inserted++ === 0) throw new Error('first transaction fails');
        return result;
    };
    const results = await Promise.allSettled([runtime.services.checkout.execute(data('one@example.test')), runtime.services.checkout.execute(data('two@example.test'))]);
    runtime.db.run = original;
    assert.equal(results.filter(r => r.status === 'fulfilled').length, 1);
    assert.deepEqual(counts(), [1, 1, 1, 1]);
    assert.deepEqual(runtime.db.all('PRAGMA foreign_key_check'), []);
});

test('email uniqueness is case insensitive and public registration cannot assign admin', async () => {
    const user = await runtime.services.auth.register({ ...data(), role: 'admin' });
    assert.equal(user.role, 'student');
    await assert.rejects(runtime.services.auth.register({ ...data(), eml: 'STUDENT@example.test' }), status(409));
});

test('sessions expire, reject tampering, revoke on login, and follow current role', async () => {
    await runtime.services.auth.register(data());
    const users = userRepository(runtime.db), sessions = sessionRepository(runtime.db);
    let now = 1000;
    const auth = authService({ db: runtime.db, users, sessions, sessionTtl: 60, dummyHash: await hashPassword(randomBytes(16).toString('hex')), now: () => now });
    const first = await auth.login(data());
    const header = 'Bearer ' + first.token;
    assert.equal(auth.authenticate(header).role, 'student');
    assert.throws(() => auth.authenticate(header + 'x'), status(401));
    assert.throws(() => auth.authenticate('Bearer ' + 'a'.repeat(43)), status(401));
    const stored = runtime.db.get('SELECT token_hash FROM sessions');
    assert.notEqual(stored.token_hash, first.token);
    runtime.db.run("UPDATE users SET role='admin' WHERE id=?", [first.user.id]);
    assert.equal(auth.authenticate(header).role, 'admin');
    now += 60001;
    assert.throws(() => auth.authenticate(header), status(401));
    now = 1000;
    const second = await auth.login(data());
    assert.throws(() => auth.authenticate(header), status(401));
    assert.equal(auth.authenticate('Bearer ' + second.token).id, first.user.id);
    runtime.db.run('DELETE FROM users WHERE id=?', [first.user.id]);
    assert.throws(() => auth.authenticate('Bearer ' + second.token), status(401));
    assert.equal(runtime.db.get('SELECT COUNT(*) AS n FROM sessions').n, 0);
});

test('wrong password and SQL-looking email do not authenticate', async () => {
    await runtime.services.auth.register(data());
    await assert.rejects(runtime.services.auth.login({ ...data(), pwd: 'senha-errada' }), status(401));
    await assert.rejects(runtime.services.auth.login({ ...data(), eml: "student@example.test'OR'1'='1" }), status(401));
    const strange = "Pessoa d'água'; DROP TABLE users; --";
    await runtime.services.auth.register({ ...data('quote@example.test'), usr: strange });
    assert.equal(runtime.db.get('SELECT name FROM users WHERE email=?', ['quote@example.test']).name, strange);
});

test('deletion requires admin and protects history, reports missing user and revokes sessions', async () => {
    const user = await runtime.services.auth.register(data());
    const admin = { id: 999, role: 'admin' };
    assert.throws(() => runtime.services.users.remove(user.id, null), status(401));
    assert.throws(() => runtime.services.users.remove(user.id, user), status(403));
    assert.throws(() => runtime.services.users.remove(999, admin), status(404));
    const login = await runtime.services.auth.login(data());
    runtime.services.users.remove(user.id, admin);
    assert.throws(() => runtime.services.auth.authenticate('Bearer ' + login.token), status(401));
    await runtime.services.checkout.execute(data());
    const enrolled = runtime.db.get('SELECT id FROM users');
    assert.throws(() => runtime.services.users.remove(enrolled.id, admin), status(409));
    assert.deepEqual(runtime.db.all('PRAGMA foreign_key_check'), []);
});

test('database constraints independently reject orphans, duplicates and invalid amounts', async () => {
    await runtime.services.checkout.execute(data());
    for (const [sql, args] of [
        ['INSERT INTO enrollments(user_id,course_id) VALUES (?,?)', [999, 1]],
        ['INSERT INTO enrollments(user_id,course_id) VALUES (?,?)', [1, 1]],
        ['INSERT INTO payments(enrollment_id,amount,status,mode) VALUES (?,?,?,?)', [999, 10, 'PAID', 'demo']],
        ['UPDATE payments SET amount=?', [-1]],
        ['DELETE FROM users WHERE id=?', [1]]
    ]) assert.throws(() => runtime.db.run(sql, args));
    assert.deepEqual(runtime.db.all('PRAGMA foreign_key_check'), []);
});

test('financial report uses two data queries, preserves zero courses and paginates students', async () => {
    for (let i = 0; i < 3; i++) await runtime.services.checkout.execute(data(`student${i}@example.test`));
    const original = runtime.db.all;
    let queries = 0;
    runtime.db.all = (...args) => { queries++; return original(...args); };
    const payload = runtime.services.reports.financial({ students_per_page: '1', student_page: '2' }, { role: 'admin' });
    assert.equal(queries, 2);
    const dto = report(payload);
    assert.equal(dto[0].revenue, 3 * 997);
    assert.equal(dto[0].students.length, 1);
    assert.deepEqual(dto[1], { course: 'Docker', revenue: 0, students: [] });
    queries = 0;
    const page = runtime.services.reports.financial({ per_page: '1', page: '2' }, { role: 'admin' });
    assert.equal(page.courses[0].title, 'Docker');
    assert.equal(queries, 2);
    assert.throws(() => runtime.services.reports.financial({}, { role: 'student' }), status(403));
    assert.throws(() => runtime.services.reports.financial({ per_page: '101' }, { role: 'admin' }), status(400));
    assert.equal(reportRepository(runtime.db).financial({ page: 999, limit: 20, studentPage: 1, studentLimit: 50 }).courses.length, 0);
});

test('report sums paid revenue while retaining paid amount field and no duplicated payments', async () => {
    await runtime.services.checkout.execute(data());
    runtime.db.run("UPDATE payments SET status='DENIED'");
    const dto = report(runtime.services.reports.financial({}, { role: 'admin' }));
    assert.equal(dto[0].revenue, 0);
    assert.equal(dto[0].students[0].paid, 997);
    assert.throws(() => runtime.db.run("INSERT INTO payments(enrollment_id,amount,status,mode) VALUES (1,997,'PAID','demo')"));
});

test('configuration rejects production, real gateway and incomplete admin credentials', () => {
    assert.throws(() => loadConfig({ NODE_ENV: 'production' }));
    assert.throws(() => loadConfig({ PAYMENT_MODE: 'real' }));
    assert.throws(() => loadConfig({ ADMIN_EMAIL: 'admin@example.test' }));
    assert.throws(() => loadConfig({ PORT: 'invalid' }));
    assert.throws(() => loadConfig({ SESSION_TTL_SECONDS: '0' }));
    assert.equal(loadConfig({}).paymentMode, 'demo');
    assert.equal(loadConfig({}).admin, null);
});

test('database connections are scoped to runtime and close cleanly', () => {
    const other = createDatabase();
    assert.equal(other.get('SELECT COUNT(*) AS n FROM courses').n, 0);
    other.close();
    assert.throws(() => other.get('SELECT 1'));
    assert.equal(runtime.db.get('SELECT COUNT(*) AS n FROM courses').n, 2);
});

test('central handler redacts unexpected errors and classifies parsing failures', () => {
    const { errorHandler } = require('../src/middleware/errors');
    const entries = [];
    const handler = errorHandler({ error: entry => entries.push(entry) });
    const res = { headersSent: false, status(code) { this.code = code; return this; }, json(body) { this.body = body; return this; }, set() { return this; } };
    handler(new Error('SQL password 4111222233334444'), {}, res, () => {});
    assert.equal(res.code, 500);
    assert.equal(res.body.error, 'Erro interno');
    assert.ok(res.body.reference);
    assert.equal(JSON.stringify(entries).includes('4111222233334444'), false);
    assert.equal(JSON.stringify(res.body).includes('password'), false);
    for (const [error, expected] of [[{ type: 'entity.parse.failed' }, 400], [{ type: 'entity.too.large' }, 413], [{ status: 415 }, 415]]) {
        handler(error, {}, res, () => {});
        assert.equal(res.code, expected);
    }
});
