const { requireAdmin } = require('./policy');
const validation = require('../models/validation');
function reportService({ reports }) {
    return {
        financial(query, actor) {
            const pagination = validation.pagination(query);
            requireAdmin(actor);
            return { ...reports.financial(pagination), pagination };
        }
    };
}
module.exports = { reportService };
