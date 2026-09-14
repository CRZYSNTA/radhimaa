"""
JARVIS V3.0 - Mobile Pairing & Remote Control Test Suite
Validates dynamic PIN pairing, token cryptographic issuance, database registration,
remote input safety boundaries, live telemetry, and FastAPI endpoints.
"""

import os
import time
import pytest
from fastapi.testclient import TestClient

import database
from core.mobile_bridge import (
    generate_pairing_session,
    verify_pairing_pin,
    get_current_pairing_status,
    handle_mouse_event,
    handle_keyboard_event,
    handle_system_command,
    get_system_telemetry,
    get_screen_jpeg,
    get_clipboard_text,
    set_clipboard_text
)
from memory.database import validate_device_token, get_paired_devices, revoke_device
from server import app

@pytest.fixture(autouse=True)
def init_test_db():
    database.init_db()

def test_pairing_session_generation_and_verification():
    # 1. Generate pairing session
    session = generate_pairing_session(ttl_seconds=300)
    assert "pin" in session
    assert len(session["pin"]) == 6
    assert session["ttl_remaining"] > 0
    assert "url" in session
    assert session["primary_ip"]

    # 2. Check active status
    status = get_current_pairing_status()
    assert status["active"] is True
    assert status["pin"] == session["pin"]

    # 3. Reject invalid PIN
    bad_res = verify_pairing_pin("000000", device_name="Unknown Device")
    assert bad_res is None

    # 4. Accept valid PIN & issue token
    res = verify_pairing_pin(session["pin"], device_name="Test Phone")
    assert res is not None
    assert res["success"] is True
    assert "auth_token" in res
    assert "device_id" in res
    token = res["auth_token"]
    dev_id = res["device_id"]

    # 5. PIN cannot be reused
    reuse_res = verify_pairing_pin(session["pin"], device_name="Duplicate")
    assert reuse_res is None

    # 6. Validate token in DB
    dev = validate_device_token(token)
    assert dev is not None
    assert dev["device_name"] == "Test Phone"
    assert dev["device_id"] == dev_id

    # 7. Device in list
    devices = get_paired_devices()
    assert any(d["device_id"] == dev_id for d in devices)

    # 8. Revoke device
    revoked = revoke_device(dev_id)
    assert revoked is True
    assert validate_device_token(token) is None

def test_remote_mouse_and_keyboard_safety():
    # Mouse move
    res_move = handle_mouse_event("move", dx=2, dy=2)
    assert res_move["status"] == "ok"

    # Mouse click
    res_click = handle_mouse_event("click", button="left")
    assert res_click["status"] == "ok"

    # Unknown mouse action
    res_bad = handle_mouse_event("invalid_action")
    assert res_bad["status"] == "error"

    # Keyboard type
    res_type = handle_keyboard_event("type", text="")
    assert res_type["status"] == "ok"

    # Keyboard press
    res_press = handle_keyboard_event("press", key="ctrl")
    assert res_press["status"] == "ok"

    # Unknown keyboard action
    res_kb_bad = handle_keyboard_event("invalid_action")
    assert res_kb_bad["status"] == "error"

def test_system_telemetry_and_screen():
    # Telemetry
    telemetry = get_system_telemetry()
    assert "cpu_percent" in telemetry
    assert "ram_percent" in telemetry
    assert "ram_used_gb" in telemetry
    assert "disk_free_gb" in telemetry
    assert "battery" in telemetry

    # Screen Capture (JPEG format check)
    jpeg_bytes = get_screen_jpeg(quality=40, scale=0.2)
    assert isinstance(jpeg_bytes, bytes)
    assert len(jpeg_bytes) > 500
    # Standard JPEG magic header: FF D8
    assert jpeg_bytes[:2] == b'\xff\xd8'

def test_server_mobile_routes_and_security():
    client = TestClient(app)

    # 1. PWA HTML App delivery
    app_res = client.get("/app")
    assert app_res.status_code == 200
    assert "JARVIS Mobile Companion" in app_res.text
    assert "PAIR MOBILE DEVICE" in app_res.text

    # 2. Pairing verify failure on bad PIN
    bad_pair = client.post("/api/pairing/verify", json={"pin": "999999", "device_name": "Test Client"})
    assert bad_pair.status_code == 400

    # 3. Pairing verify success
    session = generate_pairing_session(ttl_seconds=300)
    good_pair = client.post("/api/pairing/verify", json={"pin": session["pin"], "device_name": "Test Client"})
    assert good_pair.status_code == 200
    data = good_pair.json()
    auth_token = data["auth_token"]
    device_id = data["device_id"]
    assert auth_token

    # 4. Telemetry with paired Bearer token
    headers = {"Authorization": f"Bearer {auth_token}"}
    tel_res = client.get("/api/remote/telemetry", headers=headers)
    assert tel_res.status_code == 200
    assert "cpu_percent" in tel_res.json()

    # 5. Remote system command
    sys_res = client.post("/api/remote/system", json={"command": "volume_mute"}, headers=headers)
    assert sys_res.status_code == 200
    assert sys_res.json()["status"] == "ok"

    # 6. Remote mouse dispatch
    mouse_res = client.post("/api/remote/mouse", json={"action": "move", "dx": 1, "dy": 1}, headers=headers)
    assert mouse_res.status_code == 200
    assert mouse_res.json()["status"] == "ok"

    # 7. Screen endpoint with token query param
    scr_res = client.get(f"/api/remote/screen?token={auth_token}")
    assert scr_res.status_code == 200
    assert scr_res.headers["content-type"] == "image/jpeg"
    assert scr_res.content[:2] == b'\xff\xd8'

    # 8. Unauthenticated rejection
    unauth_res = client.get("/api/remote/telemetry", headers={"Authorization": "Bearer invalid_token_12345"})
    assert unauth_res.status_code in (401, 403)

    # 9. TTS Voice Pack list, generation & voice switching
    voices_res = client.get("/api/tts/voices")
    assert voices_res.status_code == 200
    assert "neural_voices" in voices_res.json()
    assert len(voices_res.json()["neural_voices"]) >= 5

    tts_res = client.post(
        "/api/tts/generate",
        json={"text": "Voice test", "voice": "en-GB-RyanNeural"},
        headers=headers
    )
    assert tts_res.status_code == 200
    assert tts_res.headers["content-type"] == "audio/mpeg"
    assert len(tts_res.content) > 0

    set_voice_res = client.post(
        "/api/tts/set_voice",
        json={"voice": "en-GB-RyanNeural"},
        headers=headers
    )
    assert set_voice_res.status_code == 200
    assert set_voice_res.json()["status"] == "ok"
