"""
Unit tests for Obsidian Vault Subsystem.
Tests startup read-only context loading, relative note retrieval, and proposal generation.
"""

from pathlib import Path
import pytest
from memory.obsidian_vault import ObsidianVaultManager, get_vault_manager


def test_vault_startup_loads_only_index_and_priorities():
    vm = get_vault_manager()
    ctx = vm.load_startup_context()
    assert "vault_status" in ctx
    assert "vault_index" in ctx
    assert "active_priorities" in ctx
    if vm.is_available():
        assert ctx["vault_status"] == "ready"
        assert "Gowtham" in ctx["vault_index"] or "VAULT" in ctx["vault_index"]


def test_vault_read_existing_note_identifies_source():
    vm = get_vault_manager()
    if not vm.is_available():
        pytest.skip("Obsidian vault directory not found")

    ok, content = vm.read_note("Active Priorities")
    assert ok is True
    assert "=== Source:" in content
    assert "Active Priorities" in content


def test_vault_path_containment_prevents_escape():
    vm = get_vault_manager()
    ok, err = vm.read_note("../../windows/system32/cmd.exe")
    assert ok is False
    assert "escapes vault boundary" in err.lower() or "denied" in err.lower()


def test_vault_propose_note_update_requires_confirmation():
    vm = get_vault_manager()
    proposal = vm.propose_note_update("00 - Inbox/test_idea.md", "---\nstatus: active\nproject: meta\n---\nTest Idea")
    assert proposal["success"] is True
    assert proposal["requires_confirmation"] is True
    assert proposal["has_valid_frontmatter"] is True
    assert proposal["target_path"] == "00 - Inbox/test_idea.md"
