"""
Unit and Integration Tests for LEO Full-Stack Capabilities in JARVIS:
- Obsidian Vault integration (das and co)
- Active priorities, daily notes, and inbox capture
- Project context retrieval (Polacraft, Canvs, Screenplays)
- Router fast-paths
- Tool executor dispatch
- Visualizer signal bus emission
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.permissions import check_permission, PermissionLevel
from core.router import route_intent
from core.executor import ToolExecutor
from memory.vault_sync import (
    get_active_priorities, update_active_priorities,
    log_daily_note, capture_inbox_item, read_project_context,
    VAULT_DIR
)
from voice.text_to_speech import emit_voice_state


def test_leo_vault_permissions():
    leo_tools = [
        "get_active_priorities",
        "update_active_priorities",
        "log_daily_note",
        "capture_inbox_item",
        "read_project_context",
    ]
    for tool in leo_tools:
        level, _ = check_permission(tool, {})
        assert level == PermissionLevel.SAFE, f"{tool} should have SAFE permission"


def test_leo_router_intents():
    # Active Priorities
    res_prio = route_intent("what are my priorities")
    assert res_prio["type"] == "SIMPLE"
    assert res_prio["tool"] == "get_active_priorities"

    # Daily note
    res_daily = route_intent("log daily completed testing suite with 100% pass rate")
    assert res_daily["type"] == "SIMPLE"
    assert res_daily["tool"] == "log_daily_note"
    assert "completed testing" in res_daily["params"]["entry"]

    # Inbox
    res_inbox = route_intent("inbox new screenwriting idea for act 2")
    assert res_inbox["type"] == "SIMPLE"
    assert res_inbox["tool"] == "capture_inbox_item"
    assert "screenwriting" in res_inbox["params"]["text"]

    # Projects
    res_pola = route_intent("check polacraft status")
    assert res_pola["type"] == "SIMPLE"
    assert res_pola["tool"] == "read_project_context"
    assert res_pola["params"]["project"] == "polacraft"

    res_canvs = route_intent("open canvs roadmap")
    assert res_canvs["type"] == "SIMPLE"
    assert res_canvs["tool"] == "read_project_context"
    assert res_canvs["params"]["project"] == "canvs"


def test_leo_executor_dispatch():
    executor = ToolExecutor()
    tools = [
        "get_active_priorities", "update_active_priorities",
        "log_daily_note", "capture_inbox_item", "read_project_context"
    ]
    for t in tools:
        assert t in executor.tools


def test_leo_vault_operations(tmp_path):
    with patch("memory.vault_sync.VAULT_DIR", tmp_path):
        # 1. Priorities
        update_active_priorities("- [x] Complete LEO integration")
        prio = get_active_priorities()
        assert "Complete LEO integration" in prio

        # 2. Inbox capture
        inbox_res = capture_inbox_item("Research new fabric supplier")
        assert "Saved thought to Inbox" in inbox_res
        inbox_files = list((tmp_path / "00 - Inbox").glob("*.md"))
        assert len(inbox_files) == 1
        assert "Research new fabric supplier" in inbox_files[0].read_text(encoding="utf-8")

        # 3. Daily note logging
        daily_res = log_daily_note("Shipped Polacraft customer batch")
        assert "Logged to daily note" in daily_res
        daily_files = list((tmp_path / "01 - Daily Notes").rglob("*.md"))
        assert len(daily_files) >= 1
        found_content = any("Shipped Polacraft customer batch" in f.read_text(encoding="utf-8") for f in daily_files)
        assert found_content


def test_leo_visualizer_signal_bus(tmp_path):
    with patch("voice.text_to_speech.SIGNAL_DIRS", [tmp_path]):
        emit_voice_state("speaking")
        state_file = tmp_path / ".voice_state"
        assert state_file.exists()
        assert state_file.read_text(encoding="utf-8") == "speaking"

        emit_voice_state("idle")
        assert state_file.read_text(encoding="utf-8") == "idle"
