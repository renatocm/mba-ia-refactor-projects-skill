const { AppError } = require('../models/errors');
const validation = require('../models/validation');
const { hashPassword, verifyPassword } = require('../security/passwords');

function checkoutService({ db, users, checkout, gateway }) {
    return {
        async execute(input) {
            // Full validation precedes every repository call, including authentication lookup.
            const data = validation.checkout(input);
            const existing = users.byEmail(data.email);
            let passwordHash;
            if (existing) {
                if (!await verifyPassword(data.password, existing.password_hash)) throw new AppError(401, 'Credenciais inválidas');
            } else {
                passwordHash = await hashPassword(data.password);
            }
            // KDF completes outside the transaction. All SQLite work below is synchronous,
            // so no request can interleave its reads/writes on the same connection.
            return db.transaction(() => {
                const course = checkout.activeCourse(data.courseId);
                if (!course) throw new AppError(404, 'Curso não encontrado');
                const current = users.byEmail(data.email);
                if (existing && (!current || current.id !== existing.id || current.password_hash !== existing.password_hash)) {
                    throw new AppError(401, 'Credenciais inválidas');
                }
                if (!existing && current) throw new AppError(409, 'Email cadastrado durante a operação; autentique novamente');
                if (current && checkout.enrolled(current.id, course.id)) throw new AppError(409, 'Usuário já matriculado neste curso');
                const payment = gateway.authorize(data.card);
                if (payment.status !== 'PAID') throw new AppError(400, 'Pagamento de demonstração recusado');
                const userId = current ? current.id : users.create({ name: data.name, email: data.email, passwordHash });
                const enrollmentId = checkout.enroll(userId, course.id);
                checkout.payment(enrollmentId, course.price, payment.status, payment.mode);
                checkout.audit(enrollmentId);
                return { enrollmentId, paymentMode: payment.mode };
            });
        }
    };
}
module.exports = { checkoutService };
