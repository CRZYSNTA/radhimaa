"""
JARVIS V4 - Lightweight Request & Operation Tracing Subsystem
Correlates end-to-end execution:
REQUEST -> ROUTER -> ORCHESTRATOR -> PLAN -> TOOL -> PERMISSION -> EXECUTION -> VERIFICATION -> RESPONSE.
Captures durations without external heavyweight tracing dependencies.
Rule 15: Never log secrets, passwords, tokens, or raw confidential user data.
"""

from __future__ import annotations

import time
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

import re

_SENSITIVE_KEYS = {"password", "token", "secret", "auth", "api_key", "key", "authorization", "cookie", "credential"}
_CONTENT_KEYS = {"prompt", "text", "content", "message", "query", "input", "user_input", "raw", "transcript"}
_ARGS_KEYS = {"args", "arguments", "params", "kwargs", "tool_args"}
_MEDIA_KEYS = {"frame", "image", "screenshot", "bytes", "photo", "video"}
_USER_PATH_RE = re.compile(r"[a-zA-Z]:\\(?:Users|Documents and Settings)\\[^\\]+\\", re.IGNORECASE)
_UNIX_USER_PATH_RE = re.compile(r"/(?:Users|home)/[^/]+/")

def _sanitize_meta(data: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = {}
    for k, v in data.items():
        k_lower = k.lower()
        if any(s in k_lower for s in _SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif any(s in k_lower for s in _CONTENT_KEYS):
            # Data minimization: Never retain raw prompt or user content
            length = len(str(v)) if v is not None else 0
            sanitized[k] = f"[PROMPT_MINIMIZED len={length}]"
        elif any(s in k_lower for s in _ARGS_KEYS):
            # Data minimization: Never retain raw tool argument values; keep argument names only
            if isinstance(v, dict):
                sanitized[k] = {"arg_keys": list(v.keys())}
            else:
                sanitized[k] = "[ARGS_MINIMIZED]"
        elif any(s in k_lower for s in _MEDIA_KEYS):
            # Data minimization: Never retain raw image bytes or frame arrays
            length = len(v) if hasattr(v, "__len__") else 0
            sanitized[k] = f"[MEDIA_MINIMIZED bytes={length}]"
        elif isinstance(v, dict):
            sanitized[k] = _sanitize_meta(v)
        elif isinstance(v, str):
            clean_v = _USER_PATH_RE.sub(lambda m: "[USER_DIR]\\", v)
            clean_v = _UNIX_USER_PATH_RE.sub(lambda m: "[USER_DIR]/", clean_v)
            sanitized[k] = clean_v[:80]
        elif isinstance(v, (int, float, bool)) or v is None:
            sanitized[k] = v
        else:
            sanitized[k] = str(type(v).__name__)
    return sanitized

@dataclass
class TraceSpan:
    name: str
    status: str = "OK"  # OK, FAILED, SKIPPED, REQUIRES_CONFIRMATION
    start_time: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "start_time": self.start_time,
            "duration_ms": round(self.duration_ms, 2),
            "metadata": self.metadata
        }

@dataclass
class OperationTrace:
    trace_id: str
    session_id: str = ""
    status: str = "IN_PROGRESS"
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_duration_ms: float = 0.0
    spans: List[TraceSpan] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "spans": [s.to_dict() for s in self.spans]
        }

class TraceManager:
    """Thread-safe in-memory ring buffer of operation traces."""
    def __init__(self, max_history: int = 50):
        self._lock = threading.Lock()
        self._max_history = max_history
        self._active_traces: Dict[str, OperationTrace] = {}
        self._completed_traces: List[OperationTrace] = []

    def start_trace(self, trace_id: str, session_id: str = "") -> OperationTrace:
        trace = OperationTrace(trace_id=trace_id, session_id=session_id)
        with self._lock:
            self._active_traces[trace_id] = trace
        return trace

    def record_span(self, trace_id: str, name: str, status: str = "OK",
                    duration_ms: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> Optional[TraceSpan]:
        safe_meta = _sanitize_meta(metadata or {})
        span = TraceSpan(name=name, status=status, duration_ms=duration_ms, metadata=safe_meta)
        with self._lock:
            trace = self._active_traces.get(trace_id)
            if trace:
                trace.spans.append(span)
                return span
        return None

    def finish_trace(self, trace_id: str, status: str = "COMPLETED") -> Optional[OperationTrace]:
        now = time.time()
        with self._lock:
            trace = self._active_traces.pop(trace_id, None)
            if not trace:
                return None
            trace.status = status
            trace.end_time = now
            trace.total_duration_ms = (now - trace.start_time) * 1000.0
            self._completed_traces.append(trace)
            if len(self._completed_traces) > self._max_history:
                self._completed_traces.pop(0)
            return trace

    def get_recent_traces(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            return [t.to_dict() for t in self._completed_traces[-limit:]]

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            trace = self._active_traces.get(trace_id)
            if trace:
                return trace.to_dict()
            for t in reversed(self._completed_traces):
                if t.trace_id == trace_id:
                    return t.to_dict()
        return None

    def clear(self) -> None:
        with self._lock:
            self._active_traces.clear()
            self._completed_traces.clear()

_global_trace_manager = TraceManager()

def get_trace_manager() -> TraceManager:
    return _global_trace_manager

def start_trace(trace_id: str, session_id: str = "") -> OperationTrace:
    return _global_trace_manager.start_trace(trace_id, session_id)

def record_trace_span(trace_id: str, name: str, status: str = "OK",
                      duration_ms: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> Optional[TraceSpan]:
    return _global_trace_manager.record_span(trace_id, name, status, duration_ms, metadata)

def finish_trace(trace_id: str, status: str = "COMPLETED") -> Optional[OperationTrace]:
    return _global_trace_manager.finish_trace(trace_id, status)

def get_recent_traces(limit: int = 10) -> List[Dict[str, Any]]:
    return _global_trace_manager.get_recent_traces(limit)