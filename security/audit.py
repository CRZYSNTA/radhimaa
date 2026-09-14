"""
JARVIS V4 - Audit Logging Subsystem
Provides structured audit events for tool executions, permission gates, and sensitive actions.
Rule 15: Never log secrets, authorization headers, raw credentials, or sensitive file contents.
"""

from __future__ import annotations

import time
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

logger = logging.getLogger("JARVIS.Security.Audit")


@dataclass
class AuditEvent:
    event_type: str
    action: str
    status: str
    actor: str = "user"
    details: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_SENSITIVE_KEYS = {"password", "token", "secret", "auth", "api_key", "key", "authorization"}


def _sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = {}
    for k, v in data.items():
        if any(s in k.lower() for s in _SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_dict(v)
        else:
            sanitized[k] = v
    return sanitized


def record_audit(event_type: str, action: str, status: str, actor: str = "user",
                 details: Optional[Dict[str, Any]] = None, correlation_id: str = "") -> AuditEvent:
    safe_details = _sanitize_dict(details or {})
    event = AuditEvent(
        event_type=event_type,
        action=action,
        status=status,
        actor=actor,
        details=safe_details,
        correlation_id=correlation_id
    )
    logger.info(f"[AUDIT] {event.event_type} | {event.action} | {event.status} | actor={event.actor} | cid={event.correlation_id}")
    return event
