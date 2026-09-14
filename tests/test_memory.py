"""
Unit tests for Memory Subsystem.
"""

from memory import (
    init_db, user_memory, conversation_manager,
    search_facts, log_action, get_action_logs
)

def test_user_memory_crud():
    init_db()
    user_memory.remember("operating_system", "Windows 11")
    assert user_memory.get_fact("operating_system") == "Windows 11"

    # Search
    matches = search_facts("operating")
    assert len(matches) > 0
    assert matches[0]["value"] == "Windows 11"

    # Forget
    assert user_memory.forget("operating_system")
    assert user_memory.get_fact("operating_system") is None

def test_user_fact_extraction():
    # Heuristic extraction
    extracted = user_memory.extract_and_remember("My name is Stark.")
    assert extracted is not None
    assert user_memory.get_fact("user_name") == "Stark"

def test_conversation_sliding_window():
    conversation_manager.save_turn("user", "Hello test 1")
    conversation_manager.save_turn("assistant", "Greetings test 1")

    recent = conversation_manager.get_recent(limit=2)
    assert len(recent) == 2
    assert recent[-1]["content"] == "Greetings test 1"

    context = conversation_manager.get_context_window(max_turns=2)
    assert "User: Hello test 1" in context
    assert "Assistant: Greetings test 1" in context

def test_action_logging():
    log_action(
        goal="mute sound",
        tool="volume_mute",
        params={},
        permission="SAFE",
        success=True,
        error="",
        duration_ms=12.5
    )
    logs = get_action_logs(limit=1, tool="volume_mute")
    assert len(logs) == 1
    assert logs[0]["tool"] == "volume_mute"
    assert logs[0]["success"] == 1
