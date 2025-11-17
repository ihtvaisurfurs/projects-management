ALTER TABLE users ADD COLUMN created_at TEXT;
UPDATE users SET created_at = COALESCE(created_at, datetime('now'));
