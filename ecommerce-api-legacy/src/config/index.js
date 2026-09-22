const validation = require('../models/validation');

function loadConfig(env = process.env) {
    const number = (name, fallback, min, max) => {
        const raw = env[name] === undefined ? String(fallback) : env[name];
        if (!/^\d+$/.test(raw)) throw new Error(`Configuração ${name} inválida`);
        const value = Number(raw);
        if (!Number.isSafeInteger(value) || value < min || value > max) throw new Error(`Configuração ${name} inválida`);
        return value;
    };
    if (env.NODE_ENV === 'production') throw new Error('Aplicação somente demonstrativa; pagamento real não implementado');
    if (env.PAYMENT_MODE && env.PAYMENT_MODE !== 'demo') throw new Error('Somente PAYMENT_MODE=demo é suportado');
    let admin = null;
    if (env.ADMIN_EMAIL || env.ADMIN_PASSWORD) {
        try {
            admin = { email: validation.email(env.ADMIN_EMAIL), password: validation.password(env.ADMIN_PASSWORD), name: 'Administrador' };
        } catch {
            throw new Error('ADMIN_EMAIL e ADMIN_PASSWORD devem ser válidos e fornecidos juntos');
        }
    }
    return { port: number('PORT', 3000, 0, 65535), host: env.HOST || '127.0.0.1',
        sessionTtl: number('SESSION_TTL_SECONDS', 3600, 60, 86400), paymentMode: 'demo', admin };
}
module.exports = { loadConfig };
