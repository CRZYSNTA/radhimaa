"""
Unit & integration tests for Conversational Sessions (JARVIS V3.1).
Verifies:
 - Session initialization & wake activation
 - Multi-turn conversation continuation
 - Session timeout expiry
 - Explicit goodbye / termination command
 - Context persistence across turns
"""

import time
import pytest
from core.session import (
    ConversationSession,
    SessionManager,
    get_session_manager,
    TERMINATION_PHRASES
)

def test_session_lifecycle():
    sm = SessionManager(timeout_seconds=2.0)
    assert not sm.is_session_active()

    # Create session
    session = sm.get_or_create_session(activated_by_wake=True)
    assert session.is_active
    assert sm.is_session_active()
    assert session.turn_count == 0

    # Record turn
    session.record_turn("open youtube", "Opening YouTube, sir.")
    assert session.turn_count == 1
    assert len(session.history) == 1

def test_session_context_tracking():
    sm = SessionManager(timeout_seconds=10.0)
    session = sm.get_or_create_session()
    sm.update_context("current_app", "Chrome")
    sm.update_context("last_target", "YouTube")

    ctx = sm.get_context()
    assert ctx["current_app"] == "Chrome"
    assert ctx["last_target"] == "YouTube"

def test_session_termination():
    sm = SessionManager(timeout_seconds=10.0)
    session = sm.get_or_create_session()
    assert sm.is_session_active()

    # Say goodbye
    closed = sm.check_termination("Goodbye Jarvis, power down")
    assert closed
    assert not sm.is_session_active()
    assert not session.is_active

def test_session_timeout():
    sm = SessionManager(timeout_seconds=0.1)
    session = sm.get_or_create_session()
    assert not session.is_expired()

    time.sleep(0.15)
    assert session.is_expired()
    assert not sm.is_session_active()

