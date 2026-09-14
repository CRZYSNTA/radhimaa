"""
JARVIS V3.1 - Natural Conversational Session Manager
Maintains continuous multi-turn dialogue sessions after wake-word activation,
enabling follow-up commands without repeating 'Jarvis' until timeout or goodbye.
"""

import time
import uuid
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger("JARVIS.Core.Session")

DEFAULT_SESSION_TIMEOUT = 35.0  # seconds

TERMINATION_PHRASES = {
    "goodbye jarvis",
    "goodbye",
    "bye jarvis",
    "stop listening",
    "power down",
    "shutdown jarvis",
    "go to sleep",
    "dismissed",
    "exit"
}

@dataclass
class ConversationSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    started_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    is_active: bool = True
    timeout_seconds: float = DEFAULT_SESSION_TIMEOUT
    context: Dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0
    history: List[Dict[str, str]] = field(default_factory=list)

    def is_expired(self) -> bool:
        if not self.is_active:
            return True
        return (time.time() - self.last_activity) > self.timeout_seconds

    def touch(self):
        self.last_activity = time.time()

    def record_turn(self, user_msg: str, assistant_reply: str):
        self.touch()
        self.turn_count += 1
        self.history.append({"user": user_msg, "assistant": assistant_reply})
        if len(self.history) > 10:
            self.history.pop(0)

    def close(self):
        self.is_active = False

class SessionManager:
    """
    Singleton managing conversational sessions.
    """
    def __init__(self, timeout_seconds: float = DEFAULT_SESSION_TIMEOUT):
        self.timeout_seconds = timeout_seconds
        self.current_session: Optional[ConversationSession] = None

    def get_or_create_session(self, activated_by_wake: bool = False) -> ConversationSession:
        if self.current_session is None or self.current_session.is_expired():
            self.current_session = ConversationSession(
                timeout_seconds=self.timeout_seconds,
                is_active=True
            )
            logger.info(f"[SessionManager] Created new session {self.current_session.session_id}")
        else:
            self.current_session.touch()
        return self.current_session

    def is_session_active(self) -> bool:
        if self.current_session and not self.current_session.is_expired():
            return self.current_session.is_active
        return False

    def check_termination(self, text: str) -> bool:
        clean = text.strip().lower()
        for phrase in TERMINATION_PHRASES:
            if phrase in clean:
                if self.current_session:
                    self.current_session.close()
                    logger.info(f"[SessionManager] Session closed by termination phrase '{phrase}'")
                return True
        return False

    def update_context(self, key: str, value: Any):
        if self.current_session:
            self.current_session.context[key] = value

    def get_context(self) -> Dict[str, Any]:
        if self.current_session and not self.current_session.is_expired():
            return self.current_session.context
        return {}

_global_session_manager = SessionManager()

def get_session_manager() -> SessionManager:
    return _global_session_manager


