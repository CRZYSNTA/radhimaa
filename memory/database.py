"""
JARVIS V3.0 - Memory Database
Manages persistent SQLite connection, schemas, migrations, and WAL mode.
"""

import os
import sys
import time
import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("JARVIS.Memory.DB")

def get_db_path() -> str:
    """Returns absolute path to jarvis_memory.db in runtime root directory."""
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "/tmp/jarvis_memory.db"
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).resolve().parent.parent
    return str(base_dir / "jarvis_memory.db")

DB_PATH = get_db_path()

def get_db() -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory and WAL mode enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    return conn

def init_db():
    """Initializes all required tables and ensures column schema consistency."""
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                role TEXT,
                content TEXT,
                sender TEXT,
                message TEXT
            )
        """)
        # Ensure schema compatibility with older V1/V2 records
        cursor.execute("PRAGMA table_info(conversations)")
        cols = [row["name"] for row in cursor.fetchall()]
        for c in ["role", "content", "sender", "message"]:
            if c not in cols:
                try:
                    cursor.execute(f"ALTER TABLE conversations ADD COLUMN {c} TEXT")
                except Exception:
                    pass

        # 2. User Facts & Preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT DEFAULT 'general',
                updated_at REAL
            )
        """)
        cursor.execute("PRAGMA table_info(user_facts)")
        fact_cols = [row["name"] for row in cursor.fetchall()]
        if "category" not in fact_cols:
            try:
                cursor.execute("ALTER TABLE user_facts ADD COLUMN category TEXT DEFAULT 'general'")
            except Exception:
                pass

        # 3. Action Execution Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                goal TEXT,
                tool TEXT,
                params TEXT,
                permission TEXT,
                success INTEGER,
                error TEXT,
                duration_ms REAL
            )
        """)

        # 4. Reminders
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at REAL,
                status TEXT DEFAULT 'pending'
            )
        """)

        # 5. Session Goals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT,
                created_at REAL,
                completed INTEGER DEFAULT 0
            )
        """)

        # 6. Paired Mobile Devices
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paired_devices (
                device_id TEXT PRIMARY KEY,
                device_name TEXT,
                auth_token TEXT UNIQUE,
                paired_at REAL,
                last_seen REAL,
                is_active INTEGER DEFAULT 1
            )
        """)

        conn.commit()
    logger.info("[Memory] SQLite Database initialized successfully.")

def register_paired_device(device_id: str, device_name: str, auth_token: str) -> dict:
    """Registers or updates a paired mobile device with its security token."""
    now = time.time()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO paired_devices (device_id, device_name, auth_token, paired_at, last_seen, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(device_id) DO UPDATE SET
                device_name=excluded.device_name,
                auth_token=excluded.auth_token,
                last_seen=excluded.last_seen,
                is_active=1
        """, (device_id, device_name, auth_token, now, now))
        conn.commit()
    return {"device_id": device_id, "device_name": device_name, "paired_at": now, "is_active": 1}

def validate_device_token(auth_token: str) -> Optional[dict]:
    """Validates device bearer token, updates last_seen timestamp, and returns device info."""
    if not auth_token:
        return None
    now = time.time()
    with get_db() as conn:
        row = conn.execute(
            "SELECT device_id, device_name, paired_at, last_seen, is_active FROM paired_devices WHERE auth_token = ? AND is_active = 1",
            (auth_token,)
        ).fetchone()
        if row:
            conn.execute("UPDATE paired_devices SET last_seen = ? WHERE auth_token = ?", (now, auth_token))
            conn.commit()
            return dict(row)
    return None

def get_paired_devices() -> list:
    """Returns list of all registered mobile devices."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT device_id, device_name, paired_at, last_seen, is_active FROM paired_devices ORDER BY last_seen DESC"
        ).fetchall()
        return [dict(r) for r in rows]

def revoke_device(device_id: str) -> bool:
    """Revokes a paired device by device_id."""
    with get_db() as conn:
        res = conn.execute("UPDATE paired_devices SET is_active = 0 WHERE device_id = ?", (device_id,))
        conn.commit()
        return res.rowcount > 0

if __name__ == "__main__":
    init_db()
    print("Database path:", DB_PATH)
    print("Database schema successfully verified.")
