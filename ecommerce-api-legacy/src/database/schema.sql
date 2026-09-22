CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 2 AND 200),
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student','admin'))
) STRICT;
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price REAL NOT NULL CHECK(price >= 0),
    active INTEGER NOT NULL CHECK(active IN (0,1))
) STRICT;
CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    UNIQUE(user_id, course_id)
) STRICT;
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL UNIQUE REFERENCES enrollments(id) ON DELETE RESTRICT,
    amount REAL NOT NULL CHECK(amount >= 0),
    status TEXT NOT NULL CHECK(status IN ('PAID','DENIED')),
    mode TEXT NOT NULL CHECK(mode = 'demo')
) STRICT;
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
) STRICT;
CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL
) STRICT;
CREATE INDEX enrollments_course_idx ON enrollments(course_id,id);
CREATE INDEX sessions_expiry_idx ON sessions(expires_at);
PRAGMA user_version = 1;
