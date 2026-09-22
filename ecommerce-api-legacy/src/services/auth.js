const { randomBytes, createHash } = require('node:crypto');
const { AppError } = require('../models/errors');
const { hashPassword, verifyPassword } = require('../security/passwords');
const validation = require('../models/validation');

const digest = token => createHash('sha256').update(token).digest('hex');
function authService({ db, users, sessions, sessionTtl, dummyHash, now = () => Date.now() }) {
    return {
        async register(input) {
            const data = validation.registration(input);
            const passwordHash = await hashPassword(data.password);
            return db.transaction(() => {
                if (users.byEmail(data.email)) throw new AppError(409, 'Email já cadastrado');
                const id = users.create({ name: data.name, email: data.email, passwordHash });
                return users.byId(id);
            });
        },
        async login(input) {
            const data = validation.credentials(input);
            const user = users.byEmail(data.email);
            const valid = await verifyPassword(data.password, user ? user.password_hash : dummyHash);
            if (!user || !valid) throw new AppError(401, 'Credenciais inválidas');
            const token = randomBytes(32).toString('base64url');
            db.transaction(() => {
                // Recheck after asynchronous KDF; account may have been deleted meanwhile.
                if (!users.byId(user.id)) throw new AppError(401, 'Credenciais inválidas');
                sessions.create(digest(token), user.id, now() + sessionTtl * 1000, now());
            });
            return { user, token, expiresIn: sessionTtl };
        },
        authenticate(header) {
            if (typeof header !== 'string' || !/^Bearer [A-Za-z0-9_-]{43}$/i.test(header)) throw new AppError(401, 'Autenticação necessária');
            const user = sessions.find(digest(header.slice(7)), now());
            if (!user) throw new AppError(401, 'Token inválido ou expirado');
            return user;
        }
    };
}
module.exports = { authService };
