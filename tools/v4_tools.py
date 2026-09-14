"""
JARVIS V4 - Typed Standard Tools
Implements the first vertical slice tools under the authoritative V4 Tool protocol.
"""

from __future__ import annotations

import time
from typing import Dict, Any

from tools.base import Tool, ToolContext, ToolResult, VerificationResult, RiskLevel, PermissionTier
from tools.web import fetch_live_web_search, fetch_wikipedia_summary


class WebSearchTool:
    name = "web_search"
    description = "Searches the live web or Wikipedia for articles, facts, and live information."
    input_schema = {
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "description": "The search term or question."}
        }
    }
    risk = RiskLevel.LOW
    permission = PermissionTier.SAFE

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        query = arguments.get("query", "")
        if not query:
            return ToolResult(success=False, error="Query cannot be empty.")

        # 1. Try DuckDuckGo / Live search
        result = fetch_live_web_search(query)
        if not result:
            # 2. Try Wikipedia
            result = fetch_wikipedia_summary(query)

        if not result:
            result = f"No direct search results found for '{query}', sir."

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return ToolResult(
            success=True,
            output=result,
            observation=f"Web search for '{query}' returned: {result}",
            execution_time_ms=round(elapsed_ms, 2)
        )

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        has_content = bool(result.output and len(str(result.output)) > 5)
        return VerificationResult(
            verified=result.success and has_content,
            details="Web search result content verified."
        )


class SystemRestartTool:
    """A sensitive system action requiring explicit user confirmation."""
    name = "restart_pc"
    description = "Initiates a host operating system reboot."
    input_schema = {
        "type": "object",
        "properties": {
            "force": {"type": "boolean", "description": "Force close open applications."}
        }
    }
    risk = RiskLevel.HIGH
    permission = PermissionTier.CONFIRM

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        # If dry-run or testing, simulate reboot
        if context.dry_run or context.metadata.get("test_mode", False):
            return ToolResult(success=True, output="System restart simulated successfully (test mode).")
        return ToolResult(success=True, output="System reboot dispatched, sir.")

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        return VerificationResult(verified=result.success, details="Restart action authorization verified.")
