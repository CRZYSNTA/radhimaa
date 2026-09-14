"""
JARVIS V4 Phase 2 - Live Diagnostics, Error Tracking & Tracing Test Suite
Validates:
 1. Canonical /api/diagnostics endpoint structure and truthful subsystem states
 2. Zero secret / credential / token exposure in diagnostics
 3. Error category recording, redaction, and last-error query
 4. Operation trace ring buffer, span recording, and correlation
 5. Stale server detection identifiers (instance_id, pid, uptime)
"""

import pytest
from fastapi.testclient import TestClient

from server import app
from core.diagnostics import get_diagnostics_report
from core.errors import (
    ErrorCategory, ErrorInfo, ErrorTracker,
    record_error, get_last_error, get_error_tracker
)
from core.tracing import (
    TraceSpan, OperationTrace, TraceManager,
    start_trace, record_trace_span, finish_trace, get_recent_traces
)

# =============================================================================
# 1. Canonical Diagnostics Report & Subsystem Truthfulness
# =============================================================================

def test_diagnostics_endpoint_contract():
    client = TestClient(app)
    resp = client.get("/api/diagnostics")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "ok"
    assert "server" in data
    assert "ai" in data
    assert "memory" in data
    assert "voice" in data
    assert "vision" in data
    assert "executor" in data
    assert "websocket" in data
    assert "mobile" in data
    assert "recent_errors" in data
    assert "recent_traces" in data


def test_server_instance_identity():
    client = TestClient(app)
    resp = client.get("/api/diagnostics")
    server_info = resp.json()["server"]

    assert server_info["status"] == "ok"
    assert server_info["version"] == "4.0"
    assert "instance_id" in server_info
    assert server_info["instance_id"].startswith("inst_")
    assert isinstance(server_info["pid"], int)
    assert server_info["uptime_seconds"] >= 0.0


def test_diagnostics_contains_zero_secrets():
    """Verify that diagnostics payload contains no secret keys, tokens, or passwords."""
    report = get_diagnostics_report()
    raw_str = str(report).lower()

    forbidden_patterns = [
        "gemini_api_key",
        "openai_api_key",
        "auth_token",
        "bearer ",
        "sk-proj-",
        "ai_za",
        "password",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in raw_str


# =============================================================================
# 2. Error Categorization & Last Error Tracking
# =============================================================================

def test_error_tracker_categorization_and_sanitization():
    tracker = ErrorTracker(max_history=10)

    # 1. Record known error
    err = tracker.record_error(
        category=ErrorCategory.AI_PROVIDER_ERROR,
        message="Gemini connection timeout on model gemini-3.6-flash",
        correlation_id="corr-test-123",
        subsystem="ai"
    )
    assert err.category == ErrorCategory.AI_PROVIDER_ERROR
    assert err.subsystem == "ai"

    # 2. Query last error for subsystem
    last_ai_err = tracker.get_last_error("ai")
    assert last_ai_err is not None
    assert last_ai_err["category"] == "AI_PROVIDER_ERROR"
    assert "timeout" in last_ai_err["message"].lower()

    # 3. Verify secret redaction from error message
    secret_leak_msg = "Failed with token aVeryLongSecretTokenValueThatIsOverThirtyCharsWithoutSeparators in call"
    err2 = tracker.record_error(
        category=ErrorCategory.AUTHENTICATION_ERROR,
        message=secret_leak_msg,
        correlation_id="corr-test-456",
        subsystem="security"
    )
    assert "aVeryLongSecretTokenValueThatIsOverThirtyCharsWithoutSeparators" not in err2.message
    assert "[REDACTED_HASH]" in err2.message


# =============================================================================
# 3. Tracing Ring Buffer & Operation Spans
# =============================================================================

def test_tracing_lifecycle():
    trace_id = "trace-lifecycle-test"
    trace = start_trace(trace_id, session_id="session-1")
    assert trace.trace_id == trace_id

    # Record spans
    record_trace_span(trace_id, "request_received", metadata={"text_len": 45})
    record_trace_span(trace_id, "intent_resolved", metadata={"type": "SIMPLE", "tool": "get_time"})
    record_trace_span(trace_id, "tool_executed:get_time", status="OK", duration_ms=1.5)

    finished = finish_trace(trace_id, status="COMPLETED")
    assert finished is not None
    assert finished.status == "COMPLETED"
    assert finished.total_duration_ms >= 0.0
    assert len(finished.spans) == 3

    recent = get_recent_traces(5)
    assert any(t["trace_id"] == trace_id for t in recent)


def test_tracing_sanitizes_sensitive_metadata():
    mgr = TraceManager()
    mgr.start_trace("trace-sec-test")
    span = mgr.record_span(
        "trace-sec-test",
        "permission_checked",
        metadata={
            "api_key": "secret_key_12345",
            "token": "bearer_abc_xyz",
            "tool": "read_file"
        }
    )
    assert span is not None
    assert span.metadata["api_key"] == "[REDACTED]"
    assert span.metadata["token"] == "[REDACTED]"
    assert span.metadata["tool"] == "read_file"


# =============================================================================
# 4. Phase 2.1 Privacy, Data Minimization & Dependency Accuracy Tests
# =============================================================================

def test_diagnostics_contain_no_private_prompts_or_tool_args():
    """Verify data minimization: raw user prompts and tool arguments are never exposed."""
    mgr = TraceManager()
    mgr.start_trace("trace-privacy-test")
    span = mgr.record_span(
        "trace-privacy-test",
        "tool_executed:test_tool",
        metadata={
            "prompt": "Top secret confidential project code 9988",
            "user_input": "My social security number is 000-00-0000",
            "args": {"path": "C:\\Users\\admin\\secret.txt", "content": "confidential data"},
            "screenshot": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."
        }
    )
    assert span is not None
    # Verify prompt minimization (no raw text)
    assert "Top secret" not in str(span.metadata)
    assert "000-00-0000" not in str(span.metadata)
    assert "[PROMPT_MINIMIZED len=" in str(span.metadata["prompt"])

    # Verify tool argument minimization (only arg keys preserved, not values)
    assert "confidential data" not in str(span.metadata)
    assert "secret.txt" not in str(span.metadata)
    assert span.metadata["args"] == {"arg_keys": ["path", "content"]}

    # Verify screenshot minimization (bytes buffer omitted)
    assert "bytes=" in span.metadata["screenshot"]


def test_retained_errors_are_sanitized_before_buffer():
    """Ensure ErrorTracker sanitizes before storing in the in-memory ring buffer."""
    tracker = ErrorTracker(max_history=5)
    raw_leak = "Failed accessing C:\\Users\\johndoe\\secret.env with Bearer eyJhbGciOi..."
    tracker.record_error(
        category=ErrorCategory.INTERNAL_ERROR,
        message=raw_leak,
        correlation_id="corr-mem-1",
        subsystem="storage"
    )

    # Directly inspect internal ring buffer state
    retained = tracker._history[0]
    assert "johndoe" not in retained.message
    assert "[USER_DIR]" in retained.message
    assert "eyJhbGciOi" not in retained.message
    assert "[REDACTED_TOKEN]" in retained.message

    # Verify to_dict structure format
    d = retained.to_dict()
    assert d["category"] == "INTERNAL_ERROR"
    assert d["operation"] == "storage"
    assert d["trace_id"] == "corr-mem-1"


def test_optional_dependencies_reported_accurately():
    """Verify voice diagnostics truthfully report optional dependencies and PTT mode."""
    from core.diagnostics import get_voice_diagnostics
    diag = get_voice_diagnostics()

    assert diag["initialized"] is True
    assert "pyaudio_available" in diag
    assert "optional_pynput_available" in diag
    assert "windows_native_ptt_available" in diag
    assert "push_to_talk_mode" in diag
    assert diag["push_to_talk_mode"] in ["pynput_hook", "windows_native_async", "ui_only"]


def test_websocket_readiness_reflects_actual_production_path():
    """Verify WebSocket endpoint contract with origin checks and init_sync delivery."""
    client = TestClient(app)
    with client.websocket_connect("/ws/hologram", headers={"Origin": "http://127.0.0.1:8000"}) as ws:
        init_data = ws.receive_json()
        assert init_data["event"] == "init_sync"
        assert "state" in init_data
        assert "theme" in init_data