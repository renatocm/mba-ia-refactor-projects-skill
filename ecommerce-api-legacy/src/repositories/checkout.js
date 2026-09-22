function checkoutRepository(db) {
    return {
        activeCourse(id) { return db.get('SELECT * FROM courses WHERE id=? AND active=1', [id]); },
        enrolled(userId, courseId) { return Boolean(db.get('SELECT 1 FROM enrollments WHERE user_id=? AND course_id=?', [userId, courseId])); },
        enroll(userId, courseId) {
            return Number(db.run('INSERT INTO enrollments(user_id,course_id) VALUES (?,?)', [userId, courseId]).lastInsertRowid);
        },
        payment(enrollmentId, amount, status, mode) {
            db.run('INSERT INTO payments(enrollment_id,amount,status,mode) VALUES (?,?,?,?)', [enrollmentId, amount, status, mode]);
        },
        audit(enrollmentId) {
            db.run('INSERT INTO audit_logs(action) VALUES (?)', [`Demo checkout enrollment ${enrollmentId}`]);
        }
    };
}
module.exports = { checkoutRepository };
