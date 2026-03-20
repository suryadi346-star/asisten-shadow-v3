"""
Shadow Agent — Database Layer (SQLite)
Ringan, zero-dependency server, cocok untuk Termux.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from config import config


def get_conn() -> sqlite3.Connection:
    Path(config.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Buat semua tabel kalau belum ada."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            goal        TEXT NOT NULL,
            status      TEXT DEFAULT 'active',   -- active|done|paused
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            metadata    TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id          TEXT PRIMARY KEY,
            session_id  TEXT NOT NULL REFERENCES sessions(id),
            agent_type  TEXT NOT NULL,           -- planner|researcher|writer|coder
            provider    TEXT NOT NULL,           -- anthropic|openai
            model       TEXT NOT NULL,
            prompt      TEXT NOT NULL,
            result      TEXT,
            status      TEXT DEFAULT 'pending',  -- pending|running|done|failed
            tokens_used INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL,
            finished_at TEXT,
            metadata    TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS messages (
            id          TEXT PRIMARY KEY,
            task_id     TEXT NOT NULL REFERENCES tasks(id),
            role        TEXT NOT NULL,           -- user|assistant|system
            content     TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS provider_stats (
            id          TEXT PRIMARY KEY,
            provider    TEXT NOT NULL,
            model       TEXT NOT NULL,
            tokens_in   INTEGER DEFAULT 0,
            tokens_out  INTEGER DEFAULT 0,
            calls       INTEGER DEFAULT 0,
            errors      INTEGER DEFAULT 0,
            date        TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status  ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_messages_task ON messages(task_id);
        """)


# ─── Session CRUD ─────────────────────────────────────────────────────────────

def create_session(name: str, goal: str, metadata: dict = {}) -> str:
    sid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions VALUES (?,?,?,?,?,?,?)",
            (sid, name, goal, "active", now, now, json.dumps(metadata))
        )
    return sid


def get_session(session_id: str) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        return dict(row) if row else None


def list_sessions(status: str = None) -> List[Dict]:
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE status=? ORDER BY created_at DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def update_session_status(session_id: str, status: str):
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET status=?, updated_at=? WHERE id=?",
            (status, now, session_id)
        )


# ─── Task CRUD ────────────────────────────────────────────────────────────────

def create_task(session_id: str, agent_type: str, provider: str,
                model: str, prompt: str, metadata: dict = {}) -> str:
    tid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (tid, session_id, agent_type, provider, model,
             prompt, None, "pending", 0, now, None, json.dumps(metadata))
        )
    return tid


def update_task(task_id: str, result: str, status: str, tokens_used: int = 0):
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "UPDATE tasks SET result=?, status=?, tokens_used=?, finished_at=? WHERE id=?",
            (result, status, tokens_used, now, task_id)
        )


def get_task(task_id: str) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return dict(row) if row else None


def list_tasks(session_id: str) -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE session_id=? ORDER BY created_at ASC",
            (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ─── Message CRUD ─────────────────────────────────────────────────────────────

def save_message(task_id: str, role: str, content: str):
    mid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages VALUES (?,?,?,?,?)",
            (mid, task_id, role, content, now)
        )


def get_messages(task_id: str) -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE task_id=? ORDER BY created_at ASC",
            (task_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ─── Stats ────────────────────────────────────────────────────────────────────

def record_stat(provider: str, model: str, tokens_in: int, tokens_out: int,
                success: bool = True):
    today = datetime.utcnow().date().isoformat()
    sid = f"{provider}_{model}_{today}"
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT id FROM provider_stats WHERE id=?", (sid,)
        ).fetchone()
        if exists:
            conn.execute("""
                UPDATE provider_stats
                SET tokens_in=tokens_in+?, tokens_out=tokens_out+?,
                    calls=calls+1, errors=errors+?
                WHERE id=?
            """, (tokens_in, tokens_out, 0 if success else 1, sid))
        else:
            conn.execute(
                "INSERT INTO provider_stats VALUES (?,?,?,?,?,?,?,?)",
                (sid, provider, model, tokens_in, tokens_out,
                 1, 0 if success else 1, today)
            )


def get_stats() -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM provider_stats ORDER BY date DESC LIMIT 30"
        ).fetchall()
        return [dict(r) for r in rows]
