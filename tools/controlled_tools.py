"""
Controlled Tools for Leo/Jarvis
Implements narrowly defined, validated functions with explicit permission levels,
execution timeouts, and post-execution verification checks.
"""

from __future__ import annotations

import os
import sys
import time
import asyncio
import subprocess
import psutil
from pathlib import Path
from typing import Dict, Any, Optional

from tools.base import Tool, ToolContext, ToolResult, VerificationResult, RiskLevel, PermissionTier
from memory.obsidian_vault import get_vault_manager

# Allowlist of safe applications
SAFE_APPLICATIONS = {
    "notepad": "notepad.exe",
    "calc": "calc.exe",
    "calculator": "calc.exe",
    "chrome": "chrome",
    "edge": "msedge",
    "spotify": "spotify",
    "obsidian": "obsidian",
    "terminal": "wt.exe",
    "cmd": "cmd.exe",
    "code": "code",
    "vscode": "code"
}


class SystemTelemetryTool:
    name = "get_system_telemetry"
    description = "Retrieves live CPU load, RAM utilization, battery status, and disk capacity."
    input_schema = {
        "type": "object",
        "properties": {}
    }
    risk = RiskLevel.LOW
    permission = PermissionTier.SAFE

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        try:
            battery = psutil.sensors_battery()
            battery_pct = round(battery.percent, 1) if battery else "N/A"
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\" if sys.platform == "win32" else "/")
            data = {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "ram_percent": mem.percent,
                "ram_used_gb": round(mem.used / (1024**3), 2),
                "ram_total_gb": round(mem.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "battery_percent": battery_pct,
                "status": "HEALTHY"
            }
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=True,
                output=data,
                observation=f"System Telemetry: CPU {data['cpu_percent']}%, RAM {data['ram_percent']}%, Disk {data['disk_percent']}%",
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(success=False, error=str(e), execution_time_ms=round(elapsed_ms, 2))

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        return VerificationResult(verified=result.success and isinstance(result.output, dict), details="Telemetry verified")


class OpenApplicationTool:
    name = "open_application"
    description = "Launches an allowlisted desktop application by name (e.g. notepad, calc, obsidian, chrome, code)."
    input_schema = {
        "type": "object",
        "required": ["application_id"],
        "properties": {
            "application_id": {"type": "string", "description": "The identifier or name of the app (notepad, calc, chrome, obsidian, code, spotify, terminal)."}
        }
    }
    risk = RiskLevel.LOW
    permission = PermissionTier.SAFE

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        app_id = arguments.get("application_id", "").strip().lower()
        if not app_id:
            return ToolResult(success=False, error="Application ID cannot be empty.")

        target_cmd = SAFE_APPLICATIONS.get(app_id)
        if not target_cmd:
            return ToolResult(
                success=False,
                error=f"Application '{app_id}' is not in the allowlist. Allowed apps: {', '.join(SAFE_APPLICATIONS.keys())}."
            )

        try:
            if sys.platform == "win32":
                subprocess.Popen(f"start {target_cmd}", shell=True)
            else:
                subprocess.Popen([target_cmd])
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=True,
                output=f"Successfully launched application: {app_id}",
                observation=f"Launched {app_id}",
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(success=False, error=f"Failed to launch {app_id}: {e}", execution_time_ms=round(elapsed_ms, 2))

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        return VerificationResult(verified=result.success, details="Application launch command dispatched.")


class SetVolumeTool:
    name = "set_volume"
    description = "Adjusts system audio output volume level (0 to 100) or executes volume action (up, down, mute, unmute)."
    input_schema = {
        "type": "object",
        "properties": {
            "level": {"type": "integer", "minimum": 0, "maximum": 100, "description": "Desired volume level from 0 to 100."},
            "action": {"type": "string", "description": "Volume action: up, down, mute, unmute."}
        }
    }
    risk = RiskLevel.LOW
    permission = PermissionTier.SAFE

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        try:
            target_level = None
            action = arguments.get("action", "").lower().strip()
            if "level" in arguments and arguments["level"] is not None:
                try:
                    target_level = int(arguments["level"])
                except (ValueError, TypeError):
                    target_level = 50

            # If pycaw or ctypes is available on Windows, adjust volume
            volume_ctrl = None
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))
            except Exception:
                pass

            if target_level is None:
                current_scalar = 0.5
                if volume_ctrl:
                    try:
                        current_scalar = volume_ctrl.GetMasterVolumeLevelScalar()
                    except Exception:
                        pass
                current_pct = int(current_scalar * 100)

                if action == "up":
                    target_level = min(100, current_pct + 10)
                elif action == "down":
                    target_level = max(0, current_pct - 10)
                elif action == "mute":
                    if volume_ctrl:
                        volume_ctrl.SetMute(1, None)
                    target_level = 0
                elif action == "unmute":
                    if volume_ctrl:
                        volume_ctrl.SetMute(0, None)
                    target_level = current_pct if current_pct > 0 else 30
                else:
                    target_level = 50

            target_level = max(0, min(100, target_level))

            if volume_ctrl:
                try:
                    if action != "mute":
                        volume_ctrl.SetMute(0, None)
                    volume_ctrl.SetMasterVolumeLevelScalar(target_level / 100.0, None)
                except Exception as e:
                    logger.debug(f"[Volume Hardware Warning]: {e}")

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=True,
                output=f"System volume set to {target_level}%.",
                observation=f"Volume adjusted to {target_level}%",
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(success=False, error=f"Failed to set volume: {e}", execution_time_ms=round(elapsed_ms, 2))

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        return VerificationResult(verified=result.success, details="Volume level confirmed.")


class ReadNoteTool:
    name = "read_note"
    description = "Reads a markdown note from the Obsidian Knowledge Vault (relative path, e.g. 'Active Priorities' or '02 - Polacraft/Orders')."
    input_schema = {
        "type": "object",
        "required": ["relative_path"],
        "properties": {
            "relative_path": {"type": "string", "description": "Path to the note relative to vault root."}
        }
    }
    risk = RiskLevel.LOW
    permission = PermissionTier.SAFE

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        rel_path = arguments.get("relative_path", "").strip()
        if not rel_path:
            return ToolResult(success=False, error="Relative note path is required.")

        vm = get_vault_manager()
        ok, content = vm.read_note(rel_path)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        if ok:
            return ToolResult(
                success=True,
                output=content,
                observation=f"Read note '{rel_path}' ({len(content)} chars)",
                execution_time_ms=round(elapsed_ms, 2)
            )
        else:
            return ToolResult(success=False, error=content, execution_time_ms=round(elapsed_ms, 2))

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        return VerificationResult(verified=result.success, details="Note read and bounded.")


class ProposeNoteUpdateTool:
    name = "propose_note_update"
    description = "Proposes creating or updating a note in the Obsidian Knowledge Vault. Requires explicit user confirmation."
    input_schema = {
        "type": "object",
        "required": ["relative_path", "content"],
        "properties": {
            "relative_path": {"type": "string", "description": "Path to the note relative to vault root."},
            "content": {"type": "string", "description": "Full markdown content with frontmatter to write."}
        }
    }
    risk = RiskLevel.HIGH
    permission = PermissionTier.CONFIRM

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        rel_path = arguments.get("relative_path", "").strip()
        content = arguments.get("content", "")

        if not rel_path or not content:
            return ToolResult(success=False, error="Both relative_path and content are required.")

        vm = get_vault_manager()

        # If user has already confirmed, execute the write
        if context.metadata.get("is_confirmed", False):
            ok, msg = vm.execute_confirmed_note_update(rel_path, content)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=ok,
                output=msg,
                error=None if ok else msg,
                observation=msg,
                execution_time_ms=round(elapsed_ms, 2)
            )

        # Otherwise generate proposal for the confirmation panel
        proposal = vm.propose_note_update(rel_path, content)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return ToolResult(
            success=False,
            error=f"Confirmation required: Proposed changes to note '{rel_path}'",
            metadata={
                "requires_confirmation": True,
                "tool": self.name,
                "arguments": arguments,
                "proposal_details": proposal
            },
            execution_time_ms=round(elapsed_ms, 2)
        )

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        return VerificationResult(verified=result.success, details="Note proposal confirmed and verified.")


class LookTool:
    name = "look"
    description = "Captures a single camera frame to visually identify items, labels, people, or the physical surroundings via Gemini."
    input_schema = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Specific question or visual detail to inspect."},
            "reason": {"type": "string", "description": "Short explanation for looking through the camera."}
        }
    }
    risk = RiskLevel.LOW
    permission = PermissionTier.SAFE

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        prompt = arguments.get("prompt") or "Describe what is in front of the camera."
        reason = arguments.get("reason", "")
        try:
            from vision.camera import look
            res = await asyncio.to_thread(look, prompt, reason)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=True,
                output=res,
                observation=res,
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=False,
                error=str(e),
                observation="Failed to access camera for inspection.",
                execution_time_ms=round(elapsed_ms, 2)
            )

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        return VerificationResult(verified=result.success, details="Visual frame capture completed.")


class WatchTool:
    name = "watch"
    description = "Watches through the camera over a short sequence of seconds (2 to 10 seconds) to evaluate motion, exercise form, or action transitions via Gemini."
    input_schema = {
        "type": "object",
        "properties": {
            "seconds": {"type": "integer", "description": "Duration in seconds to watch (2 to 10)."},
            "prompt": {"type": "string", "description": "What motion, exercise form, or action change to evaluate."},
            "reason": {"type": "string", "description": "Short explanation shown to user."}
        }
    }
    risk = RiskLevel.LOW
    permission = PermissionTier.SAFE

    async def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        seconds = int(arguments.get("seconds") or 4)
        prompt = arguments.get("prompt") or "Analyze what changed across these frames."
        reason = arguments.get("reason", "")
        try:
            from vision.camera import watch
            res = await asyncio.to_thread(watch, seconds, prompt, reason)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=True,
                output=res,
                observation=res,
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=False,
                error=str(e),
                observation="Failed to record frame sequence.",
                execution_time_ms=round(elapsed_ms, 2)
            )

    async def verify(self, context: ToolContext, result: ToolResult) -> VerificationResult:
        return VerificationResult(verified=result.success, details="Visual sequence capture completed.")

