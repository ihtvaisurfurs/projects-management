ALTER TABLE users ADD COLUMN telegram_id INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
