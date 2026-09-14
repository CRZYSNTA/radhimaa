"""
JARVIS V4 - Context Engine
Assembles conversational dialogue history, fact memory, and active session context
into a coherent prompt block for the orchestrator and AI Gateway.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from memory.repositories import get_conversation_repository, get_fact_repository
from core.session import get_session_manager

logger = logging.getLogger("JARVIS.Orchestration.ContextEngine")


class ContextEngine:
    def __init__(self):
        self.conv_repo = get_conversation_repository()
        self.fact_repo = get_fact_repository()
        self.session_manager = get_session_manager()

    def assemble_context(self, user_message: str, max_turns: int = 10) -> str:
        """Assembles conversational history, user facts, and session state."""
        blocks = []

        # 1. Facts from long-term memory
        facts = self.fact_repo.get_all_facts()
        if facts:
            fact_lines = [f"- {k}: {v}" for k, v in list(facts.items())[:15]]
            blocks.append("User Facts & Preferences:\n" + "\n".join(fact_lines))

        # 2. Active Session Context
        session_ctx = self.session_manager.get_context()
        if session_ctx:
            blocks.append(f"Current Session State:\n{session_ctx}")

        # 3. Conversation History
        history = self.conv_repo.get_context_window(max_turns=max_turns)
        if history:
            blocks.append(f"Recent Conversation:\n{history}")

        return "\n\n".join(blocks)


_context_engine: Optional[ContextEngine] = None


def get_context_engine() -> ContextEngine:
    global _context_engine
    if _context_engine is None:
        _context_engine = ContextEngine()
    return _context_engine
