import sqlite3

DB_FILE = "sync.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            gdrive_id TEXT NOT NULL,
            mtime REAL
        )
    """)
    conn.commit()
    conn.close()

def add_file(path, gdrive_id, mtime):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO files (path, gdrive_id, mtime) VALUES (?, ?, ?)",
        (path, gdrive_id, mtime)
    )
    conn.commit()
    conn.close()

def get_file(path):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT gdrive_id, mtime FROM files WHERE path=?", (path,))
    row = c.fetchone()
    conn.close()
    return row

def remove_file(path):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM files WHERE path=?", (path,))
    conn.commit()
    conn.close()

def all_files():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT path, gdrive_id, mtime FROM files")
    rows = c.fetchall()
    conn.close()
    return rows
