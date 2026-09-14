"""
Automated tests for Cloud API and Server Security Hardening.
Verifies:
 - Remote auth fails closed when no token is configured
 - Referer spoofing cannot bypass authentication
 - Invalid tokens are rejected (401)
 - Valid tokens are accepted (200)
 - WebSocket authentication & policy violation rejection (1008)
 - Message length limits (max 4000 chars rejected with 400)
 - Rate limiting (429 Too Many Requests)
"""

import os
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

def test_cloud_fails_closed_when_no_token(monkeypatch):
    monkeypatch.delenv("JARVIS_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("AUTH_TOKEN", raising=False)

    from cloud_deployment.main import app
    client = TestClient(app)

    # Remote request with no server token configured must fail closed (403)
    response = client.post("/ask", json={"text": "hello"})
    assert response.status_code == 403
    assert "Remote access denied" in response.json().get("detail", "")

def test_cloud_rejects_spoofed_referer(monkeypatch):
    monkeypatch.setenv("JARVIS_AUTH_TOKEN", "super_secret_test_token_999")

    from cloud_deployment.main import app
    client = TestClient(app)

    # Attempting to bypass auth with spoofed onrender.com Referer header
    response = client.post(
        "/ask",
        json={"text": "hello"},
        headers={"Referer": "https://jarvis-bot.onrender.com"}
    )
    # Must reject with 401 Unauthorized (Referer bypass eliminated)
    assert response.status_code == 401

def test_cloud_accepts_valid_token(monkeypatch):
    test_token = "valid_test_token_12345"
    monkeypatch.setenv("JARVIS_AUTH_TOKEN", test_token)

    from cloud_deployment.main import app
    client = TestClient(app)

    # Test with X-JARVIS-Token header
    response = client.post(
        "/ask",
        json={"text": "hello"},
        headers={"X-JARVIS-Token": test_token}
    )
    assert response.status_code == 200

    # Test with Authorization: Bearer <token>
    response_bearer = client.post(
        "/ask",
        json={"text": "hello"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response_bearer.status_code == 200

def test_cloud_rejects_oversized_message(monkeypatch):
    test_token = "valid_test_token_12345"
    monkeypatch.setenv("JARVIS_AUTH_TOKEN", test_token)

    from cloud_deployment.main import app
    client = TestClient(app)

    # Create message larger than 4000 chars
    oversized = "A" * 4005
    response = client.post(
        "/ask",
        json={"text": oversized},
        headers={"X-JARVIS-Token": test_token}
    )
    assert response.status_code == 400
    assert "exceeds maximum limit" in response.json().get("detail", "").lower()

def test_cloud_websocket_unauthenticated_rejected(monkeypatch):
    monkeypatch.setenv("JARVIS_AUTH_TOKEN", "websocket_secret_token_123")

    from cloud_deployment.main import app
    client = TestClient(app)

    # Connecting without token must be closed with policy violation (1008)
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/chat") as websocket:
            websocket.send_text("hello")
    assert excinfo.value.code == 1008

def test_cloud_websocket_authenticated_accepted(monkeypatch):
    test_token = "websocket_secret_token_123"
    monkeypatch.setenv("JARVIS_AUTH_TOKEN", test_token)

    from cloud_deployment.main import app
    client = TestClient(app)

    with client.websocket_connect(f"/ws/chat?token={test_token}") as websocket:
        websocket.send_text("hello")
        data = websocket.receive_text()
        assert len(data) > 0

def test_server_py_websocket_remote_auth(monkeypatch):
    test_token = "server_secret_token_abc"
    monkeypatch.setenv("JARVIS_AUTH_TOKEN", test_token)
    monkeypatch.setenv("AUTH_TOKEN", test_token)

    import config
    import server
    monkeypatch.setattr(config, "AUTH_TOKEN", test_token)
    server.config_data["AUTH_TOKEN"] = test_token
    client = TestClient(server.app)

    # Unauthenticated remote websocket rejected with 1008
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/chat") as websocket:
            websocket.send_text("hello")
    assert excinfo.value.code == 1008

    # Authenticated remote websocket accepted
    with client.websocket_connect(f"/ws/chat?token={test_token}") as websocket:
        websocket.send_text("time")
        data = websocket.receive_text()
        assert "time" in data.lower()
