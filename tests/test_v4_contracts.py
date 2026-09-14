"""
Tests for JARVIS V4 Core Contracts and Protocols (Phase M1)
"""

import pytest
from ai.contracts import AIRequest, AIResponse, Message, Role, TokenUsage, AIGateway
from tools.base import Tool, ToolContext, ToolResult, RiskLevel, PermissionTier, VerificationResult
from tools.schemas import validate_tool_arguments, to_openai_tool_schema
from config_v4.settings import get_settings
from memory.repositories import get_conversation_repository, get_fact_repository
from security.audit import record_audit


def test_ai_contracts_data_structures():
    msg = Message(role=Role.USER, content="Hello JARVIS")
    assert msg.to_dict() == {"role": "user", "content": "Hello JARVIS"}

    req = AIRequest(messages=[msg], system_prompt="Be concise")
    assert len(req.messages) == 1
    assert req.correlation_id is not None

    resp = AIResponse(
        content="Greetings, sir.",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        model="test-model",
        provider="test-provider",
        latency_ms=45.2
    )
    assert resp.content == "Greetings, sir."
    assert resp.usage.total_tokens == 15
    assert resp.latency_ms == 45.2


def test_tool_contracts_and_permissions():
    assert PermissionTier.SAFE.value == "SAFE"
    assert PermissionTier.CONFIRM.value == "CONFIRM"
    assert PermissionTier.BLOCKED.value == "BLOCKED"
    assert RiskLevel.LOW.value == "LOW"

    class SampleTool:
        name = "test_tool"
        description = "A sample test tool"
        input_schema = {
            "type": "object",
            "required": ["query"],
            "properties": {"query": {"type": "string"}}
        }
        risk = RiskLevel.LOW
        permission = PermissionTier.SAFE

        async def execute(self, context: ToolContext, arguments: dict) -> ToolResult:
            return ToolResult(success=True, output=f"Found: {arguments['query']}")

        async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
            return VerificationResult(verified=result.success)

    tool = SampleTool()
    assert isinstance(tool, Tool)

    valid, errors = validate_tool_arguments(tool.input_schema, {"query": "weather"})
    assert valid is True
    assert len(errors) == 0

    valid, errors = validate_tool_arguments(tool.input_schema, {})
    assert valid is False
    assert "query" in errors[0]


def test_typed_settings():
    settings = get_settings()
    assert settings.ai is not None
    assert settings.database is not None
    assert settings.security is not None
    assert isinstance(settings.security.rate_limit_per_minute, int)
    assert settings.database.wal_mode is True


def test_memory_repositories():
    conv_repo = get_conversation_repository()
    conv_repo.save_turn("user", "Testing V4 contract persistence")
    recent = conv_repo.get_recent(limit=3)
    assert len(recent) > 0
    assert any("Testing V4 contract persistence" in r.get("content", "") for r in recent)

    fact_repo = get_fact_repository()
    fact_repo.remember("v4_protocol_test", "active")
    assert fact_repo.get_fact("v4_protocol_test") == "active"
    fact_repo.delete_fact("v4_protocol_test")


def test_audit_redaction():
    evt = record_audit(
        event_type="AUTH",
        action="login_attempt",
        status="SUCCESS",
        actor="test_user",
        details={"username": "alice", "api_key": "secret_12345", "token": "bearer_abc"}
    )
    assert evt.details["username"] == "alice"
    assert evt.details["api_key"] == "[REDACTED]"
    assert evt.details["token"] == "[REDACTED]"
