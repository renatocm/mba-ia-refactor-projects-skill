const { AppError } = require('./errors');

function object(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new AppError(400, 'Corpo JSON deve ser um objeto');
    return value;
}
function text(value, field, min = 1, max = 200) {
    if (typeof value !== 'string' || value.trim().length < min || value.trim().length > max) {
        throw new AppError(400, `${field} inválido`);
    }
    return value.trim();
}
function email(value) {
    const result = text(value, 'Email', 3, 254).toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(result)) throw new AppError(400, 'Email inválido');
    return result;
}
function password(value) {
    if (typeof value !== 'string' || value.length < 8 || Buffer.byteLength(value, 'utf8') > 1024) {
        throw new AppError(400, 'Senha deve ter pelo menos 8 caracteres e no máximo 1024 bytes');
    }
    return value;
}
function id(value) {
    if (typeof value !== 'number' || !Number.isSafeInteger(value) || value <= 0) throw new AppError(400, 'ID inválido');
    return value;
}
function pathId(value) {
    if (typeof value !== 'string' || !/^[1-9]\d{0,15}$/.test(value)) throw new AppError(400, 'ID inválido');
    return id(Number(value));
}
function credentials(data) {
    object(data);
    return { email: email(data.eml), password: password(data.pwd) };
}
function registration(data) {
    return { ...credentials(data), name: text(data.usr, 'Nome', 2) };
}
function checkout(data) {
    const result = registration(data);
    result.courseId = id(data.c_id);
    if (typeof data.card !== 'string' || !/^\d{13,19}$/.test(data.card)) throw new AppError(400, 'Cartão de demonstração inválido');
    result.card = data.card;
    return result;
}
function pagination(query) {
    const parse = (key, fallback, max) => {
        const value = query[key] === undefined ? String(fallback) : query[key];
        if (typeof value !== 'string' || !/^[1-9]\d{0,6}$/.test(value) || Number(value) > max) {
            throw new AppError(400, `${key} inválido`);
        }
        return Number(value);
    };
    return { page: parse('page', 1, 1000000), limit: parse('per_page', 20, 100),
        studentPage: parse('student_page', 1, 1000000), studentLimit: parse('students_per_page', 50, 100) };
}
module.exports = { object, text, email, password, id, pathId, credentials, registration, checkout, pagination };
