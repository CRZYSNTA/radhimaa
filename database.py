"""
=============================================================================
JARVIS Stage 4: SQLite Database Memory Helper
=============================================================================
Goal: Provide persistent, long-term memory for JARVIS so it remembers:
 - Conversation history
 - User facts & personal preferences (e.g. name, location, favorite tools)
 - Reminders and scheduled tasks

Uses: Standard Python `sqlite3` (Zero external setup required)

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis_memory.db")

def get_db():
    """Returns a SQLite connection object with Dictionary row formatting."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database schema tables if they do not exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Table 1: Conversation History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                sender TEXT,
                message TEXT
            )
        """)

        # Table 2: User Facts & Preferences (Key-Value Store)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at REAL
            )
        """)

        # Table 3: Reminders
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at REAL,
                status TEXT DEFAULT 'pending'
            )
        """)
        conn.commit()
    print("[OK] Database memory initialized successfully.")

def save_conversation(sender: str, message: str):
    """Saves a single message entry into the conversations table."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (timestamp, sender, message) VALUES (?, ?, ?)",
            (time.time(), sender, message)
        )
        conn.commit()

def get_recent_conversations(limit: int = 10):
    """Fetches the last N conversation messages to build memory context for the LLM."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT sender, message FROM conversations ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        # Return in chronological order (oldest to newest)
        return list(reversed([dict(row) for row in rows]))

def set_fact(key: str, value: str):
    """Saves or updates a personal fact in memory (e.g. set_fact('user_name', 'Tony Stark'))."""
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_facts (key, value, updated_at) VALUES (?, ?, ?)",
            (key.lower(), value, time.time())
        )
        conn.commit()

def get_fact(key: str) -> str:
    """Retrieves a stored personal fact from memory."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM user_facts WHERE key = ?", (key.lower(),))
        row = cursor.fetchone()
        return row["value"] if row else None

if __name__ == "__main__":
    init_db()
    set_fact("user_name", "Developer")
    save_conversation("User", "Hello JARVIS!")
    save_conversation("JARVIS", "Greetings! How may I assist you today?")
    print("Stored Recent History:", get_recent_conversations(5))
