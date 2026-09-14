"""
JARVIS Core Context - Conversation & multi-turn memory state
Manages conversation history, user facts, and session context.
"""
import os
import sys
import json
import time
import sqlite3
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

def get_db_path() -> str:
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_dir, "jarvis_memory.db")

@dataclass
class ConversationEntry:
    timestamp: float
    role: str
    content: str

@dataclass
class UserFact:
    key: str
    value: str
    updated_at: float

class ConversationMemory:
    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.history: List[ConversationEntry] = []
        self.facts: Dict[str, UserFact] = {}
        self.session_goals: List[str] = []
        self.current_screen_context: Optional[str] = None
        self.db_path = get_db_path()
        self._init_db()
        self._load_from_db()
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL,
                        role TEXT,
                        content TEXT,
                        sender TEXT,
                        message TEXT
                    )
                """)
                # Ensure columns exist if table was created with older schema
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(conversations)")
                cols = [row["name"] for row in cursor.fetchall()]
                if "role" not in cols:
                    try:
                        conn.execute("ALTER TABLE conversations ADD COLUMN role TEXT")
                    except Exception:
                        pass
                if "content" not in cols:
                    try:
                        conn.execute("ALTER TABLE conversations ADD COLUMN content TEXT")
                    except Exception:
                        pass
                if "sender" not in cols:
                    try:
                        conn.execute("ALTER TABLE conversations ADD COLUMN sender TEXT")
                    except Exception:
                        pass
                if "message" not in cols:
                    try:
                        conn.execute("ALTER TABLE conversations ADD COLUMN message TEXT")
                    except Exception:
                        pass

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_facts (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at REAL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS session_goals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        goal TEXT,
                        created_at REAL,
                        completed INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"[Memory Init Error]: {e}")
    
    def _load_from_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(conversations)")
                cols = [row["name"] for row in cursor.fetchall()]
                
                # Dynamic column resolution
                role_col = "role" if "role" in cols else "sender"
                msg_col = "content" if "content" in cols else "message"

                cursor.execute(f"""
                    SELECT {role_col}, {msg_col}, timestamp FROM conversations 
                    ORDER BY id DESC LIMIT ?
                """, (self.max_history,))
                rows = cursor.fetchall()
                for row in reversed(rows):
                    d = dict(row)
                    r = d.get(role_col) or d.get("sender") or "user"
                    c = d.get(msg_col) or d.get("message") or ""
                    self.history.append(ConversationEntry(
                        timestamp=d.get("timestamp", time.time()),
                        role=r,
                        content=c
                    ))
                
                cursor.execute("SELECT key, value, updated_at FROM user_facts")
                for row in cursor.fetchall():
                    self.facts[row["key"]] = UserFact(
                        key=row["key"],
                        value=row["value"],
                        updated_at=row["updated_at"]
                    )
        except Exception as e:
            print(f"[Memory Load Error]: {e}")
    
    def add_message(self, role: str, content: str):
        entry = ConversationEntry(timestamp=time.time(), role=role, content=content)
        self.history.append(entry)
        
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO conversations (timestamp, role, content, sender, message) VALUES (?, ?, ?, ?, ?)",
                    (entry.timestamp, role, content, role, content)
                )
                conn.commit()
        except Exception as e:
            print(f"[Memory Save Error]: {e}")
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_history(self, limit: int = None) -> List[Dict]:
        limit = limit or self.max_history
        return [asdict(e) for e in self.history[-limit:]]
    
    def get_context_string(self) -> str:
        parts = []
        if self.facts:
            parts.append("User Facts:")
            for k, v in self.facts.items():
                parts.append(f"  {k}: {v.value}")
        
        if self.session_goals:
            parts.append("Active Goals:")
            for g in self.session_goals:
                parts.append(f"  - {g}")
        
        if self.current_screen_context:
            parts.append(f"Screen Context: {self.current_screen_context}")
        
        if self.history:
            parts.append("Recent Conversation:")
            for e in self.history[-5:]:
                parts.append(f"  {e.role}: {e.content}")
        
        return "\n".join(parts) if parts else "No prior context."
    
    def set_fact(self, key: str, value: str):
        self.facts[key] = UserFact(key=key, value=value, updated_at=time.time())
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO user_facts (key, value, updated_at) VALUES (?, ?, ?)",
                    (key, value, time.time())
                )
                conn.commit()
        except Exception as e:
            print(f"[Memory Set Fact Error]: {e}")
    
    def get_fact(self, key: str) -> Optional[str]:
        fact = self.facts.get(key)
        return fact.value if fact else None
    
    def add_goal(self, goal: str):
        self.session_goals.append(goal)
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO session_goals (goal, created_at) VALUES (?, ?)",
                    (goal, time.time())
                )
                conn.commit()
        except Exception as e:
            print(f"[Memory Add Goal Error]: {e}")
    
    def complete_goal(self, goal: str):
        if goal in self.session_goals:
            self.session_goals.remove(goal)
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE session_goals SET completed=1 WHERE goal=? AND completed=0",
                    (goal,)
                )
                conn.commit()
        except Exception as e:
            print(f"[Memory Complete Goal Error]: {e}")
    
    def set_screen_context(self, context: str):
        self.current_screen_context = context
    
    def clear_screen_context(self):
        self.current_screen_context = None

_global_memory: Optional[ConversationMemory] = None

def get_memory() -> ConversationMemory:
    global _global_memory
    if _global_memory is None:
        _global_memory = ConversationMemory()
    return _global_memory

if __name__ == "__main__":
    mem = get_memory()
    mem.add_message("user", "Hello JARVIS")
    mem.add_message("assistant", "Hello! How can I help?")
    mem.set_fact("user_name", "Tony")
    print(mem.get_context_string())