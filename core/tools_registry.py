"""
=============================================================================
JARVIS Core: Centralized Tools Registry & Python-Enforced Permission Tiers
=============================================================================
Goal: Statically define all capability tools and their ground-truth permissions
      in Python so LLM JSON output cannot bypass security controls.

Permissions:
 - SAFE     : Executed immediately without user prompt
 - CONFIRM  : Requires explicit user confirmation
 - BLOCKED  : Permanently restricted / rejected

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

from tools import computer, browser, web
from vision import screen

TOOLS_REGISTRY = {
    "lock_screen": {
        "function": computer.lock_screen,
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Locks the Windows workstation"
    },
    "take_screenshot": {
        "function": computer.take_screenshot,
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Captures desktop screenshot"
    },
    "set_volume": {
        "function": lambda action="up": computer.control_volume(action),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Adjusts laptop master volume"
    },
    "control_media": {
        "function": lambda action="play": computer.control_media(action),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Controls media play/pause/skip"
    },
    "control_window": {
        "function": lambda action="minimize": computer.control_window(action),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Manages active window state"
    },
    "open_app": {
        "function": lambda target="chrome": computer.open_app(target),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Opens popular desktop apps or websites"
    },
    "play_youtube": {
        "function": lambda query="": browser.play_youtube_video(query),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Searches YouTube and auto-plays video via Selenium"
    },
    "search_google": {
        "function": lambda query="": browser.search_google_selenium(query),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Searches Google via Selenium"
    },
    "web_search": {
        "function": lambda query="": web.get_web_info(query),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Scrapes Google News RSS or Wikipedia via BeautifulSoup"
    },
    "analyze_screen": {
        "function": lambda prompt="Analyze screen": screen.analyze(prompt),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Captures and analyzes desktop screen using Gemini Vision"
    },
    "screen_click": {
        "function": lambda x=0, y=0: __import__("core.action_schema", fromlist=["execute_computer_action"]).execute_computer_action("click", {"x": x, "y": y})[1],
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Clicks mouse at verified screen coordinates (x, y)"
    },
    "screen_type": {
        "function": lambda text="": __import__("core.action_schema", fromlist=["execute_computer_action"]).execute_computer_action("type", {"text": text})[1],
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Types validated text string via clipboard injection"
    },
    "screen_hotkey": {
        "function": lambda keys=[]: __import__("core.action_schema", fromlist=["execute_computer_action"]).execute_computer_action("hotkey", {"keys": keys})[1],
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Triggers validated hotkey combination (e.g. ['ctrl', 'v'])"
    },
    "screen_scroll": {
        "function": lambda amount=300: __import__("core.action_schema", fromlist=["execute_computer_action"]).execute_computer_action("scroll", {"amount": amount})[1],
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Scrolls display vertically by amount"
    },
    "delete_file": {
        "function": lambda path="": f"Delete file {path}",
        "permission": "CONFIRM",
        "verify_fn": lambda: True,
        "description": "Deletes local files"
    },
    "create_presentation": {
        "function": lambda title="Presentation", slides=[]: __import__("tools.office", fromlist=["create_presentation"]).create_presentation(title, slides),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Generates a PowerPoint presentation"
    },
    "create_spreadsheet": {
        "function": lambda title="Workbook", sheets_data=[]: __import__("tools.office", fromlist=["create_spreadsheet"]).create_spreadsheet(title, sheets_data),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Generates an Excel spreadsheet"
    },
    "create_word_document": {
        "function": lambda title="Document", content=[]: __import__("tools.office", fromlist=["create_word_document"]).create_word_document(title, content),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Generates a Word document"
    },
    "create_pdf_document": {
        "function": lambda title="Document", content=[]: __import__("tools.office", fromlist=["create_pdf_document"]).create_pdf_document(title, content),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Generates a PDF document"
    },
    "build_website": {
        "function": lambda topic="Website", template_style="modern": __import__("tools.web_builder", fromlist=["build_website"]).build_website(topic, template_style),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Builds a complete responsive website"
    },
    "set_brightness": {
        "function": lambda level=70: __import__("tools.computer_settings", fromlist=["set_brightness"]).set_brightness(level),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Adjusts display brightness"
    },
    "toggle_dark_mode": {
        "function": lambda enabled=True: __import__("tools.computer_settings", fromlist=["toggle_dark_mode"]).toggle_dark_mode(enabled),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Toggles dark mode theme"
    },
    "toggle_wifi": {
        "function": lambda state="enable": __import__("tools.computer_settings", fromlist=["toggle_wifi"]).toggle_wifi(state),
        "permission": "CONFIRM",
        "verify_fn": lambda: True,
        "description": "Toggles Wi-Fi network interface"
    },
    "toggle_bluetooth": {
        "function": lambda state="enable": __import__("tools.computer_settings", fromlist=["toggle_bluetooth"]).toggle_bluetooth(state),
        "permission": "CONFIRM",
        "verify_fn": lambda: True,
        "description": "Toggles Bluetooth adapter"
    },
    "get_system_settings": {
        "function": lambda: __import__("tools.computer_settings", fromlist=["get_system_settings"]).get_system_settings(),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Gets current system display, theme, and battery settings"
    },
    "organize_directory": {
        "function": lambda path="~/Downloads": __import__("tools.file_processor", fromlist=["organize_directory"]).organize_directory(path),
        "permission": "CONFIRM",
        "verify_fn": lambda: True,
        "description": "Categorizes and organizes files in directory"
    },
    "find_large_files": {
        "function": lambda path="~", min_mb=100.0: __import__("tools.file_processor", fromlist=["find_large_files"]).find_large_files(path, min_mb),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Finds files larger than size threshold"
    },
    "clean_temp_files": {
        "function": lambda: __import__("tools.file_processor", fromlist=["clean_temp_files"]).clean_temp_files(),
        "permission": "CONFIRM",
        "verify_fn": lambda: True,
        "description": "Safely purges temp files"
    },
    "compress_files": {
        "function": lambda source_path=".", zip_name=None: __import__("tools.file_processor", fromlist=["compress_files"]).compress_files(source_path, zip_name),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Compresses files into ZIP archive"
    },
    "extract_archive": {
        "function": lambda zip_path="", target_dir=None: __import__("tools.file_processor", fromlist=["extract_archive"]).extract_archive(zip_path, target_dir),
        "permission": "CONFIRM",
        "verify_fn": lambda: True,
        "description": "Extracts ZIP archive"
    },
    "spotify_control": {
        "function": lambda action="play", query=None: __import__("tools.media_controller", fromlist=["spotify_control"]).spotify_control(action, query),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Controls Spotify playback or search"
    },
    "get_youtube_transcript_and_summary": {
        "function": lambda url="": __import__("tools.media_controller", fromlist=["get_youtube_transcript_and_summary"]).get_youtube_transcript_and_summary(url),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Retrieves transcript and summary of YouTube video"
    },
    "set_reminder": {
        "function": lambda message="", delay_minutes=10.0: __import__("tools.productivity", fromlist=["set_reminder"]).set_reminder(message, delay_minutes),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Sets a scheduled reminder"
    },
    "get_active_reminders": {
        "function": lambda: __import__("tools.productivity", fromlist=["get_active_reminders"]).get_active_reminders(),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Lists active reminders"
    },
    "cancel_reminder": {
        "function": lambda reminder_id="": __import__("tools.productivity", fromlist=["cancel_reminder"]).cancel_reminder(reminder_id),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Cancels scheduled reminder"
    },
    "daily_briefing": {
        "function": lambda: __import__("tools.productivity", fromlist=["daily_briefing"]).daily_briefing(),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Compiles morning daily briefing report"
    },
    "analyze_clipboard": {
        "function": lambda: __import__("tools.productivity", fromlist=["analyze_clipboard"]).analyze_clipboard(),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Inspects and classifies clipboard content"
    },
    "send_whatsapp_message": {
        "function": lambda recipient="", message="": __import__("tools.social", fromlist=["send_whatsapp_message"]).send_whatsapp_message(recipient, message),
        "permission": "CONFIRM",
        "verify_fn": lambda: True,
        "description": "Sends message via WhatsApp desktop"
    },
    "check_instagram_dms": {
        "function": lambda username=None, password=None: __import__("tools.social", fromlist=["check_instagram_dms"]).check_instagram_dms(username, password),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Checks recent Instagram DMs"
    },
    "reply_instagram_dm": {
        "function": lambda thread_id="", message="": __import__("tools.social", fromlist=["reply_instagram_dm"]).reply_instagram_dm(thread_id, message),
        "permission": "CONFIRM",
        "verify_fn": lambda: True,
        "description": "Replies to Instagram DM"
    },
    "analyze_meal_nutrition": {
        "function": lambda meal_info="": __import__("tools.fitness", fromlist=["analyze_meal_nutrition"]).analyze_meal_nutrition(meal_info),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Analyzes meal nutrition and calories"
    },
    "count_exercise_reps": {
        "function": lambda exercise_type="pushup", duration_seconds=30: __import__("tools.fitness", fromlist=["count_exercise_reps"]).count_exercise_reps(exercise_type, duration_seconds),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Tracks exercise repetitions via webcam"
    },
    "discover_smart_devices": {
        "function": lambda: __import__("tools.smart_home", fromlist=["discover_smart_devices"]).discover_smart_devices(),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Discovers local Wi-Fi smart devices"
    },
    "control_smart_plug": {
        "function": lambda device_alias="", state="on": __import__("tools.smart_home", fromlist=["control_smart_plug"]).control_smart_plug(device_alias, state),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Controls smart plug power state"
    },
    "control_smart_bulb": {
        "function": lambda device_alias="", state="on", brightness=None: __import__("tools.smart_home", fromlist=["control_smart_bulb"]).control_smart_bulb(device_alias, state, brightness),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Controls smart light bulb power and brightness"
    },
    "git_quick_status": {
        "function": lambda repo_path=None: __import__("tools.dev_tools", fromlist=["git_quick_status"]).git_quick_status(repo_path),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Inspects Git repository status"
    },
    "explain_code_snippet": {
        "function": lambda code="", language=None: __import__("tools.dev_tools", fromlist=["explain_code_snippet"]).explain_code_snippet(code, language),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Explains code snippet"
    },
    "pair_mobile": {
        "function": lambda: __import__("tools.pairing_manager", fromlist=["pair_mobile"]).pair_mobile(),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Generates PIN and QR code to pair mobile phone"
    },
    "list_paired_devices": {
        "function": lambda: __import__("tools.pairing_manager", fromlist=["list_paired_devices"]).list_paired_devices(),
        "permission": "SAFE",
        "verify_fn": lambda: True,
        "description": "Lists all registered paired mobile devices"
    },
    "revoke_mobile_device": {
        "function": lambda device_id="": __import__("tools.pairing_manager", fromlist=["revoke_mobile_device"]).revoke_mobile_device(device_id),
        "permission": "CONFIRM",
        "verify_fn": lambda: True,
        "description": "Revokes access for a paired mobile phone"
    },
    "modify_system": {
        "function": lambda cmd="": f"Modify system {cmd}",
        "permission": "CONFIRM",
        "verify_fn": lambda: True,
        "description": "Modifies system registry or configuration"
    },
    "run_shell_cmd": {
        "function": lambda cmd="": "Shell command blocked",
        "permission": "BLOCKED",
        "verify_fn": lambda: False,
        "description": "Executes raw shell command"
    }
}

def get_tool_meta(tool_name: str) -> dict:
    """Returns tool metadata dictionary including Python-enforced permission."""
    return TOOLS_REGISTRY.get(tool_name, {
        "function": None,
        "permission": "BLOCKED",
        "verify_fn": lambda: False,
        "description": "Unknown tool"
    })
