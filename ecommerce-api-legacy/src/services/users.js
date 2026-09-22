const { AppError } = require('../models/errors');
const { requireAdmin } = require('./policy');
const validation = require('../models/validation');

function userService({ db, users }) {
    return {
        remove(id, actor) {
            validation.id(id);
            requireAdmin(actor);
            return db.transaction(() => {
                if (!users.byId(id)) throw new AppError(404, 'Usuário não encontrado');
                if (users.hasEnrollments(id)) throw new AppError(409, 'Usuário possui matrículas; histórico preservado');
                if (id === actor.id) throw new AppError(409, 'Administrador não pode excluir a própria conta');
                if (users.delete(id) !== 1) throw new AppError(404, 'Usuário não encontrado');
            });
        }
    };
}
module.exports = { userService };
