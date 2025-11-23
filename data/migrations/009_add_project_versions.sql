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
    version TEXT NOT NULL DEFAULT '0',
    version_updated_at TEXT,
    deleted_at TEXT
);

INSERT INTO projects (id, title, description, status, owner_name, start_date, end_date, version, version_updated_at, deleted_at)
SELECT
    id,
    title,
    description,
    status,
    owner_name,
    start_date,
    end_date,
    '0' AS version,
    CASE WHEN status = 'done' THEN COALESCE(end_date, start_date, date('now')) ELSE NULL END AS version_updated_at,
    deleted_at
FROM projects_old;

DROP TABLE projects_old;

CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_name);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

CREATE TABLE IF NOT EXISTS project_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    version TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS idx_project_versions_project ON project_versions(project_id);

INSERT INTO project_versions (project_id, version, changed_at)
SELECT id, '0', COALESCE(end_date, start_date, date('now'))
FROM projects
WHERE status = 'done';

COMMIT;
PRAGMA foreign_keys=ON;
