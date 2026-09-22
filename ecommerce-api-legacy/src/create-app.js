const express = require('express');
const { randomBytes } = require('node:crypto');
const { loadConfig } = require('./config');
const { createDatabase } = require('./database');
const { seedDemo } = require('./database/seed');
const { hashPassword } = require('./security/passwords');
const { userRepository } = require('./repositories/users');
const { checkoutRepository } = require('./repositories/checkout');
const { sessionRepository } = require('./repositories/sessions');
const { reportRepository } = require('./repositories/reports');
const { authService } = require('./services/auth');
const { checkoutService } = require('./services/checkout');
const { userService } = require('./services/users');
const { reportService } = require('./services/reports');
const { DemoPaymentGateway } = require('./payments/demo');
const { controllers } = require('./controllers');
const { routes } = require('./routes');
const { errorHandler } = require('./middleware/errors');

async function createApp({ config = loadConfig(), logger = console } = {}) {
    const db = createDatabase();
    try {
        await seedDemo(db, config.admin);
        const users = userRepository(db);
        const auth = authService({ db, users, sessions: sessionRepository(db), sessionTtl: config.sessionTtl,
            dummyHash: await hashPassword(randomBytes(32).toString('hex')) });
        const services = { auth,
            checkout: checkoutService({ db, users, checkout: checkoutRepository(db), gateway: new DemoPaymentGateway() }),
            users: userService({ db, users }), reports: reportService({ reports: reportRepository(db) }) };
        const app = express();
        app.disable('x-powered-by');
        app.use((req, res, next) => { res.set('X-Payment-Mode', 'demo'); next(); });
        app.use(express.json({ limit: '16kb' }));
        app.use('/api', routes(controllers(services), auth));
        app.use((req, res) => res.status(404).json({ error: 'Recurso não encontrado' }));
        app.use(errorHandler(logger));
        return { app, db, services, close: () => db.close() };
    } catch (error) {
        db.close();
        throw error;
    }
}
module.exports = { createApp };
