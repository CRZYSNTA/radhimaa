"""
JARVIS Database Module (Backwards Compatibility Wrapper)
Routes database operations through the unified `memory` subsystem.
"""

from memory.database import (
    get_db, init_db, DB_PATH,
    register_paired_device, validate_device_token,
    get_paired_devices, revoke_device
)
from memory.conversation import conversation_manager
from memory.user_memory import user_memory

def save_conversation(sender: str, message: str):
    """Saves a single message entry into the conversations table."""
    conversation_manager.save_turn(sender, message)

def get_recent_conversations(limit: int = 10):
    """Fetches the last N conversation messages in chronological order."""
    recent = conversation_manager.get_recent(limit=limit)
    return [{"sender": r.get("role", "user"), "message": r.get("content", "")} for r in recent]

def set_fact(key: str, value: str):
    """Saves or updates a personal fact in memory."""
    user_memory.remember(key, value)

def get_fact(key: str):
    """Retrieves a stored personal fact from memory."""
    return user_memory.get_fact(key)

if __name__ == "__main__":
    init_db()
    set_fact("user_name", "Developer")
    save_conversation("User", "Hello JARVIS!")
    save_conversation("JARVIS", "Greetings! How may I assist you today?")
    print("Stored Recent History:", get_recent_conversations(5))
