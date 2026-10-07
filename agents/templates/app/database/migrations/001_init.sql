CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  body TEXT,
  created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_items_created_at ON items (created_at);
