"""
Unit tests for Controlled Tools and Permission Gates.
Verifies input validation, timeouts, safe execution, and confirmation requirement.
"""

import pytest
from tools.base import ToolContext, PermissionTier
from orchestration.tool_router import ToolRouter


@pytest.mark.asyncio
async def test_telemetry_tool_safe_execution():
    router = ToolRouter()
    ctx = ToolContext(session_id="test_sess", user_id="gowtham", correlation_id="c1")
    res = await router.execute_tool("get_system_telemetry", {}, ctx)
    assert res.success is True
    assert isinstance(res.output, dict)
    assert "cpu_percent" in res.output
    assert "ram_percent" in res.output
    assert res.execution_time_ms < 5000


@pytest.mark.asyncio
async def test_open_application_allowlist_validation():
    router = ToolRouter()
    ctx = ToolContext(session_id="test_sess", user_id="gowtham", correlation_id="c2")

    # Rejected app
    res_bad = await router.execute_tool("open_application", {"application_id": "malicious_script.exe"}, ctx)
    assert res_bad.success is False
    assert "not in the allowlist" in res_bad.error

    # Allowed app validation (dry check on calc or notepad)
    tool = router.get_tool("open_application")
    assert tool.permission == PermissionTier.SAFE


@pytest.mark.asyncio
async def test_set_volume_bounds_level():
    router = ToolRouter()
    ctx = ToolContext(session_id="test_sess", user_id="gowtham", correlation_id="c3")
    res = await router.execute_tool("set_volume", {"level": 35}, ctx)
    assert res.success is True
    assert "35%" in res.output

    res2 = await router.execute_tool("set_volume", {"action": "up"}, ctx)
    assert res2.success is True
    assert "%" in res2.output


@pytest.mark.asyncio
async def test_read_note_safe_execution():
    router = ToolRouter()
    ctx = ToolContext(session_id="test_sess", user_id="gowtham", correlation_id="c4")
    res = await router.execute_tool("read_note", {"relative_path": "Active Priorities"}, ctx)
    assert res.success is True
    assert "Source:" in res.output


@pytest.mark.asyncio
async def test_propose_note_update_requires_confirmation():
    router = ToolRouter()
    ctx_unconfirmed = ToolContext(session_id="test_sess", user_id="gowtham", correlation_id="c5", metadata={"is_confirmed": False})
    res = await router.execute_tool("propose_note_update", {
        "relative_path": "00 - Inbox/test_idea.md",
        "content": "---\nstatus: active\n---\nTest note content"
    }, ctx_unconfirmed)

    # Must NOT write immediately; must require confirmation
    assert res.success is False
    assert res.metadata.get("requires_confirmation") is True
    assert res.metadata.get("tool") == "propose_note_update"
    assert "arguments" in res.metadata
    assert res.metadata["arguments"]["relative_path"] == "00 - Inbox/test_idea.md"

    # Confirmed execution
    ctx_confirmed = ToolContext(session_id="test_sess", user_id="gowtham", correlation_id="c6", metadata={"is_confirmed": True})
    res_confirmed = await router.execute_tool("propose_note_update", {
        "relative_path": "00 - Inbox/test_idea.md",
        "content": "---\nstatus: active\n---\nTest note content"
    }, ctx_confirmed)
    assert res_confirmed.success is True
    assert "successfully updated note" in res_confirmed.output.lower()


def test_controlled_tools_routing():
    from core.router import route_intent
    r1 = route_intent("system telemetry")
    assert r1["type"] == "SIMPLE"
    assert r1["tool"] == "get_system_telemetry"

    r2 = route_intent("open notepad")
    assert r2["type"] == "SIMPLE"
    assert r2["tool"] == "open_application"
    assert r2["params"]["application_id"] == "notepad"

    r3 = route_intent("read note Active Priorities")
    assert r3["type"] == "SIMPLE"
    assert r3["tool"] == "read_note"
    assert r3["params"]["relative_path"] == "Active Priorities"

    r4 = route_intent("update note 00 - Inbox/quick_idea: meeting summary")
    assert r4["type"] == "SIMPLE"
    assert r4["tool"] == "propose_note_update"
    assert r4["params"]["relative_path"] == "00 - Inbox/quick_idea"
    assert r4["params"]["content"] == "meeting summary"

    r5 = route_intent("volume level 65")
    assert r5["type"] == "SIMPLE"
    assert r5["tool"] == "set_volume"
    assert r5["params"]["level"] == 65


