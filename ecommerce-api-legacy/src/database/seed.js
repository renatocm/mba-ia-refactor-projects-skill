const { hashPassword } = require('../security/passwords');
const { userRepository } = require('../repositories/users');
async function seedDemo(db, admin) {
    const passwordHash = admin ? await hashPassword(admin.password) : null;
    db.transaction(() => {
        db.run('INSERT INTO courses(id,title,price,active) VALUES (?,?,?,?),(?,?,?,?)',
            [1, 'Clean Architecture', 997, 1, 2, 'Docker', 497, 1]);
        // No default users, passwords, enrollments or paid transactions.
        if (admin) userRepository(db).create({ name: admin.name, email: admin.email, passwordHash, role: 'admin' });
    });
}
module.exports = { seedDemo };
