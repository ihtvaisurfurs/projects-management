BEGIN TRANSACTION;

CREATE TABLE project_owner_history_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    owner_name TEXT NOT NULL,
    from_date TEXT NOT NULL,
    to_date TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

INSERT INTO project_owner_history_new (id, project_id, owner_name, from_date, to_date)
SELECT id, project_id, owner_name, from_date, to_date FROM project_owner_history;

DROP TABLE project_owner_history;
ALTER TABLE project_owner_history_new RENAME TO project_owner_history;

COMMIT;
