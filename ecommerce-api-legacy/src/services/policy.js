const { AppError } = require('../models/errors');
function requireAdmin(actor) {
    if (!actor) throw new AppError(401, 'Autenticação necessária');
    if (actor.role !== 'admin') throw new AppError(403, 'Acesso não permitido');
}
module.exports = { requireAdmin };
