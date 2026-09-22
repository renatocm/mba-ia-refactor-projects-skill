function userRepository(db) {
    return {
        byEmail(email) { return db.get('SELECT * FROM users WHERE email=?', [email]); },
        byId(id) { return db.get('SELECT * FROM users WHERE id=?', [id]); },
        create({ name, email, passwordHash, role = 'student' }) {
            return Number(db.run('INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)', [name, email, passwordHash, role]).lastInsertRowid);
        },
        hasEnrollments(id) { return Boolean(db.get('SELECT 1 FROM enrollments WHERE user_id=? LIMIT 1', [id])); },
        delete(id) { return db.run('DELETE FROM users WHERE id=?', [id]).changes; }
    };
}
module.exports = { userRepository };
