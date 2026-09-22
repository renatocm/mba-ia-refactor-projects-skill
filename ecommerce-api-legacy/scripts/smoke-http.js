/* Real network validation of the documented entry point; no production data/files. */
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const { randomBytes } = require('node:crypto');
const { once } = require('node:events');
const path = require('node:path');

async function smoke() {
    const password = randomBytes(24).toString('base64url');
    const child = spawn(process.execPath, ['src/app.js'], {
        cwd: path.join(__dirname, '..'),
        env: { ...process.env, PORT: '0', HOST: '127.0.0.1', NODE_ENV: 'test', PAYMENT_MODE: 'demo',
            ADMIN_EMAIL: 'admin@example.test', ADMIN_PASSWORD: password, SESSION_TTL_SECONDS: '3600' },
        stdio: ['ignore', 'pipe', 'pipe']
    });
    const exited = once(child, 'exit');
    let output = '', errors = '';
    child.stdout.on('data', chunk => { output += chunk; });
    child.stderr.on('data', chunk => { errors += chunk; });
    const results = [];
    try {
        const port = await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => reject(new Error('Servidor não ficou pronto')), 15000);
            const check = () => {
                const match = output.match(/LMS DEMO pronto em http:\/\/127\.0\.0\.1:(\d+)/);
                if (match) { clearTimeout(timeout); resolve(match[1]); }
            };
            child.stdout.on('data', check);
            child.once('exit', () => { clearTimeout(timeout); reject(new Error('Servidor encerrou antes da prontidão')); });
            child.once('error', error => { clearTimeout(timeout); reject(error); });
        });
        const base = `http://127.0.0.1:${port}`;
        async function request(method, route, expected, body, token) {
            const headers = { 'Content-Type': 'application/json' };
            if (token) headers.Authorization = `Bearer ${token}`;
            const response = await fetch(base + route, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(5000) });
            const payload = await response.text();
            results.push({ method, path: route, status: response.status, expected });
            assert.equal(response.status, expected, `${method} ${route}`);
            assert.equal(response.headers.get('x-payment-mode'), 'demo');
            return { data: response.headers.get('content-type').includes('application/json') ? JSON.parse(payload) : payload, headers: response.headers };
        }
        const checkout = { usr: 'Pessoa HTTP', eml: 'http@example.test', pwd: password, c_id: 1, card: '4111222233334444' };
        await request('GET', '/api/admin/financial-report', 401);
        await request('DELETE', '/api/users/999', 401);
        const login = await request('POST', '/api/auth/login', 200, { eml: 'admin@example.test', pwd: password });
        const admin = login.data.token;
        assert.equal(login.headers.get('cache-control'), 'no-store');
        await request('POST', '/api/auth/login', 401, { eml: 'admin@example.test', pwd: 'incorrect-password' });
        const enrolled = await request('POST', '/api/checkout', 200, checkout);
        assert.ok(enrolled.data.enrollment_id);
        assert.equal(enrolled.data.payment_mode, 'demo');
        await request('POST', '/api/checkout', 401, { ...checkout, pwd: 'incorrect-password', c_id: 2 });
        await request('POST', '/api/checkout', 409, checkout);
        await request('POST', '/api/checkout', 400, { ...checkout, card: 4111222233334444 });
        await request('POST', '/api/checkout', 400, { ...checkout, pwd: true });
        await request('POST', '/api/checkout', 404, { ...checkout, c_id: 999 });
        await request('POST', '/api/checkout', 400, { ...checkout, eml: 'denied@example.test', card: '5111222233334444' });
        await request('POST', '/api/auth/login', 401, { eml: 'denied@example.test', pwd: password });
        const student = (await request('POST', '/api/auth/login', 200, { eml: checkout.eml, pwd: password })).data;
        await request('GET', '/api/admin/financial-report', 403, undefined, student.token);
        await request('DELETE', '/api/users/999', 403, undefined, student.token);
        await request('GET', '/api/admin/financial-report', 401, undefined, admin + 'x');
        const report = await request('GET', '/api/admin/financial-report', 200, undefined, admin);
        assert.deepEqual(report.data, [
            { course: 'Clean Architecture', revenue: 997, students: [{ student: checkout.usr, paid: 997 }] },
            { course: 'Docker', revenue: 0, students: [] }
        ]);
        assert.equal(report.headers.get('x-per-page'), '20');
        await request('GET', '/api/admin/financial-report?per_page=0', 400, undefined, admin);
        await request('GET', '/api/admin/financial-report?page=999', 200, undefined, admin);
        await request('DELETE', `/api/users/${student.user.id}`, 409, undefined, admin);
        await request('DELETE', '/api/users/999', 404, undefined, admin);
        await request('DELETE', '/api/users/not-an-id', 400, undefined, admin);
        const registration = await request('POST', '/api/auth/register', 201, { usr: 'Excluir Pessoa', eml: 'delete@example.test', pwd: password, role: 'admin' });
        assert.equal(registration.data.user.role, 'student');
        assert.equal('password_hash' in registration.data.user, false);
        await request('POST', '/api/auth/register', 409, { usr: 'Excluir Pessoa', eml: 'DELETE@example.test', pwd: password });
        await request('DELETE', `/api/users/${registration.data.user.id}`, 200, undefined, admin);
        await request('POST', '/api/auth/login', 401, { eml: 'delete@example.test', pwd: password });
        const malformed = await fetch(base + '/api/checkout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{', signal: AbortSignal.timeout(5000) });
        assert.equal(malformed.status, 400);
        await malformed.text();
        results.push({ method: 'POST', path: '/api/checkout (malformed JSON)', status: 400, expected: 400 });
        await request('GET', '/api/admin/financial-report', 200, undefined, admin);
        for (const value of [password, admin, checkout.card, '5111222233334444', checkout.eml]) {
            assert.equal((output + errors).includes(value), false, 'Dados sensíveis encontrados nos logs');
        }
    } finally {
        if (child.exitCode === null && child.signalCode === null) child.kill('SIGTERM');
        const timeout = setTimeout(() => child.kill('SIGKILL'), 5000);
        await exited;
        clearTimeout(timeout);
    }
    assert.equal(child.exitCode, 0, 'Servidor deve encerrar graciosamente');
    console.log(JSON.stringify({ boot: 'ok', server_stopped: true, database: ':memory:', payment_mode: 'demo', logs_redacted: true, requests: results }, null, 2));
}
if (require.main === module) smoke().catch(() => { console.error('Falha na validação HTTP; nenhum segredo foi registrado'); process.exitCode = 1; });
module.exports = { smoke };
