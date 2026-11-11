import sqlite3
from pathlib import Path
from app.config import DATABASE_PATH

def _connect():
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _connect() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                github_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                html_url TEXT NOT NULL UNIQUE,
                repository TEXT NOT NULL,
                issue_number INTEGER NOT NULL,
                saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def add_bookmark(data):
    with _connect() as conn:
        conn.execute('''
            INSERT INTO bookmarks (github_id, title, html_url, repository, issue_number)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(github_id) DO UPDATE SET
                title=excluded.title, html_url=excluded.html_url,
                repository=excluded.repository, issue_number=excluded.issue_number
        ''', (data.github_id, data.title, data.html_url, data.repository, data.number))
    return {"github_id": data.github_id, "title": data.title, "html_url": data.html_url,
            "repository": data.repository, "number": data.number}

def get_bookmarks():
    with _connect() as conn:
        rows = conn.execute(
            "SELECT github_id, title, html_url, repository, issue_number, saved_at "
            "FROM bookmarks ORDER BY saved_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]

def delete_bookmark(github_id):
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM bookmarks WHERE github_id = ?", (github_id,))
    return cursor.rowcount > 0
