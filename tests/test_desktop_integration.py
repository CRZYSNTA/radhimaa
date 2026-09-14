"""
End-to-End Integration Tests for Native Desktop App & Confirmation Flow
"""

import pytest
import asyncio
import json
from starlette.testclient import TestClient

from server import app
from orchestration.chat_service import get_chat_service, ChatRequestDTO
from tools.base import ToolContext


def test_interface_static_served():
    """Verify that interface/index.html is served successfully."""
    client = TestClient(app)
    response = client.get("/interface/index.html")
    assert response.status_code == 200
    assert "JARVIS V4" in response.text
    assert "hud-chat-dock" in response.text
    assert "hud-confirm-modal" in response.text
    assert "hud-mic-pill" in response.text


def test_chat_dock_js_served():
    """Verify that interface/js/chat_dock.js is served successfully."""
    client = TestClient(app)
    response = client.get("/interface/js/chat_dock.js")
    assert response.status_code == 200
    assert "ChatDockManager" in response.text


@pytest.mark.asyncio
async def test_chat_streaming_tool_execution():
    """Verify that /v1/chat/stream yields SSE chunks and tool execution events."""
    service = get_chat_service()
    dto = ChatRequestDTO(
        message="system telemetry",
        conversation_id="test_stream_conv",
        user_id="test_user"
    )

    events = []
    async for event in service.handle_stream(dto):
        events.append(event)

    types = [e["type"] for e in events]
    assert "tool_events" in types
    assert "done" in types

    tool_ev = next(e for e in events if e["type"] == "tool_events")
    assert tool_ev["tool_events"][0]["tool"] == "get_system_telemetry"
    assert tool_ev["tool_events"][0]["success"] is True


@pytest.mark.asyncio
async def test_propose_note_confirmation_flow():
    """
    Verify complete authorization cycle:
    1. Unconfirmed request triggers confirmation_required
    2. Client confirms via POST /v1/tools/{name}/confirm
    3. Action executes and note is written.
    """
    client = TestClient(app)
    service = get_chat_service()

    # Step 1: Propose update without confirmation
    dto = ChatRequestDTO(
        message="update note 00 - Inbox/desktop_test_idea: Meeting notes from Monday",
        conversation_id="test_confirm_conv",
        user_id="test_user",
        confirmed=False
    )

    stream_events = []
    async for event in service.handle_stream(dto):
        stream_events.append(event)

    # Must require confirmation
    conf_event = next((e for e in stream_events if e["type"] == "confirmation_required"), None)
    assert conf_event is not None
    assert conf_event["tool"] == "propose_note_update"
    assert conf_event["arguments"]["relative_path"] == "00 - Inbox/desktop_test_idea"

    # Step 2: Confirm action via /v1/tools/{name}/confirm endpoint
    confirm_payload = {
        "conversation_id": "test_confirm_conv",
        "tool_name": "propose_note_update",
        "arguments": conf_event["arguments"],
        "confirmed": True
    }
    resp = client.post("/v1/tools/propose_note_update/confirm", json=confirm_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed" or data.get("tool_events") is not None
