const presenters = require('../presenters');
const validation = require('../models/validation');
function controllers(services) {
    return {
        async checkout(req, res) {
            res.status(200).json(presenters.checkout(await services.checkout.execute(req.body)));
        },
        report(req, res) {
            const result = services.reports.financial(req.query, req.actor);
            res.set({ 'X-Page': String(result.pagination.page), 'X-Per-Page': String(result.pagination.limit),
                'X-Student-Page': String(result.pagination.studentPage), 'X-Students-Per-Page': String(result.pagination.studentLimit) });
            res.json(presenters.report(result));
        },
        removeUser(req, res) {
            services.users.remove(validation.pathId(req.params.id), req.actor);
            res.status(200).type('text').send('Usuário deletado.');
        },
        async register(req, res) {
            res.status(201).json({ user: presenters.user(await services.auth.register(req.body)) });
        },
        async login(req, res) {
            const result = await services.auth.login(req.body);
            res.set('Cache-Control', 'no-store').json({ user: presenters.user(result.user),
                token: result.token, token_type: 'Bearer', expires_in: result.expiresIn });
        }
    };
}
module.exports = { controllers };
