"""
JARVIS V3.0 - Conversation Memory Manager
Handles multi-turn dialogue history, persistence, and sliding-window context.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from memory.database import get_db

logger = logging.getLogger("JARVIS.Memory.Conversation")

class ConversationManager:
    """Manages chat history with SQLite persistence and sliding window truncation."""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns

    def save_turn(self, role: str, content: str) -> None:
        """Persist a single dialogue turn to the database."""
        now = time.time()
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO conversations (timestamp, role, content, sender, message) VALUES (?, ?, ?, ?, ?)",
                    (now, role, content, role, content)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"[Conversation] Error saving turn: {e}")

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch the last N turns in chronological order."""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(conversations)")
                cols = [row["name"] for row in cursor.fetchall()]

                role_col = "role" if "role" in cols else "sender"
                msg_col = "content" if "content" in cols else "message"

                cursor.execute(f"""
                    SELECT id, timestamp, {role_col} as role, {msg_col} as content 
                    FROM conversations 
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                results = [dict(r) for r in reversed(rows)]
                return results
        except Exception as e:
            logger.error(f"[Conversation] Error fetching recent: {e}")
            return []

    def get_context_window(self, max_turns: Optional[int] = None) -> str:
        """Returns formatted conversation block for LLM prompts."""
        turns = self.get_recent(limit=max_turns or self.max_turns)
        if not turns:
            return ""
        lines = []
        for t in turns:
            role = (t.get("role") or "User").capitalize()
            content = t.get("content", "").strip()
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def clear_history(self) -> bool:
        """Clear all conversation entries."""
        try:
            with get_db() as conn:
                conn.execute("DELETE FROM conversations")
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[Conversation] Error clearing history: {e}")
            return False

# Global instance
conversation_manager = ConversationManager()
