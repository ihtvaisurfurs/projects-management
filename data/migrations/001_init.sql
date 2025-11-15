CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT CHECK(role IN ("admin", "programmer")) NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone ON users(phone);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ("pending", "MVP", "support_update", "done")) NOT NULL,
    owner_name TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT
);

CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_name);

INSERT INTO users (phone, name, role)
SELECT '+9647728774494', 'ali masood', 'admin'
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE phone = '+9647728774494'
);
