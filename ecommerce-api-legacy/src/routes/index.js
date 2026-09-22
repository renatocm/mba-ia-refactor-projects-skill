const { Router } = require('express');
const { asyncHandler } = require('../middleware/errors');
const { administrator } = require('../middleware/auth');
const { AppError } = require('../models/errors');
function routes(controllers, auth) {
    const router = Router();
    const json = (req, res, next) => req.is('application/json') ? next() : next(new AppError(415, 'Envie Content-Type application/json'));
    const admin = administrator(auth);
    router.post('/checkout', json, asyncHandler(controllers.checkout));
    router.get('/admin/financial-report', admin, asyncHandler(controllers.report));
    router.delete('/users/:id', admin, asyncHandler(controllers.removeUser));
    router.post('/auth/register', json, asyncHandler(controllers.register));
    router.post('/auth/login', json, asyncHandler(controllers.login));
    return router;
}
module.exports = { routes };
