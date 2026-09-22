function reportRepository(db) {
    return {
        financial({ page, limit, studentPage, studentLimit }) {
            const courses = db.all(`SELECT c.id,c.title,
                COALESCE((SELECT SUM(p.amount) FROM enrollments e JOIN payments p ON p.enrollment_id=e.id
                    WHERE e.course_id=c.id AND p.status='PAID'),0) AS revenue
                FROM courses c ORDER BY c.id LIMIT ? OFFSET ?`, [limit, (page - 1) * limit]);
            if (!courses.length) return { courses, students: [] };
            // SQL structure contains only generated placeholders; all IDs are bound.
            const placeholders = courses.map(() => '?').join(',');
            const students = db.all(`WITH ranked AS (
                SELECT e.course_id,u.name AS student,COALESCE(p.amount,0) AS paid,
                    ROW_NUMBER() OVER (PARTITION BY e.course_id ORDER BY e.id) AS position
                FROM enrollments e JOIN users u ON u.id=e.user_id
                LEFT JOIN payments p ON p.enrollment_id=e.id WHERE e.course_id IN (${placeholders})
            ) SELECT course_id,student,paid FROM ranked WHERE position>? AND position<=?
              ORDER BY course_id,position`, [...courses.map(c => c.id), (studentPage - 1) * studentLimit, studentPage * studentLimit]);
            return { courses, students };
        }
    };
}
module.exports = { reportRepository };
