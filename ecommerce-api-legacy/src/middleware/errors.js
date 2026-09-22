const { randomUUID } = require('node:crypto');
const { AppError } = require('../models/errors');
const asyncHandler = handler => (req, res, next) => Promise.resolve().then(() => handler(req, res, next)).catch(next);
function errorHandler(logger) {
    return (error, req, res, next) => {
        if (res.headersSent) return next(error);
        if (error instanceof AppError) {
            if (error.status === 401) res.set('WWW-Authenticate', 'Bearer');
            return res.status(error.status).json({ error: error.message });
        }
        if (error.type === 'entity.parse.failed') return res.status(400).json({ error: 'JSON inválido' });
        if (error.type === 'entity.too.large') return res.status(413).json({ error: 'Corpo muito grande' });
        if (error.status === 415) return res.status(415).json({ error: 'Formato ou codificação não suportados' });
        const reference = randomUUID();
        // Never log message/stack/body/headers: they may contain SQL, credentials or card data.
        logger.error({ event: 'request_failed', reference, type: error.name || 'Error' });
        return res.status(500).json({ error: 'Erro interno', reference });
    };
}
module.exports = { asyncHandler, errorHandler };
