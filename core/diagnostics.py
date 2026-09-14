"""
JARVIS V4 - Subsystem Health & Truthful Diagnostics Engine
Distinguishes:
 - Component Existence vs. Initialization vs. Current Availability vs. Operational State.
Exposes safe operational telemetry without leaking secrets, tokens, or private data.
"""

from __future__ import annotations

import os
import sys
import time
import secrets
import logging
from typing import Dict, Any, Optional

from core.errors import get_error_tracker, get_last_error
from core.tracing import get_trace_manager, get_recent_traces

logger = logging.getLogger("JARVIS.Core.Diagnostics")

# Server instance identity to detect stale server processes
SERVER_START_TIME = time.time()
INSTANCE_ID = f"inst_{secrets.token_hex(4)}"

def get_server_diagnostics() -> Dict[str, Any]:
    current_state = "IDLE"
    try:
        from communication.broadcaster import get_broadcaster
        broadcaster = get_broadcaster()
        current_state = getattr(broadcaster, "_current_state", "IDLE")
    except Exception:
        pass

    return {
        "status": "ok",
        "version": "4.0",
        "instance_id": INSTANCE_ID,
        "pid": os.getpid(),
        "uptime_seconds": round(time.time() - SERVER_START_TIME, 1),
        "current_state": current_state
    }

def get_ai_diagnostics() -> Dict[str, Any]:
    try:
        import config
        from ai.provider import get_ai_provider
        provider_name = getattr(config, "AI_PROVIDER", "gemini")
        provider = get_ai_provider(provider_name)
        is_avail = provider.is_available() if provider else False
        configured_model = getattr(config, "DEFAULT_MODEL", "gemini-3.6-flash")

        return {
            "initialized": True,
            "provider": provider.name if provider else provider_name,
            "configured_model": configured_model,
            "available": is_avail,
            "last_error": get_last_error("ai")
        }
    except Exception as e:
        return {
            "initialized": False,
            "available": False,
            "error": str(e)
        }

def get_memory_diagnostics() -> Dict[str, Any]:
    try:
        import config
        from memory.database import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) as cnt FROM user_facts")
            row = cursor.fetchone()
            facts_count = row["cnt"] if row else 0

        vault_ok = False
        try:
            vault_path = getattr(config, "VAULT_DIR", None)
            vault_ok = bool(vault_path and os.path.exists(str(vault_path)))
        except Exception:
            pass

        return {
            "initialized": True,
            "database_connected": True,
            "facts_count": facts_count,
            "vault_directory_available": vault_ok,
            "last_error": get_last_error("memory")
        }
    except Exception as e:
        return {
            "initialized": True,
            "database_connected": False,
            "error": str(e)
        }

def get_voice_diagnostics() -> Dict[str, Any]:
    pyaudio_ok = False
    try:
        import pyaudio
        pyaudio_ok = True
    except ImportError:
        pass

    ptt_active = False
    try:
        from voice.ptt_engine import get_ptt_engine
        engine = get_ptt_engine()
        ptt_active = bool(engine and hasattr(engine, "is_recording"))
    except Exception:
        pass

    edge_tts_ok = False
    try:
        import edge_tts
        edge_tts_ok = True
    except ImportError:
        pass

    pynput_ok = False
    try:
        from voice.ptt_engine import PYNPUT_AVAILABLE
        pynput_ok = PYNPUT_AVAILABLE
    except Exception:
        pass

    windows_ptt_ok = sys.platform == "win32"

    return {
        "initialized": True,
        "pyaudio_available": pyaudio_ok,
        "tts_engine_available": edge_tts_ok,
        "push_to_talk_initialized": ptt_active,
        "optional_pynput_available": pynput_ok,
        "windows_native_ptt_available": windows_ptt_ok,
        "push_to_talk_mode": "pynput_hook" if pynput_ok else ("windows_native_async" if windows_ptt_ok else "ui_only"),
        "last_error": get_last_error("voice")
    }

_vision_cache = {"time": 0.0, "result": None}

def get_vision_diagnostics() -> Dict[str, Any]:
    global _vision_cache
    now = time.time()
    if _vision_cache["result"] is not None and (now - _vision_cache["time"]) < 15.0:
        return _vision_cache["result"]

    screen_ok = False
    try:
        from vision.screen import capture_screen_bytes
        bytes_out = capture_screen_bytes()
        screen_ok = bool(bytes_out and len(bytes_out) > 100)
    except Exception:
        pass

    cam_avail = False
    try:
        from vision.camera import is_camera_available
        cam_avail = is_camera_available(0)
    except Exception:
        pass

    res = {
        "initialized": True,
        "screen_capture_available": screen_ok,
        "camera_available": cam_avail,
        "last_error": get_last_error("vision")
    }
    _vision_cache = {"time": now, "result": res}
    return res

def get_executor_diagnostics() -> Dict[str, Any]:
    try:
        from orchestration.tool_router import get_tool_router
        router = get_tool_router()
        tool_count = len(router.list_tools()) if router else 0
        return {
            "initialized": True,
            "registered_tools_count": tool_count,
            "permission_enforcement": "authoritative_python_grounded",
            "last_error": get_last_error("tools")
        }
    except Exception as e:
        return {
            "initialized": False,
            "error": str(e)
        }

def get_websocket_diagnostics() -> Dict[str, Any]:
    try:
        from communication.broadcaster import get_broadcaster
        broadcaster = get_broadcaster()
        async_count = len(getattr(broadcaster, "_async_subscribers", []))
        sync_count = len(getattr(broadcaster, "_subscribers", []))
        return {
            "broadcaster_active": True,
            "active_clients": async_count + sync_count,
            "current_theme": getattr(broadcaster, "_current_theme", "orange")
        }
    except Exception as e:
        return {
            "broadcaster_active": False,
            "error": str(e)
        }

def get_mobile_diagnostics() -> Dict[str, Any]:
    try:
        import database
        from core.mobile_bridge import _active_pairing_session
        paired = database.get_paired_devices()
        return {
            "paired_devices_count": len(paired) if paired else 0,
            "pairing_session_active": bool(_active_pairing_session.get("pin")),
            "last_error": get_last_error("mobile")
        }
    except Exception as e:
        return {
            "paired_devices_count": 0,
            "error": str(e)
        }

def get_diagnostics_report() -> Dict[str, Any]:
    """
    Compiles the authoritative, truthful system diagnostics snapshot across all subsystems.
    Zero secrets, API keys, tokens, or private contents are exposed.
    """
    return {
        "status": "ok",
        "server": get_server_diagnostics(),
        "ai": get_ai_diagnostics(),
        "memory": get_memory_diagnostics(),
        "voice": get_voice_diagnostics(),
        "vision": get_vision_diagnostics(),
        "executor": get_executor_diagnostics(),
        "websocket": get_websocket_diagnostics(),
        "mobile": get_mobile_diagnostics(),
        "recent_errors": get_error_tracker().get_recent_errors(limit=5),
        "recent_traces": get_trace_manager().get_recent_traces(limit=5),
    }