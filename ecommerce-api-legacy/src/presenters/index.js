function user(row) { return { id: row.id, name: row.name, email: row.email, role: row.role }; }
function checkout(result) { return { msg: 'Sucesso', enrollment_id: result.enrollmentId, payment_mode: result.paymentMode }; }
function report({ courses, students }) {
    const result = new Map(courses.map(course => [course.id, { course: course.title, revenue: course.revenue, students: [] }]));
    for (const student of students) result.get(student.course_id).students.push({ student: student.student, paid: student.paid });
    return [...result.values()];
}
module.exports = { user, checkout, report };
