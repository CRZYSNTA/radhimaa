"""
JARVIS V4 - Tool Base Contracts and Protocols
Defines typed tools, execution contexts, verification results, and permission tiers.
The model can request an action but cannot grant itself permission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Protocol, runtime_checkable
import time


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PermissionTier(str, Enum):
    SAFE = "SAFE"
    CONFIRM = "CONFIRM"
    BLOCKED = "BLOCKED"


@dataclass
class ToolContext:
    session_id: str
    user_id: str = "default_user"
    correlation_id: str = ""
    is_interactive: bool = True
    dry_run: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    verified: bool
    details: str = ""
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class ToolResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    observation: Optional[str] = None
    verification: Optional[VerificationResult] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Tool(Protocol):
    """
    Standard Tool Protocol for JARVIS V4.
    Decouples tool definition, schema, risk, permission tier, and execution.
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    risk: RiskLevel
    permission: PermissionTier

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        """Execute the tool action within the given context."""
        ...

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        """Verify the post-action state and effect."""
        ...
