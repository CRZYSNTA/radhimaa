"""
JARVIS V3.0 - User Long-term Memory
Stores, extracts, and manages user preferences, profile facts, and instructions.
"""

import re
import time
import logging
from typing import Dict, Any, Optional, List
from memory.database import get_db

logger = logging.getLogger("JARVIS.Memory.User")

class UserMemory:
    """Manages explicit and heuristic user facts & preferences."""

    def remember(self, key: str, value: str, category: str = "general") -> None:
        """Store or update a key-value fact."""
        clean_key = key.strip().lower().replace(" ", "_")
        clean_val = value.strip()
        now = time.time()
        try:
            with get_db() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_facts (key, value, category, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (clean_key, clean_val, category, now))
                conn.commit()
            logger.info(f"[UserMemory] Remembered fact: {clean_key} = {clean_val}")
        except Exception as e:
            logger.error(f"[UserMemory] Error saving fact: {e}")

    def forget(self, key: str) -> bool:
        """Delete a fact from memory."""
        clean_key = key.strip().lower().replace(" ", "_")
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_facts WHERE key = ?", (clean_key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"[UserMemory] Error forgetting fact: {e}")
            return False

    def get_fact(self, key: str) -> Optional[str]:
        """Retrieve a specific fact by key."""
        clean_key = key.strip().lower().replace(" ", "_")
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM user_facts WHERE key = ?", (clean_key,))
                row = cursor.fetchone()
                return row["value"] if row else None
        except Exception as e:
            logger.error(f"[UserMemory] Error retrieving fact: {e}")
            return None

    def get_all_facts(self) -> Dict[str, str]:
        """Returns all stored facts as a key-value dictionary."""
        facts = {}
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM user_facts")
                for row in cursor.fetchall():
                    facts[row["key"]] = row["value"]
        except Exception as e:
            logger.error(f"[UserMemory] Error listing facts: {e}")
        return facts

    def extract_and_remember(self, text: str) -> Optional[Dict[str, str]]:
        """
        Heuristic fast extractor for common memory patterns:
        - "my name is [name]"
        - "call me [name]"
        - "remember that [key] is [value]"
        - "my favorite [item] is [value]"
        """
        extracted = {}
        # Name pattern
        m_name = re.search(r"(?:my name is|call me)\s+([A-Za-z0-9_\-\s]+)", text, re.IGNORECASE)
        if m_name:
            name = m_name.group(1).strip().split(".")[0]
            self.remember("user_name", name, category="profile")
            extracted["user_name"] = name

        # Remember that X is Y pattern
        m_remember = re.search(r"remember (?:that\s+)?(.+?)\s+(?:is|=|are)\s+(.+)", text, re.IGNORECASE)
        if m_remember:
            k = m_remember.group(1).strip()
            v = m_remember.group(2).strip().rstrip(".")
            self.remember(k, v, category="user_note")
            extracted[k] = v

        # Favorite pattern
        m_fav = re.search(r"my favorite\s+(.+?)\s+is\s+(.+)", text, re.IGNORECASE)
        if m_fav:
            k = f"favorite_{m_fav.group(1).strip()}"
            v = m_fav.group(2).strip().rstrip(".")
            self.remember(k, v, category="preference")
            extracted[k] = v

        return extracted if extracted else None

# Global instance
user_memory = UserMemory()
