BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS project_owner_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    owner_name TEXT NOT NULL,
    from_date TEXT NOT NULL,
    to_date TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

ALTER TABLE projects RENAME TO projects_old;

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ("pending", "MVP", "support_update", "done", "deleted")) NOT NULL,
    owner_name TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT,
    deleted_at TEXT
);

INSERT INTO projects (id, title, description, status, owner_name, start_date, end_date, deleted_at)
SELECT id, title, description, status, owner_name, start_date, end_date, NULL FROM projects_old;

DROP TABLE projects_old;

CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_name);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

INSERT INTO project_owner_history (project_id, owner_name, from_date, to_date)
SELECT id, owner_name, COALESCE(start_date, date('now')), NULL
FROM projects
WHERE owner_name IS NOT NULL;

COMMIT;
