function sessionRepository(db) {
    return {
        create(hash, userId, expiresAt, now) {
            // One active session per account bounds growth and revokes previous login tokens.
            db.run('DELETE FROM sessions WHERE expires_at<=? OR user_id=?', [now, userId]);
            db.run('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES (?,?,?)', [hash, userId, expiresAt]);
        },
        find(hash, now) {
            return db.get(`SELECT u.id,u.name,u.email,u.role FROM sessions s
                JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?`, [hash, now]);
        }
    };
}
module.exports = { sessionRepository };
