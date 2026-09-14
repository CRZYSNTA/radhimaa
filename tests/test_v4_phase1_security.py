"""
JARVIS V4 Phase 1 - Security Hardening & Secret Isolation Test Suite
Validates:
 1. Secret Exfiltration Protection via read_file, write_file, delete_file, list_directory
 2. Loopback CORS & Origin Spoofing Rejection (Local API Hijacking Defense)
 3. WebSocket Origin Verification & Policy Enforcement (1008 on untrusted origin)
 4. Mobile Agent Remote Execution Confirmation Policy Enforcement
 5. Sensitive File Upload Blocking via Mobile Bridge
"""

import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import config
from server import app
from core.permissions import is_sensitive_path, is_path_safe, check_permission, PermissionLevel
from tools.files import read_file, write_file, delete_file, list_directory
from core.mobile_bridge import save_uploaded_file, execute_mobile_agent_query


# =============================================================================
# 1. Secret Exfiltration & Sensitive Path Sandbox Tests
# =============================================================================

@pytest.mark.parametrize("sensitive_file", [
    "config.json",
    "config.py",
    "credentials.json",
    "secrets.json",
    ".phone_config.json",
    ".tv_config.json",
    "jarvis_memory.db",
    "jarvis_memory.db.v3_backup",
    ".env",
    ".env.local",
    ".env.production",
    "server.key",
    "cert.pem",
    "id_rsa",
    "id_rsa.pub",
    "id_ed25519",
    "auth_token.json",
    "api_token.txt",
    ".git/config",
    ".vscode/settings.json",
])
def test_sensitive_paths_identified(sensitive_file):
    """Ensure all critical secret patterns are authoritatively flagged as sensitive."""
    assert is_sensitive_path(sensitive_file) is True
    assert is_path_safe(sensitive_file) is False


def test_secret_read_file_blocked():
    """Verifies that read_file returns the canonical error message without leaking paths."""
    res = read_file("config.json")
    assert "access denied" in res.lower()
    assert "i'm afraid i cannot access that file, sir" in res.lower()

    res_env = read_file(".env")
    assert "access denied" in res_env.lower()
    assert "i'm afraid i cannot access that file, sir" in res_env.lower()


def test_secret_write_and_delete_blocked():
    """Verifies that write_file and delete_file block sensitive targets."""
    res_write = write_file("config.json", "{}")
    assert "access denied" in res_write.lower()
    assert "i'm afraid i cannot access that file, sir" in res_write.lower()

    res_del = delete_file("config.py")
    assert "access denied" in res_del.lower()
    assert "i'm afraid i cannot access that file, sir" in res_del.lower()


def test_list_directory_filters_secrets():
    """Verifies that list_directory completely strips sensitive items from results."""
    listing = list_directory(str(config.BASE_DIR))
    assert "config.json" not in listing
    assert "config.py" not in listing
    assert ".git" not in listing


def test_safe_file_operations_allowed():
    """Verifies that non-sensitive files in safe paths function normally."""
    safe_file = str(Path(config.BASE_DIR) / "safe_test_phase1.txt")
    
    # Write safe file
    w_res = write_file(safe_file, "Safe content for testing.")
    assert "successfully written" in w_res.lower()
    assert os.path.exists(safe_file)

    # Read safe file
    r_res = read_file(safe_file)
    assert r_res == "Safe content for testing."

    # Delete safe file
    d_res = delete_file(safe_file)
    assert "deleted successfully" in d_res.lower()
    assert not os.path.exists(safe_file)


# =============================================================================
# 2. Loopback CORS & Local API Hijacking Defense Tests
# =============================================================================

def test_untrusted_origin_rejected_even_from_loopback():
    """
    Simulates a malicious browser website attempting to hijack loopback API.
    Must be blocked with 403 Forbidden.
    """
    client = TestClient(app)
    malicious_headers = {
        "Origin": "http://evil-attacker.com",
        "Host": "127.0.0.1:8000"
    }

    # Test /ask endpoint
    resp_ask = client.post("/ask", json={"text": "hello"}, headers=malicious_headers)
    assert resp_ask.status_code == 403
    assert "Cross-origin request from origin" in resp_ask.json().get("detail", "")

    # Test /v1/chat endpoint
    resp_chat = client.post("/v1/chat", json={"message": "hello"}, headers=malicious_headers)
    assert resp_chat.status_code == 403


def test_untrusted_referer_rejected():
    """Verifies cross-origin requests with untrusted Referer header are blocked."""
    client = TestClient(app)
    headers = {"Referer": "https://malicious-phishing.org/index.html"}
    resp = client.post("/ask", json={"text": "hello"}, headers=headers)
    assert resp.status_code == 403
    assert "Cross-origin request from referer" in resp.json().get("detail", "")


def test_trusted_origin_accepted():
    """Verifies requests with trusted local origins succeed."""
    client = TestClient(app)
    trusted_headers = {"Origin": "http://127.0.0.1:8000"}
    resp = client.post("/ask", json={"text": "time"}, headers=trusted_headers)
    assert resp.status_code == 200


# =============================================================================
# 3. WebSocket Origin Verification & Policy Enforcement Tests
# =============================================================================

def test_websocket_untrusted_origin_rejected():
    """Verifies /ws/hologram rejects connections from untrusted origins with 1008."""
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/hologram", headers={"Origin": "http://evil.com"}):
            pass
    assert excinfo.value.code == 1008


# =============================================================================
# 4. Mobile Agent Remote Execution Confirmation & Upload Security
# =============================================================================

def test_mobile_agent_requires_confirmation_on_sensitive_actions():
    """
    Verifies that execute_mobile_agent_query does NOT bypass confirmation policies.
    Triggering a CONFIRM-tier action without confirmed=True returns requires_confirmation status.
    """
    result = execute_mobile_agent_query(
        "update note 00 - Inbox/mobile_sec_test: Security test note content",
        conversation_id="test_mobile_sec_conv",
        confirmed=False
    )
    assert result.get("status") == "requires_confirmation"
    assert result.get("requires_confirmation") is True
    assert result.get("success") is False
    assert result.get("tool") == "propose_note_update"


def test_mobile_upload_sensitive_file_blocked():
    """Verifies that uploading sensitive files via mobile bridge is prohibited."""
    with pytest.raises(ValueError) as excinfo:
        save_uploaded_file("config.json", b"{}")
    assert "prohibited" in str(excinfo.value).lower()

    with pytest.raises(ValueError) as excinfo2:
        save_uploaded_file(".env", b"SECRET=123")
    assert "prohibited" in str(excinfo2.value).lower()


def test_mobile_upload_endpoint_blocks_sensitive_file():
    """Verifies that POST /api/remote/upload rejects sensitive files with HTTP 400."""
    client = TestClient(app)
    files = {"file": ("config.json", b"{}", "application/json")}
    resp = client.post("/api/remote/upload", files=files)
    assert resp.status_code == 400
    assert "prohibited" in resp.json().get("detail", "").lower()