"""
Unit and Integration Tests for JARVIS V4 Holographic Interface Subsystem.
Verifies broadcaster event serialization, theme intent routing, executor dispatch,
and FastAPI static/WebSocket endpoints.
"""

import json
import pytest
from communication.broadcaster import get_broadcaster
from core.router import route_intent
from core.permissions import check_permission, PermissionLevel
from core.executor import ToolExecutor


def test_hologram_broadcaster_serialization():
    broadcaster = get_broadcaster()
    received_events = []

    def subscriber(msg_str):
        received_events.append(json.loads(msg_str))

    broadcaster.subscribe(subscriber)
    try:
        broadcaster.broadcast_state("LISTENING", "Awaiting wake word")
        broadcaster.broadcast_theme("cyan")
        broadcaster.broadcast_audio_level(0.85)
        broadcaster.broadcast_command("TV_VOLUME_UP", {"value": 15})
        broadcaster.broadcast_assistant_text("Good evening, sir.")
        broadcaster.broadcast_system_status(25.5, 42.0, "CONNECTED")
        broadcaster.broadcast_tv_status("POWER_ON", {"app": "YouTube"})

        event_types = [e.get("event") for e in received_events]
        assert "state_change" in event_types
        assert "theme_change" in event_types
        assert "audio_level" in event_types
        assert "command" in event_types
        assert "assistant_text" in event_types
        assert "system_status" in event_types
        assert "tv_status" in event_types

        # Verify state payload
        state_ev = next(e for e in received_events if e.get("event") == "state_change")
        assert state_ev["state"] == "LISTENING"

        # Verify audio level clamping
        broadcaster.broadcast_audio_level(1.5)
        audio_ev = received_events[-1]
        assert audio_ev["level"] <= 1.0
    finally:
        broadcaster.unsubscribe(subscriber)


def test_hologram_router_theme_intents():
    r1 = route_intent("switch to blue")
    assert r1["type"] == "SIMPLE"
    assert r1["tool"] == "set_hologram_theme"
    assert r1["params"]["theme"] == "blue"

    r2 = route_intent("activate green mode")
    assert r2["type"] == "SIMPLE"
    assert r2["tool"] == "set_hologram_theme"
    assert r2["params"]["theme"] == "green"

    r3 = route_intent("activate warning mode")
    assert r3["type"] == "SIMPLE"
    assert r3["tool"] == "set_hologram_theme"
    assert r3["params"]["theme"] == "red"

    r4 = route_intent("change theme to orange")
    assert r4["type"] == "SIMPLE"
    assert r4["tool"] == "set_hologram_theme"
    assert r4["params"]["theme"] == "orange"


def test_hologram_permissions_and_executor():
    perm, _ = check_permission("set_hologram_theme", {"theme": "purple"})
    assert perm == PermissionLevel.SAFE

    executor = ToolExecutor()
    res = executor.execute_step("set_hologram_theme", {"theme": "purple"})
    assert res.success is True
    assert "purple" in res.output.lower()


def test_hologram_server_routes():
    from fastapi.testclient import TestClient
    from server import app

    client = TestClient(app)

    # 1. Test /hologram HTML route
    resp = client.get("/hologram")
    assert resp.status_code == 200
    assert "JARVIS V4" in resp.text
    assert "webgl-container" in resp.text

    # 2. Test static file delivery
    css_resp = client.get("/interface/css/jarvis.css")
    assert css_resp.status_code == 200
    assert "--jarvis-primary" in css_resp.text

    # 3. Test WebSocket connection & initial synchronization burst
    with client.websocket_connect("/ws/hologram") as ws:
        init_data = ws.receive_json()
        assert init_data["event"] == "init_sync"
        assert "state" in init_data
        assert "theme" in init_data
