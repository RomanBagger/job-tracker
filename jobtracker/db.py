import sqlite3
from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS emails (
    id TEXT PRIMARY KEY,
    thread_id TEXT,
    date TEXT,            -- ISO UTC
    sender TEXT,
    subject TEXT,
    snippet TEXT,
    is_job INTEGER,       -- 0/1
    company TEXT,
    company_key TEXT,
    role TEXT,
    event TEXT,           -- applied|hr_invite|tech_invite|final_invite|test_task|rejected|offer|recruiter_outreach|other
    stage_hint TEXT,      -- для rejected: auto|hr|tech|final (из текста письма)
    confidence REAL
);
CREATE INDEX IF NOT EXISTS idx_emails_company ON emails(company_key);
CREATE TABLE IF NOT EXISTS companies (
    company_key TEXT PRIMARY KEY,
    name TEXT,
    tier TEXT,            -- S|A|B|C|D
    category TEXT,        -- product|consulting|outsourcing|startup|agency|other
    rationale TEXT,
    manual INTEGER DEFAULT 0,
    rated_at TEXT,        -- ISO UTC, когда оценивали последний раз
    prev_tier TEXT,       -- тир до последней переоценки
    tier_changed_at TEXT
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(companies)")}
    for col in ("rated_at", "prev_tier", "tier_changed_at"):
        if col not in cols:
            conn.execute(f"ALTER TABLE companies ADD COLUMN {col} TEXT")
    if conn.execute("SELECT 1 FROM companies WHERE rated_at IS NULL LIMIT 1").fetchone():
        conn.execute("UPDATE companies SET rated_at=datetime('now') WHERE rated_at IS NULL")
        conn.commit()
    return conn


def get_meta(conn, key, default=None):
    r = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return r["value"] if r else default


def set_meta(conn, key, value):
    conn.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, value))
    conn.commit()
