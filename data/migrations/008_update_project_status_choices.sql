PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

ALTER TABLE projects RENAME TO projects_old;

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ("pending", "in_progress", "MVP", "support_update", "done", "failed", "deleted")) NOT NULL,
    owner_name TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT,
    deleted_at TEXT
);

INSERT INTO projects (id, title, description, status, owner_name, start_date, end_date, deleted_at)
SELECT id, title, description, status, owner_name, start_date, end_date, deleted_at
FROM projects_old;

DROP TABLE projects_old;

CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_name);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

COMMIT;
PRAGMA foreign_keys=ON;
