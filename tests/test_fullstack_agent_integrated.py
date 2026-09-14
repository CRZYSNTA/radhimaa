"""
JARVIS V3.0 - Test Suite for Fullstack-Agent Capabilities Integration
Verifies Obsidian Memory Vault, bi-directional sync, Push-to-Talk lifecycle,
and Web Visualizer endpoint.
"""

import os
import pytest
from pathlib import Path

from core.permissions import check_permission, PermissionLevel
from core.executor import ToolExecutor
from core.router import route_intent
from memory.vault_sync import (
    ensure_vault_initialized, sync_memory_to_vault, sync_vault_to_memory,
    read_vault_file, append_vault_note, VAULT_DIR
)
from tools.vault_manager import read_memory_vault, write_memory_vault_note, sync_memory_vault
from voice.push_to_talk import start_push_to_talk, stop_push_to_talk


def test_vault_permissions():
    """Verify all vault and PTT tools are SAFE."""
    tools = [
        "read_memory_vault",
        "write_memory_vault_note",
        "sync_memory_vault",
        "open_obsidian_vault",
        "start_push_to_talk",
        "stop_push_to_talk",
    ]
    for t in tools:
        lvl, reason = check_permission(t, {})
        assert lvl == PermissionLevel.SAFE, f"Expected {t} to be SAFE, got {lvl}"


def test_vault_initialization_and_files():
    """Verify vault directory and core markdown files exist."""
    vault_path = ensure_vault_initialized()
    assert vault_path.exists()

    expected_files = ["Identity.md", "Preferences.md", "Projects.md", "Lessons.md"]
    for ef in expected_files:
        p = vault_path / ef
        assert p.exists(), f"File {ef} was not found in vault!"


def test_vault_append_and_read():
    """Verify appending and reading notes from vault."""
    append_res = append_vault_note("Projects", "Automated Testing", "Achieved 100% test pass rate.")
    assert "Appended note" in append_res

    read_res = read_memory_vault("projects")
    assert "Automated Testing" in read_res
    assert "Achieved 100% test pass rate." in read_res


def test_vault_bi_directional_sync():
    """Verify memory to vault and vault to memory syncing."""
    res1 = sync_memory_to_vault()
    assert "Successfully synchronized" in res1

    res2 = sync_vault_to_memory()
    assert "Successfully imported" in res2


def test_push_to_talk_lifecycle():
    """Verify push-to-talk starts and stops cleanly."""
    res = start_push_to_talk(hotkey="F8")
    assert "Push-to-Talk enabled" in res
    assert "[F8]" in res

    stop_push_to_talk()


def test_router_vault_shortcuts():
    """Verify router matches vault intent queries."""
    assert route_intent("open memory vault")["tool"] == "open_obsidian_vault"
    assert route_intent("read vault")["tool"] == "read_memory_vault"
    assert route_intent("sync vault")["tool"] == "sync_memory_vault"


def test_executor_contains_vault_tools():
    """Verify ToolExecutor registers and can execute vault tools."""
    executor = ToolExecutor(confirm_callback=lambda desc: True)
    assert "read_memory_vault" in executor.tools
    assert "write_memory_vault_note" in executor.tools
    assert "sync_memory_vault" in executor.tools
    assert "start_push_to_talk" in executor.tools

    res = executor.execute_step("read_memory_vault", {"category": "preferences"})
    assert res.success is True
    assert "User Preferences" in res.output or "Preferred Voice" in res.output


def test_visualizer_endpoint_serves_html():
    """Verify server.py serves /visualizer with HTML content."""
    from fastapi.testclient import TestClient
    from server import app

    client = TestClient(app)
    resp = client.get("/visualizer")
    assert resp.status_code == 200
    assert "Living Visualizer" in resp.text or "JARVIS V3.0" in resp.text
    assert "visualizerCanvas" in resp.text
