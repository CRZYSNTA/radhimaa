"""
JARVIS V4 - Vertical Slice Integration Tests
Validates the authoritative vertical slice specified in Section 21 of the V4 Specification:
POST /v1/chat -> ChatService -> JARVIS Orchestrator -> AI Gateway -> Provider -> SQLite persistence.
Also validates ToolRouter schema validation, permission checks, and legacy API backward compatibility.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

from orchestration.chat_service import get_chat_service, ChatRequestDTO
from orchestration.orchestrator import get_orchestrator
from orchestration.ai_gateway import get_ai_gateway
from orchestration.tool_router import get_tool_router
from tools.base import ToolContext, PermissionTier
from memory.repositories import get_conversation_repository
from server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_v4_ai_gateway_generation():
    gateway = get_ai_gateway()
    from ai.contracts import AIRequest, Message, Role

    req = AIRequest(
        messages=[Message(role=Role.USER, content="Hello JARVIS, are you online?")]
    )
    resp = asyncio.run(gateway.generate(req))
    assert resp.content is not None
    assert len(resp.content) > 0
    assert resp.latency_ms >= 0.0
    assert resp.correlation_id == req.correlation_id


def test_v4_vertical_slice_chat_service():
    service = get_chat_service()
    req = ChatRequestDTO(
        message="What is the capital of France?",
        user_id="test_user"
    )
    resp = asyncio.run(service.handle(req))
    assert resp.conversation_id is not None
    assert resp.status in ("completed", "requires_confirmation")
    assert resp.content is not None

    # Verify SQLite conversation persistence
    conv_repo = get_conversation_repository()
    recent = conv_repo.get_recent(limit=5)
    assert any("What is the capital of France?" in r.get("content", "") for r in recent)


def test_v4_fastapi_v1_chat_endpoint(client):
    response = client.post("/v1/chat", json={
        "message": "Hello from V4 client!",
        "confirmed": False
    })
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "content" in data
    assert data["status"] in ("completed", "requires_confirmation")


def test_v4_tool_router_safe_execution():
    router = get_tool_router()
    tool = router.get_tool("web_search")
    assert tool is not None
    assert tool.permission == PermissionTier.SAFE

    context = ToolContext(session_id="test_sess", user_id="test_user")
    res = asyncio.run(router.execute_tool("web_search", {"query": "Python programming"}, context))
    assert res.success is True
    assert res.output is not None
    assert res.verification is not None
    assert res.verification.verified is True


def test_v4_tool_router_confirm_permission_gate():
    router = get_tool_router()
    tool = router.get_tool("restart_pc")
    assert tool is not None
    assert tool.permission == PermissionTier.CONFIRM

    # 1. Without confirmation -> blocked with requires_confirmation
    context_unconfirmed = ToolContext(session_id="test_sess", user_id="test_user", metadata={"is_confirmed": False})
    res = asyncio.run(router.execute_tool("restart_pc", {}, context_unconfirmed))
    assert res.success is False
    assert res.metadata.get("requires_confirmation") is True

    # 2. With confirmation -> succeeds
    context_confirmed = ToolContext(session_id="test_sess", user_id="test_user", metadata={"is_confirmed": True, "test_mode": True})
    res_confirmed = asyncio.run(router.execute_tool("restart_pc", {}, context_confirmed))
    assert res_confirmed.success is True


def test_v4_legacy_compatibility_endpoints(client, monkeypatch):
    test_token = "valid_v4_test_token"
    monkeypatch.setenv("JARVIS_AUTH_TOKEN", test_token)
    headers = {"x-jarvis-token": test_token}

    # Test /ask backwards compatibility through ChatService
    res_ask = client.post("/ask", json={"text": "Hello JARVIS legacy"}, headers=headers)
    assert res_ask.status_code == 200
    data_ask = res_ask.json()
    assert "reply" in data_ask
    assert len(data_ask["reply"]) > 0

    # Test /api/chat backwards compatibility
    res_chat = client.post("/api/chat", json={"message": "Legacy API chat ping"}, headers=headers)
    assert res_chat.status_code == 200
    data_chat = res_chat.json()
    assert "response" in data_chat
    assert len(data_chat["response"]) > 0
