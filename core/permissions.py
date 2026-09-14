"""
JARVIS V3.0 - Security Permissions Subsystem
Authoritative, Python-enforced permission tiers (SAFE, CONFIRM, BLOCKED).
LLM output CANNOT override or elevate these permissions.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Tuple
import config

class PermissionLevel(Enum):
    SAFE = "SAFE"
    CONFIRM = "CONFIRM"
    BLOCKED = "BLOCKED"

# Ground-truth tool permission catalog
TOOL_PERMISSIONS: Dict[str, PermissionLevel] = {
    # System & Computer
    "volume_up": PermissionLevel.SAFE,
    "volume_down": PermissionLevel.SAFE,
    "volume_set": PermissionLevel.SAFE,
    "volume_mute": PermissionLevel.SAFE,
    "set_volume": PermissionLevel.SAFE,
    "control_media": PermissionLevel.SAFE,
    "control_window": PermissionLevel.SAFE,
    "take_screenshot": PermissionLevel.SAFE,
    "lock_screen": PermissionLevel.SAFE,
    "get_time": PermissionLevel.SAFE,
    "get_date": PermissionLevel.SAFE,
    "get_weather": PermissionLevel.SAFE,
    "get_news": PermissionLevel.SAFE,
    "get_system_stats": PermissionLevel.SAFE,
    
    # Applications
    "open_app": PermissionLevel.SAFE,
    "close_app": PermissionLevel.CONFIRM,
    
    # Browser & Web
    "search_web": PermissionLevel.SAFE,
    "search_google": PermissionLevel.SAFE,
    "play_youtube": PermissionLevel.SAFE,
    "web_search": PermissionLevel.SAFE,
    "scrape_url": PermissionLevel.SAFE,
    
    # Vision & Gestures
    "analyze_screen": PermissionLevel.SAFE,
    "analyze_camera": PermissionLevel.SAFE,
    "look": PermissionLevel.SAFE,
    "watch": PermissionLevel.SAFE,
    "gesture_mouse_start": PermissionLevel.SAFE,
    "gesture_mouse_stop": PermissionLevel.SAFE,

    # Screen-Aware Computer Actions (Bound to display geometry)
    "screen_click": PermissionLevel.SAFE,
    "screen_double_click": PermissionLevel.SAFE,
    "screen_right_click": PermissionLevel.SAFE,
    "screen_type": PermissionLevel.SAFE,
    "screen_hotkey": PermissionLevel.SAFE,
    "screen_scroll": PermissionLevel.SAFE,
    "screen_wait": PermissionLevel.SAFE,
    "find_and_click_element": PermissionLevel.SAFE,
    
    # Memory
    "remember_fact": PermissionLevel.SAFE,
    "retrieve_fact": PermissionLevel.SAFE,
    "forget_fact": PermissionLevel.SAFE,
    
    # Files (Guarded by path validation)
    "list_directory": PermissionLevel.SAFE,
    "read_file": PermissionLevel.SAFE,
    "write_file": PermissionLevel.CONFIRM,
    "delete_file": PermissionLevel.CONFIRM,

    # Office & Document Generation
    "create_presentation": PermissionLevel.SAFE,
    "create_spreadsheet": PermissionLevel.SAFE,
    "create_word_document": PermissionLevel.SAFE,
    "create_pdf_document": PermissionLevel.SAFE,
    "build_website": PermissionLevel.SAFE,

    # Computer & Environment Settings
    "set_brightness": PermissionLevel.SAFE,
    "toggle_dark_mode": PermissionLevel.SAFE,
    "toggle_wifi": PermissionLevel.CONFIRM,
    "toggle_bluetooth": PermissionLevel.CONFIRM,
    "get_system_settings": PermissionLevel.SAFE,

    # Advanced File Processor
    "organize_directory": PermissionLevel.CONFIRM,
    "find_large_files": PermissionLevel.SAFE,
    "clean_temp_files": PermissionLevel.CONFIRM,
    "compress_files": PermissionLevel.SAFE,
    "extract_archive": PermissionLevel.CONFIRM,

    # Media & Content
    "spotify_control": PermissionLevel.SAFE,
    "get_youtube_transcript_and_summary": PermissionLevel.SAFE,

    # Productivity & Daily Workflow
    "set_reminder": PermissionLevel.SAFE,
    "get_active_reminders": PermissionLevel.SAFE,
    "cancel_reminder": PermissionLevel.SAFE,
    "daily_briefing": PermissionLevel.SAFE,
    "analyze_clipboard": PermissionLevel.SAFE,

    # Social & Messaging
    "send_whatsapp_message": PermissionLevel.SAFE,
    "check_instagram_dms": PermissionLevel.SAFE,
    "reply_instagram_dm": PermissionLevel.CONFIRM,

    # Fitness & Health Vision
    "analyze_meal_nutrition": PermissionLevel.SAFE,
    "count_exercise_reps": PermissionLevel.SAFE,

    # Smart Home IoT
    "discover_smart_devices": PermissionLevel.SAFE,
    "control_smart_plug": PermissionLevel.SAFE,
    "control_smart_bulb": PermissionLevel.SAFE,

    # Developer Automation
    "git_quick_status": PermissionLevel.SAFE,
    "explain_code_snippet": PermissionLevel.SAFE,

    # Mobile Pairing & Remote Access
    "pair_mobile": PermissionLevel.SAFE,
    "list_paired_devices": PermissionLevel.SAFE,
    "revoke_mobile_device": PermissionLevel.CONFIRM,
    "unlock_phone": PermissionLevel.SAFE,
    "lock_phone": PermissionLevel.SAFE,
    "setup_wireless_phone": PermissionLevel.SAFE,
    "connect_wireless_phone": PermissionLevel.SAFE,
    "open_phone_app": PermissionLevel.SAFE,
    "play_phone_youtube": PermissionLevel.SAFE,
    "send_phone_whatsapp": PermissionLevel.SAFE,

    # Smart TV Control
    "discover_smart_tvs": PermissionLevel.SAFE,
    "connect_tv": PermissionLevel.SAFE,
    "tv_remote_control": PermissionLevel.SAFE,
    "tv_launch_app": PermissionLevel.SAFE,
    "tv_play_media": PermissionLevel.SAFE,
    "tv_input_text": PermissionLevel.SAFE,

    # Autonomous Background Monitors
    "monitor_crypto_price": PermissionLevel.SAFE,
    "monitor_website_uptime": PermissionLevel.SAFE,
    "monitor_system_resources": PermissionLevel.SAFE,
    "list_background_monitors": PermissionLevel.SAFE,
    "cancel_background_monitor": PermissionLevel.SAFE,

    # Meeting Assistant
    "start_meeting_recording": PermissionLevel.SAFE,
    "stop_meeting_recording": PermissionLevel.SAFE,

    # Advanced Media Downloads
    "download_youtube_audio": PermissionLevel.SAFE,
    "download_youtube_video": PermissionLevel.SAFE,

    # Window Management & Snapping
    "tile_window_left": PermissionLevel.SAFE,
    "tile_window_right": PermissionLevel.SAFE,
    "minimize_all_windows": PermissionLevel.SAFE,
    "snap_window": PermissionLevel.SAFE,

    # Advanced Browser Automation
    "browser_navigate": PermissionLevel.SAFE,
    "browser_click_element": PermissionLevel.SAFE,
    "browser_type_text": PermissionLevel.SAFE,
    "browser_capture_page": PermissionLevel.SAFE,
    "browser_extract_text": PermissionLevel.SAFE,
    
    # Obsidian Markdown Memory Vault
    "read_memory_vault": PermissionLevel.SAFE,
    "write_memory_vault_note": PermissionLevel.SAFE,
    "sync_memory_vault": PermissionLevel.SAFE,
    "open_obsidian_vault": PermissionLevel.SAFE,
    "get_active_priorities": PermissionLevel.SAFE,
    "update_active_priorities": PermissionLevel.SAFE,
    "log_daily_note": PermissionLevel.SAFE,
    "capture_inbox_item": PermissionLevel.SAFE,
    "read_project_context": PermissionLevel.SAFE,
    "set_hologram_theme": PermissionLevel.SAFE,

    # LEO Native Tools
    "open_application": PermissionLevel.SAFE,
    "manage_obsidian_note": PermissionLevel.SAFE,
    "get_system_telemetry": PermissionLevel.SAFE,

    # Push-to-Talk Voice Engine
    "start_push_to_talk": PermissionLevel.SAFE,
    "stop_push_to_talk": PermissionLevel.SAFE,
    
    # Dangerous Operations (Permanently Blocked or strictly confirmed)
    "run_shell_cmd": PermissionLevel.BLOCKED,
    "format_disk": PermissionLevel.BLOCKED,
    "modify_system_registry": PermissionLevel.BLOCKED,
}

SENSITIVE_FILENAMES = {
    "config.json",
    "config.py",
    "credentials.json",
    "secrets.json",
    ".phone_config.json",
    ".tv_config.json",
    "jarvis_memory.db",
    "jarvis_memory.db.v3_backup",
    "backtalk.json",
    "discord_bot.json",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "id_dsa",
    ".env",
}

SENSITIVE_EXTENSIONS = (
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".crt",
    ".token",
)

SENSITIVE_DIR_NAMES = {
    ".git",
    ".vscode",
    "__pycache__",
}

def is_sensitive_path(file_path: str) -> bool:
    """
    Authoritative guard against reading, modifying, or exfiltrating sensitive credentials,
    configuration files, private keys, certificates, database files, and repository metadata.
    """
    if not file_path or not isinstance(file_path, str):
        return True

    # Normalize path separators
    norm = file_path.replace("\\", "/").strip().lower()

    # Block directory traversal attempts
    if ".." in norm:
        return True

    try:
        resolved = Path(file_path).resolve()
    except Exception:
        return True

    name = resolved.name.lower()

    # 1. Check exact sensitive filenames
    if name in SENSITIVE_FILENAMES:
        return True

    # 2. Check sensitive extensions
    if any(name.endswith(ext) for ext in SENSITIVE_EXTENSIONS):
        return True

    # 3. Check environment file prefixes or SSH key prefixes
    if name.startswith(".env") or name.startswith("id_rsa") or name.startswith("id_ed25519"):
        return True

    # 4. Check token/auth files
    if ("token" in name or "auth" in name) and (name.endswith(".json") or name.endswith(".txt") or name.endswith(".yaml") or name.endswith(".yml")):
        return True

    # 5. Check secrets in name
    if "secret" in name and (name.endswith(".json") or name.endswith(".txt") or name.endswith(".yaml") or name.endswith(".yml") or name.endswith(".env")):
        return True

    # 6. Check sensitive directories (.git, .vscode, __pycache__)
    for part in resolved.parts:
        part_lower = part.lower()
        if part_lower in SENSITIVE_DIR_NAMES:
            return True
        if part_lower.startswith(".git") or part_lower == ".vscode":
            return True

    return False

def is_path_safe(file_path: str) -> bool:
    """Verifies that the target path does not escape sandbox, traverse maliciously, or use UNC/device escapes, and is not sensitive."""
    if not file_path or not isinstance(file_path, str):
        return False

    # Block sensitive paths immediately
    if is_sensitive_path(file_path):
        return False

    # Detect directory traversal
    if ".." in file_path:
        return False

    # Block Windows UNC network paths and device namespaces
    clean_p = file_path.replace("/", "\\").strip()
    if clean_p.startswith("\\\\") or clean_p.startswith("//"):
        return False
    if clean_p.startswith("\\\\?\\") or clean_p.startswith("\\\\.\\"):
        return False

    try:
        resolved = Path(file_path).resolve()
    except Exception:
        return False

    if is_sensitive_path(str(resolved)):
        return False

    # Check against safe directories
    safe_roots = [Path(p).resolve() for p in getattr(config, "SAFE_PATHS", [])]
    for root in safe_roots:
        try:
            if resolved == root or root in resolved.parents:
                return True
        except Exception:
            continue

    return False

def check_permission(tool_name: str, params: Dict[str, Any]) -> Tuple[PermissionLevel, str]:
    """
    Evaluates ground-truth permission for a given tool and its parameters.
    Returns (PermissionLevel, reason_string).
    """
    clean_tool = tool_name.strip().lower()
    base_level = TOOL_PERMISSIONS.get(clean_tool, PermissionLevel.BLOCKED)

    # If tool is unknown, block it by default
    if clean_tool not in TOOL_PERMISSIONS:
        return PermissionLevel.BLOCKED, f"Tool '{tool_name}' is not recognized in security catalog."

    # Validate coordinate bounds for screen click actions
    if clean_tool in ("screen_click", "screen_double_click", "screen_right_click"):
        if "x" in params and "y" in params:
            from core.action_schema import validate_computer_action
            val = validate_computer_action("click", params)
            if not val.is_valid:
                return PermissionLevel.BLOCKED, f"Screen action blocked: {val.error}"

    # Inspect file operations for path escape / safety / sensitive secrets
    if clean_tool in ("read_file", "write_file", "delete_file", "list_directory"):
        target_path = params.get("path") or params.get("file_path") or params.get("target") or ""
        if target_path:
            if is_sensitive_path(target_path) or not is_path_safe(target_path):
                return PermissionLevel.BLOCKED, "Access blocked: I'm afraid I cannot access that file, sir."

    # Shell commands or raw modifications are strictly blocked
    if base_level == PermissionLevel.BLOCKED:
        return PermissionLevel.BLOCKED, f"Tool '{tool_name}' is permanently blocked by security policy."

    return base_level, "Allowed under policy"
