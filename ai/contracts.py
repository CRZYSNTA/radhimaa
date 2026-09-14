"""
JARVIS V4 - AI Contracts and Protocols
Defines standard request/response DTOs and the AIGateway protocol.
Model choice and provider mechanics live behind this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Protocol, AsyncIterator, runtime_checkable
import time
import uuid


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    role: Role | str
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        role_val = self.role.value if isinstance(self.role, Role) else str(self.role)
        data = {"role": role_val, "content": self.content}
        if self.name:
            data["name"] = self.name
        if self.tool_call_id:
            data["tool_call_id"] = self.tool_call_id
        return data


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class AIRequest:
    messages: List[Message]
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stream: bool = False
    timeout: float = 30.0


@dataclass
class AIResponse:
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = "unknown"
    provider: str = "unknown"
    latency_ms: float = 0.0
    correlation_id: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None


@runtime_checkable
class AIGateway(Protocol):
    """
    Authoritative AI Gateway protocol.
    Owns provider selection, cascading fallbacks, token usage, and latency tracking.
    Must not know about UI, PyAutoGUI, or database details.
    """

    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate a complete model response."""
        ...

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        """Stream generated text chunks incrementally."""
        ...

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for semantic search."""
        ...
