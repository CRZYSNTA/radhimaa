"""
Unit & Integration Tests for JARVIS + LEO Unified Platform.
Tests dual wake-word detection ("Jarvis" vs "Leo"), persona identity resolution,
signal bus synchronization, and LEO tool executor dispatch.
"""

from pathlib import Path
import config
from voice.wake_word import check_wake_word, WakeWordResult
from core.permissions import check_permission, PermissionLevel
from core.executor import ToolExecutor
from communication.broadcaster import get_broadcaster


def test_dual_wake_word_detection():
    # 1. Test "Hey Leo" detection
    res_leo = check_wake_word("Hey Leo what are my priorities")
    assert res_leo[0] is True
    assert res_leo[1] == "what are my priorities"
    assert getattr(res_leo, "identity", None) == "leo"

    # 2. Test solitary "Leo" call
    res_leo_single = check_wake_word("leo")
    assert res_leo_single[0] is True
    assert res_leo_single[1] == ""
    assert getattr(res_leo_single, "identity", None) == "leo"

    # 3. Test "Hey Jarvis" detection
    res_jarvis = check_wake_word("Hey Jarvis turn on the tv")
    assert res_jarvis[0] is True
    assert res_jarvis[1] == "turn on the tv"
    assert getattr(res_jarvis, "identity", None) == "jarvis"

    # 4. Backward compatibility: verify standard 2-tuple unpacking
    detected, cmd = check_wake_word("Hey Leo polacraft status")
    assert detected is True
    assert cmd == "polacraft status"


def test_leo_tools_permissions_and_execution():
    for tool_name in ("open_application", "manage_obsidian_note", "get_system_telemetry"):
        perm, _ = check_permission(tool_name, {})
        assert perm == PermissionLevel.SAFE

    executor = ToolExecutor()
    # Test get_system_telemetry dispatch
    res = executor.execute_step("get_system_telemetry", {})
    assert res.success is True
    assert "hardware status" in str(res.output).lower() or "cpu" in str(res.output).lower()


def test_unified_signal_bus_multi_target_sync():
    broadcaster = get_broadcaster()
    broadcaster.broadcast_state("SPEAKING", "Testing unified bus")

    # Verify workspace root .voice_state was synced
    root_bus = Path(getattr(config, "BASE_DIR", ".")) / ".voice_state"
    if root_bus.exists():
        assert root_bus.read_text(encoding="utf-8").strip().lower() == "speaking"

    broadcaster.broadcast_state("IDLE")
    if root_bus.exists():
        assert root_bus.read_text(encoding="utf-8").strip().lower() == "idle"


def test_unified_assistant_greeting():
    from core.router import route_intent
    for wake_greeting in ("jarvis", "leo", "hey jarvis", "hey leo", "hello"):
        routed = route_intent(wake_greeting)
        assert routed["type"] == "GREETING"
        assert routed["response"] == "Hello Gowtham, what are we working on today?"

