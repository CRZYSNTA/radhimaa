"""
JARVIS V4 - Memory Repositories
Defines abstract repository interfaces and SQLite implementations for Phase 1.
Preserves existing SQLite tables while paving the way for pgvector / semantic search in Phase 2.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List, Optional, Protocol, runtime_checkable

from memory.database import get_db
from memory.conversation import conversation_manager
from memory.user_memory import user_memory

logger = logging.getLogger("JARVIS.Memory.Repositories")


@runtime_checkable
class ConversationRepository(Protocol):
    def save_turn(self, role: str, content: str, conversation_id: Optional[str] = None) -> None:
        ...

    def get_recent(self, limit: int = 10, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        ...

    def get_context_window(self, max_turns: Optional[int] = None) -> str:
        ...


class SQLiteConversationRepository:
    """Production SQLite conversation repository wrapping existing WAL tables."""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns

    def save_turn(self, role: str, content: str, conversation_id: Optional[str] = None) -> None:
        conversation_manager.save_turn(role, content)

    def get_recent(self, limit: int = 10, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return conversation_manager.get_recent(limit=limit)

    def get_context_window(self, max_turns: Optional[int] = None) -> str:
        return conversation_manager.get_context_window(max_turns=max_turns or self.max_turns)


@runtime_checkable
class FactMemoryRepository(Protocol):
    def remember(self, key: str, value: str) -> None:
        ...

    def get_fact(self, key: str) -> Optional[str]:
        ...

    def get_all_facts(self) -> Dict[str, str]:
        ...

    def delete_fact(self, key: str) -> bool:
        ...


class SQLiteFactMemoryRepository:
    """Production SQLite fact memory repository wrapping user_memory."""

    def remember(self, key: str, value: str) -> None:
        user_memory.remember(key, value)

    def get_fact(self, key: str) -> Optional[str]:
        return user_memory.get_fact(key)

    def get_all_facts(self) -> Dict[str, str]:
        return user_memory.get_all_facts()

    def delete_fact(self, key: str) -> bool:
        return user_memory.forget(key)


_conversation_repo: Optional[ConversationRepository] = None
_fact_repo: Optional[FactMemoryRepository] = None


def get_conversation_repository() -> ConversationRepository:
    global _conversation_repo
    if _conversation_repo is None:
        _conversation_repo = SQLiteConversationRepository()
    return _conversation_repo


def get_fact_repository() -> FactMemoryRepository:
    global _fact_repo
    if _fact_repo is None:
        _fact_repo = SQLiteFactMemoryRepository()
    return _fact_repo
