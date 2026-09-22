const { randomBytes, scrypt, timingSafeEqual } = require('node:crypto');
const { promisify } = require('node:util');
const derive = promisify(scrypt);
const OPTIONS = { N: 32768, r: 8, p: 3, maxmem: 64 * 1024 * 1024 };

async function hashPassword(password) {
    const salt = randomBytes(16).toString('hex');
    const key = await derive(password, salt, 64, OPTIONS);
    return `scrypt$32768$8$3$${salt}$${key.toString('hex')}`;
}
async function verifyPassword(password, encoded) {
    if (typeof encoded !== 'string' || !/^scrypt\$32768\$8\$3\$[0-9a-f]{32}\$[0-9a-f]{128}$/.test(encoded)) return false;
    const parts = encoded.split('$');
    const actual = await derive(password, parts[4], 64, OPTIONS);
    return timingSafeEqual(actual, Buffer.from(parts[5], 'hex'));
}
module.exports = { hashPassword, verifyPassword };
