const { requireAdmin } = require('../services/policy');
function administrator(auth) {
    return (req, res, next) => {
        try {
            req.actor = auth.authenticate(req.get('Authorization'));
            requireAdmin(req.actor);
            next();
        } catch (error) { next(error); }
    };
}
module.exports = { administrator };
