"""
JARVIS V4 - Tool Router & Server-Side Permission Policy Engine
The model can request an action but cannot grant itself permission.
Flow: LLM request -> Tool schema validation -> Policy lookup -> User/session authorization -> Execution.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List, Optional, Tuple

from tools.base import Tool, ToolContext, ToolResult, VerificationResult, RiskLevel, PermissionTier
from tools.schemas import validate_tool_arguments
from security.audit import record_audit
from core.permissions import check_permission as check_v3_permission, PermissionLevel

logger = logging.getLogger("JARVIS.Orchestration.ToolRouter")


class LegacyToolAdapter:
    """Adapts existing V3 callable tools into the V4 Tool protocol."""

    def __init__(self, name: str, fn: Any, permission_tier: PermissionTier = PermissionTier.SAFE):
        self.name = name
        self.fn = fn
        self.description = f"V3 tool: {name}"
        self.input_schema = {"type": "object", "properties": {}}
        self.risk = RiskLevel.LOW if permission_tier == PermissionTier.SAFE else RiskLevel.MEDIUM
        self.permission = permission_tier

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        try:
            # Call function with kwargs or dict
            import inspect
            sig = inspect.signature(self.fn) if callable(self.fn) else None
            
            if sig and len(sig.parameters) == 1 and list(sig.parameters.keys())[0] in ("params", "p", "payload", "kwargs"):
                res = self.fn(arguments)
            else:
                try:
                    res = self.fn(**arguments)
                except TypeError:
                    res = self.fn(arguments) if arguments else self.fn()

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=True,
                output=res,
                observation=str(res),
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=round(elapsed_ms, 2)
            )

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        return VerificationResult(verified=result.success, details="Legacy verification check")


class ToolRouter:
    """
    Authoritative Tool Router and Policy Enforcer.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._load_legacy_tools()
        # Register authoritative typed V4 tools
        from tools.v4_tools import WebSearchTool, SystemRestartTool
        from tools.controlled_tools import (
            SystemTelemetryTool,
            OpenApplicationTool,
            SetVolumeTool,
            ReadNoteTool,
            ProposeNoteUpdateTool,
            LookTool,
            WatchTool
        )
        self.register_tool(WebSearchTool())
        self.register_tool(SystemRestartTool())
        self.register_tool(SystemTelemetryTool())
        self.register_tool(OpenApplicationTool())
        self.register_tool(SetVolumeTool())
        self.register_tool(ReadNoteTool())
        self.register_tool(ProposeNoteUpdateTool())
        self.register_tool(LookTool())
        self.register_tool(WatchTool())

    def register_tool(self, tool: Tool) -> None:
        """Register a typed V4 tool."""
        self._tools[tool.name] = tool
        logger.info(f"[ToolRouter] Registered typed tool: {tool.name} (Tier: {tool.permission})")

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def _load_legacy_tools(self) -> None:
        """Loads and adapts existing V3 tools from ToolExecutor."""
        from core.executor import ToolExecutor
        executor = ToolExecutor()
        for name, fn in executor.tools.items():
            # Lookup permission tier from existing permissions
            perm_level, _ = check_v3_permission(name, {})
            tier = PermissionTier.SAFE
            if perm_level == PermissionLevel.CONFIRM:
                tier = PermissionTier.CONFIRM
            elif perm_level == PermissionLevel.BLOCKED:
                tier = PermissionTier.BLOCKED

            adapter = LegacyToolAdapter(name, fn, permission_tier=tier)
            self._tools[name] = adapter

    def check_permission(self, tool_name: str, context: ToolContext, arguments: Dict[str, Any]) -> Tuple[PermissionTier, str]:
        """
        Authoritative permission check.
        Returns (PermissionTier, reason).
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return PermissionTier.BLOCKED, f"Tool '{tool_name}' not recognized."

        # 1. BLOCKED policy check
        if tool.permission == PermissionTier.BLOCKED:
            record_audit("PERMISSION", tool_name, "BLOCKED", actor=context.user_id, correlation_id=context.correlation_id)
            return PermissionTier.BLOCKED, f"Operation '{tool_name}' is blocked by security policy."

        # 2. CONFIRM policy check
        if tool.permission == PermissionTier.CONFIRM:
            record_audit("PERMISSION", tool_name, "CONFIRM_REQUIRED", actor=context.user_id, correlation_id=context.correlation_id)
            return PermissionTier.CONFIRM, f"Action '{tool_name}' requires explicit user authorization."

        # 3. SAFE tier
        record_audit("PERMISSION", tool_name, "SAFE_ALLOWED", actor=context.user_id, correlation_id=context.correlation_id)
        return PermissionTier.SAFE, "Action authorized."

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any], context: ToolContext) -> ToolResult:
        """
        Validates schema, checks permissions, executes, verifies, and records audit.
        """
        from core.tracing import record_trace_span
        from core.errors import record_error, ErrorCategory

        tool = self.get_tool(tool_name)
        if not tool:
            record_error(ErrorCategory.TOOL_VALIDATION_ERROR, f"Unknown tool: {tool_name}", correlation_id=context.correlation_id, subsystem="tools")
            return ToolResult(success=False, error=f"Unknown tool: '{tool_name}'")

        # 1. Schema validation
        valid, errors = validate_tool_arguments(tool.input_schema, arguments)
        if not valid:
            err_text = "; ".join(errors)
            record_audit("TOOL_VALIDATION", tool_name, "FAILED", actor=context.user_id, details={"errors": errors}, correlation_id=context.correlation_id)
            record_error(ErrorCategory.TOOL_VALIDATION_ERROR, err_text, correlation_id=context.correlation_id, subsystem="tools")
            record_trace_span(context.correlation_id, f"tool_validation:{tool_name}", status="FAILED")
            return ToolResult(success=False, error=f"Invalid arguments for {tool_name}: {err_text}")

        # 2. Server-side permission check
        tier, reason = self.check_permission(tool_name, context, arguments)
        if tier == PermissionTier.BLOCKED:
            record_error(ErrorCategory.AUTHORIZATION_ERROR, reason, correlation_id=context.correlation_id, subsystem="security")
            record_trace_span(context.correlation_id, f"permission_checked:{tool_name}", status="BLOCKED")
            return ToolResult(success=False, error=f"Permission Denied: {reason}")
        if tier == PermissionTier.CONFIRM and not context.metadata.get("is_confirmed", False):
            record_trace_span(context.correlation_id, f"permission_checked:{tool_name}", status="REQUIRES_CONFIRMATION")
            return ToolResult(success=False, error=f"Confirmation Required: {reason}", metadata={"requires_confirmation": True, "tool": tool_name, "arguments": arguments})

        record_trace_span(context.correlation_id, f"permission_checked:{tool_name}", status="OK")

        # 3. Execution
        try:
            res = await tool.execute(context, arguments)
            # 4. Verification
            verification = await tool.verify(context, res)
            res.verification = verification

            record_trace_span(
                context.correlation_id,
                f"tool_executed:{tool_name}",
                status="OK" if res.success else "FAILED",
                duration_ms=res.execution_time_ms
            )
            record_trace_span(
                context.correlation_id,
                f"tool_verified:{tool_name}",
                status="OK" if verification.verified else "FAILED"
            )

            record_audit(
                "TOOL_EXECUTION",
                tool_name,
                "SUCCESS" if res.success else "FAILED",
                actor=context.user_id,
                details={"success": res.success, "execution_time_ms": res.execution_time_ms},
                correlation_id=context.correlation_id
            )
            return res
        except Exception as e:
            record_error(ErrorCategory.TOOL_EXECUTION_ERROR, str(e), correlation_id=context.correlation_id, subsystem="tools")
            record_audit("TOOL_EXECUTION", tool_name, "EXCEPTION", actor=context.user_id, details={"error": str(e)}, correlation_id=context.correlation_id)
            record_trace_span(context.correlation_id, f"tool_executed:{tool_name}", status="FAILED")
            return ToolResult(success=False, error=f"Execution error in {tool_name}: {e}")


_tool_router: Optional[ToolRouter] = None


def get_tool_router() -> ToolRouter:
    global _tool_router
    if _tool_router is None:
        _tool_router = ToolRouter()
    return _tool_router
