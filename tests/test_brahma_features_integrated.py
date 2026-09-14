"""
JARVIS V3.0 - Test Suite for Integrated Automation Features & UI Overlay Suite
Verifies 100% native independence, safety permissions, background monitoring,
meeting assistant lifecycle, proactive engine prompt rotation, and PySide UI components.
"""

import os
import time
import pytest
from pathlib import Path

import config
from core.permissions import check_permission, PermissionLevel
from core.executor import ToolExecutor
from core.router import route_intent
from core.proactive_engine import JarvisProactiveEngine
from tools.background_monitor import (
    monitor_crypto_price, monitor_website_uptime, monitor_system_resources,
    list_background_monitors, cancel_background_monitor
)
from tools.meeting_assistant import start_meeting_recording, stop_meeting_recording
from tools.computer import tile_window_left, tile_window_right, minimize_all_windows, snap_window


def test_permissions_for_new_features():
    """All newly added tools must evaluate to PermissionLevel.SAFE."""
    new_tools = [
        "monitor_crypto_price",
        "monitor_website_uptime",
        "monitor_system_resources",
        "list_background_monitors",
        "cancel_background_monitor",
        "start_meeting_recording",
        "stop_meeting_recording",
        "download_youtube_audio",
        "download_youtube_video",
        "tile_window_left",
        "tile_window_right",
        "minimize_all_windows",
        "snap_window",
        "browser_navigate",
        "browser_click_element",
        "browser_type_text",
        "browser_capture_page",
        "browser_extract_text",
    ]
    for tool_name in new_tools:
        level, reason = check_permission(tool_name, {})
        assert level == PermissionLevel.SAFE, f"Tool {tool_name} was expected to be SAFE, got {level}"


def test_background_monitor_lifecycle():
    """Verify background monitor registration, listing, and cancellation."""
    msg1 = monitor_crypto_price(coin_id="bitcoin", threshold=95000.0, condition="above", interval_sec=15)
    assert "Bitcoin" in msg1 or "bitcoin" in msg1.lower()

    msg2 = monitor_website_uptime(url="https://google.com", interval_sec=20)
    assert "google.com" in msg2

    msg3 = monitor_system_resources(ram_threshold=90.0, cpu_threshold=95.0)
    assert "System health" in msg3

    active = list_background_monitors()
    assert "Crypto:" in active
    assert "Web Uptime:" in active
    assert "Hardware:" in active

    # Cancel one
    res = cancel_background_monitor("bitcoin")
    assert "Cancelled" in res


def test_proactive_engine_rotation_and_trigger():
    """Verifies idle time gating and non-repetitive context rotation."""
    engine = JarvisProactiveEngine(min_silence_secs=10, cooldown_secs=5)

    # When user just spoke, trigger should be False
    now = time.monotonic()
    assert engine.should_trigger(last_user_interaction=now) is False

    # When user has been idle for > 10s and not busy
    assert engine.should_trigger(last_user_interaction=now - 15) is True

    # Build prompts across rotations to verify diversity
    p1 = engine.build_proactive_prompt(user_facts=["Likes morning coffee"], active_tasks=["Coding"])
    engine.mark_triggered()
    assert "[PROACTIVE_TRIGGER]" in p1
    assert "goals or projects" in p1

    p2 = engine.build_proactive_prompt()
    engine.mark_triggered()
    assert "wellbeing" in p2

    p3 = engine.build_proactive_prompt()
    engine.mark_triggered()
    assert "proactive assistance" in p3


def test_meeting_assistant_recording_and_markdown():
    """Verify meeting recorder start, stop, and clean markdown report generation."""
    start_msg = start_meeting_recording(meeting_title="Architecture Review")
    assert "initiated" in start_msg.lower() or "active" in start_msg.lower()

    time.sleep(0.05)

    stop_res = stop_meeting_recording(meeting_title="Architecture Review", participants="Tony, JARVIS")
    assert "Architecture Review" in stop_res
    assert "Key Decisions" in stop_res
    assert "Action Items" in stop_res

    # Verify report was written to sandbox
    sandbox_dir = Path(config.SANDBOX_DIR).resolve()
    reports = list(sandbox_dir.glob("meeting_notes_*.md"))
    assert len(reports) > 0, "Meeting markdown report was not found in sandbox!"


def test_router_new_shortcuts():
    """Verify router matches newly added intent patterns."""
    assert route_intent("tile left")["tool"] == "tile_window_left"
    assert route_intent("tile right")["tool"] == "tile_window_right"
    assert route_intent("show desktop")["tool"] == "minimize_all_windows"
    assert route_intent("start meeting recording")["tool"] == "start_meeting_recording"
    assert route_intent("stop meeting recording")["tool"] == "stop_meeting_recording"
    assert route_intent("list background monitors")["tool"] == "list_background_monitors"


def test_executor_can_dispatch_new_tools():
    """Verify ToolExecutor contains and can invoke newly added tools."""
    executor = ToolExecutor(confirm_callback=lambda desc: True)

    # Verify tools exist in executor dictionary
    assert "tile_window_left" in executor.tools
    assert "monitor_crypto_price" in executor.tools
    assert "start_meeting_recording" in executor.tools
    assert "browser_navigate" in executor.tools
    assert "download_youtube_audio" in executor.tools

    # Test safe execution through executor
    res = executor.execute_step("tile_window_left", {})
    assert res.success is True


def test_ui_overlay_module_exports():
    """Verify all UI overlay widgets can be imported and have expected interfaces."""
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    from ui.overlay import (
        JarvisFloatingOrb, JarvisCommandBar, JarvisScanningOverlay, JarvisTaskHUD,
        show_scanning_overlay, show_task_hud, set_ui_state
    )
    assert JarvisFloatingOrb is not None
    assert JarvisCommandBar is not None
    assert JarvisScanningOverlay is not None
    assert JarvisTaskHUD is not None

    # Verify set_ui_state without error
    set_ui_state("IDLE", "Test idle state")
    set_ui_state("OBSERVING", "Scanning display")

