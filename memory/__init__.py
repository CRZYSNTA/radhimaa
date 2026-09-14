"""
JARVIS Memory Subsystem
Combines SQLite database persistence, conversation history, user preferences,
and action auditing.
"""

from memory.database import get_db, init_db, DB_PATH
from memory.conversation import ConversationManager, conversation_manager
from memory.user_memory import UserMemory, user_memory
from memory.retrieval import search_facts, retrieve, log_action, get_action_logs

def remember(key: str, value: str, category: str = "general") -> None:
    user_memory.remember(key, value, category)

def forget(key: str) -> bool:
    return user_memory.forget(key)

def get_fact(key: str):
    return user_memory.get_fact(key)

__all__ = [
    "get_db",
    "init_db",
    "DB_PATH",
    "ConversationManager",
    "conversation_manager",
    "UserMemory",
    "user_memory",
    "remember",
    "forget",
    "get_fact",
    "search_facts",
    "retrieve",
    "log_action",
    "get_action_logs",
]