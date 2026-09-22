const { DatabaseSync } = require('node:sqlite');
const { readFileSync } = require('node:fs');
const path = require('node:path');

function createDatabase() {
    const connection = new DatabaseSync(':memory:', { enableForeignKeyConstraints: true });
    const db = {
        run(sql, params = []) { return connection.prepare(sql).run(...params); },
        get(sql, params = []) { return connection.prepare(sql).get(...params); },
        all(sql, params = []) { return connection.prepare(sql).all(...params); },
        // Callback MUST be synchronous: no yielding inside a shared-connection transaction.
        transaction(work) {
            connection.exec('BEGIN IMMEDIATE');
            try {
                const result = work();
                if (result && typeof result.then === 'function') throw new Error('Transação deve ser síncrona');
                connection.exec('COMMIT');
                return result;
            } catch (error) {
                connection.exec('ROLLBACK');
                throw error;
            }
        },
        close() { connection.close(); }
    };
    try {
        connection.exec('BEGIN IMMEDIATE;\n' + readFileSync(path.join(__dirname, 'schema.sql'), 'utf8') + '\nCOMMIT;');
        return db;
    } catch (error) {
        connection.close();
        throw error;
    }
}
module.exports = { createDatabase };
