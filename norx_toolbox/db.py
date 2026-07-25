import sqlite3
from contextlib import contextmanager

from norx_toolbox.config import config

DB_PATH = config.OUTPUT_DIR / "toolbox.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    dashboard_token TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS short_links (
    token TEXT PRIMARY KEY,
    target_url TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL,          -- NULL = permanent
    hits INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS files (
    token TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    path TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    chat_id INTEGER,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL  -- always required, no permanent option
);
"""


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)


def get_dashboard_token(user_id: int) -> str:
    """Every user gets one stable dashboard token, created on first use. This token
    acts as the bearer credential for their management page — unguessable, so no
    separate login system needed, consistent with your other token-based links."""
    import secrets
    with get_db() as conn:
        row = conn.execute("SELECT dashboard_token FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return row["dashboard_token"]
        token = secrets.token_urlsafe(24)
        conn.execute("INSERT INTO users (user_id, dashboard_token) VALUES (?, ?)", (user_id, token))
        return token