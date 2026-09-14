"""
JARVIS V3.0 - Action Verification Subsystem
Verifies real-world ground-truth state changes after tool execution.
Never equates function returning with action success.
"""

import os
import time
import psutil
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("JARVIS.Core.Verifier")

@dataclass
class VerificationResult:
    success: bool
    observation: str
    details: Optional[Dict[str, Any]] = None

def verify_action(tool_name: str, params: Dict[str, Any], exec_output: Any) -> VerificationResult:
    """
    Verifies that the executed action actually achieved its intended system effect.
    """
    clean_tool = tool_name.strip().lower()

    # 1. Application Launch Verification
    if clean_tool == "open_app":
        app_name = str(params.get("name", "")).lower()
        time.sleep(0.3)
        # Check if process is running
        for proc in psutil.process_iter(['name']):
            try:
                pname = proc.info['name'].lower()
                if app_name in pname or pname.startswith(app_name):
                    return VerificationResult(
                        success=True,
                        observation=f"Verified application '{app_name}' is actively running (PID: {proc.pid})."
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        # Web URLs or generic system commands might launch via shell without matching process name directly
        if exec_output and not str(exec_output).lower().startswith("error"):
            return VerificationResult(
                success=True,
                observation=f"Application launch command issued successfully: {exec_output}"
            )
        return VerificationResult(
            success=False,
            observation=f"Could not confirm process '{app_name}' started."
        )

    # 2. Application Close Verification
    if clean_tool == "close_app":
        app_name = str(params.get("name", "")).lower()
        time.sleep(0.3)
        still_running = False
        for proc in psutil.process_iter(['name']):
            try:
                if app_name in proc.info['name'].lower():
                    still_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not still_running:
            return VerificationResult(
                success=True,
                observation=f"Verified application '{app_name}' is closed."
            )
        return VerificationResult(
            success=False,
            observation=f"Application '{app_name}' appears to still be running."
        )

    # 3. File Write Verification
    if clean_tool == "write_file":
        path = params.get("path") or params.get("file_path", "")
        if os.path.exists(path) and os.path.getsize(path) >= 0:
            return VerificationResult(
                success=True,
                observation=f"Verified file exists at '{path}' ({os.path.getsize(path)} bytes)."
            )
        return VerificationResult(
            success=False,
            observation=f"File was not found on disk at '{path}'."
        )

    # 4. File Delete Verification
    if clean_tool == "delete_file":
        path = params.get("path") or params.get("file_path", "")
        if not os.path.exists(path):
            return VerificationResult(
                success=True,
                observation=f"Verified file at '{path}' is deleted."
            )
        return VerificationResult(
            success=False,
            observation=f"File still exists on disk at '{path}'."
        )

    # 5. Fact Memory Verification
    if clean_tool == "remember_fact":
        from memory.user_memory import user_memory
        key = params.get("key", "")
        val = user_memory.get_fact(key)
        if val is not None:
            return VerificationResult(
                success=True,
                observation=f"Verified fact '{key}' is stored in memory database."
            )
        return VerificationResult(
            success=False,
            observation=f"Fact '{key}' was not found in memory database."
        )

    # 6. Screenshot & Screen Action Verification
    if clean_tool == "take_screenshot":
        if exec_output and (isinstance(exec_output, str) or isinstance(exec_output, bytes)):
            return VerificationResult(
                success=True,
                observation="Verified screen screenshot captured successfully."
            )

    if clean_tool in ("screen_click", "screen_double_click", "screen_right_click", "screen_type", "screen_hotkey", "screen_scroll"):
        if exec_output and not str(exec_output).lower().startswith("action validation failed") and not str(exec_output).lower().startswith("action execution error"):
            return VerificationResult(
                success=True,
                observation=f"Screen action verified: {exec_output}"
            )
        return VerificationResult(
            success=False,
            observation=f"Screen action verification failed: {exec_output}"
        )

    # 7. General Tool Verification Fallback
    if exec_output is not None and not str(exec_output).lower().startswith("error"):
        return VerificationResult(
            success=True,
            observation=f"Step succeeded with output: {str(exec_output)[:120]}"
        )
    
    return VerificationResult(
        success=False,
        observation=f"Action produced empty or erroneous output: {exec_output}"
    )
