"""
JARVIS V4 - Canonical Error Categories & Last-Error Tracking
Provides centralized, safe error categorization and diagnostics metadata.
Rule: Never record or leak secrets, passwords, tokens, or raw user contents.
"""

from __future__ import annotations

import time
import threading
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict

class ErrorCategory(str, Enum):
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    TOOL_VALIDATION_ERROR = "TOOL_VALIDATION_ERROR"
    TOOL_EXECUTION_ERROR = "TOOL_EXECUTION_ERROR"
    VERIFICATION_ERROR = "VERIFICATION_ERROR"
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    AI_MODEL_ERROR = "AI_MODEL_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    VISION_CAPTURE_ERROR = "VISION_CAPTURE_ERROR"
    VISION_PROVIDER_ERROR = "VISION_PROVIDER_ERROR"
    VOICE_ERROR = "VOICE_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN = "UNKNOWN"

import re

# Redaction patterns
_API_KEY_RE = re.compile(r"(AIza[0-9A-Za-z-_]{35}|sk-[0-9A-Za-z]{20,})")
_BEARER_RE = re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)
_PASSWORD_PARAM_RE = re.compile(r"(password|passwd|token|secret|auth|apikey|api_key)\s*[:=]\s*['\"]?[^'\s,]+['\"]?", re.IGNORECASE)
_USER_PATH_RE = re.compile(r"[a-zA-Z]:\\(?:Users|Documents and Settings)\\[^\\]+\\", re.IGNORECASE)
_UNIX_USER_PATH_RE = re.compile(r"/(?:Users|home)/[^/]+/")
_PROMPT_SNIPPET_RE = re.compile(r"(prompt|query|input|user_input|content)\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE)

def _sanitize_error_message(message: str) -> str:
    if not message:
        return ""
    clean = str(message).strip()

    # Redact credentials, bearer tokens, passwords
    clean = _API_KEY_RE.sub("[REDACTED_API_KEY]", clean)
    clean = _BEARER_RE.sub(r"\1[REDACTED_TOKEN]", clean)
    clean = _PASSWORD_PARAM_RE.sub(r"\1=[REDACTED]", clean)
    clean = _PROMPT_SNIPPET_RE.sub(r"\1=[PROMPT_MINIMIZED]", clean)

    # Redact absolute user profile paths safely
    clean = _USER_PATH_RE.sub(lambda m: "[USER_DIR]\\", clean)
    clean = _UNIX_USER_PATH_RE.sub(lambda m: "[USER_DIR]/", clean)

    # Redact high-entropy words (>30 chars without path separators)
    words = clean.split()
    sanitized_words = []
    for w in words:
        if len(w) > 30 and ("=" not in w) and ("/" not in w) and ("\\" not in w):
            sanitized_words.append("[REDACTED_HASH]")
        else:
            sanitized_words.append(w)
    clean = " ".join(sanitized_words)

    # Apply data minimization: concise operational description (max 150 chars)
    if len(clean) > 150:
        clean = clean[:147] + "..."
    return clean

@dataclass
class ErrorInfo:
    category: ErrorCategory
    message: str
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = ""
    subsystem: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value if isinstance(self.category, ErrorCategory) else str(self.category),
            "operation": self.subsystem,
            "subsystem": self.subsystem,
            "message": self.message,
            "trace_id": self.correlation_id,
            "correlation_id": self.correlation_id,
            "timestamp": round(self.timestamp, 2),
        }

class ErrorTracker:
    """Thread-safe ring buffer tracking the last error per subsystem and globally."""
    def __init__(self, max_history: int = 50):
        self._lock = threading.Lock()
        self._max_history = max_history
        self._history: List[ErrorInfo] = []
        self._last_error: Optional[ErrorInfo] = None
        self._subsystem_errors: Dict[str, ErrorInfo] = {}

    def record_error(self, category: ErrorCategory, message: str,
                     correlation_id: str = "", subsystem: str = "general") -> ErrorInfo:
        safe_msg = _sanitize_error_message(message)
        err = ErrorInfo(
            category=category,
            message=safe_msg,
            correlation_id=correlation_id,
            subsystem=subsystem
        )
        with self._lock:
            self._last_error = err
            self._subsystem_errors[subsystem] = err
            self._history.append(err)
            if len(self._history) > self._max_history:
                self._history.pop(0)
        return err

    def get_last_error(self, subsystem: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock:
            if subsystem:
                err = self._subsystem_errors.get(subsystem)
            else:
                err = self._last_error
            return err.to_dict() if err else None

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            return [e.to_dict() for e in self._history[-limit:]]

    def clear(self) -> None:
        with self._lock:
            self._history.clear()
            self._last_error = None
            self._subsystem_errors.clear()

_global_error_tracker = ErrorTracker()

def get_error_tracker() -> ErrorTracker:
    return _global_error_tracker

def record_error(category: ErrorCategory, message: str,
                 correlation_id: str = "", subsystem: str = "general") -> ErrorInfo:
    return _global_error_tracker.record_error(category, message, correlation_id, subsystem)

def get_last_error(subsystem: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return _global_error_tracker.get_last_error(subsystem)