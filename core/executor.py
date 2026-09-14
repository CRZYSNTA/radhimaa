"""
JARVIS V3.0 - Core Tool Executor
Enforces strict Python-grounded permission security, runs post-execution verification,
and logs actions to SQLite memory.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, Callable, Optional, List
from enum import Enum

from core.permissions import check_permission, PermissionLevel
from core.verifier import verify_action, VerificationResult
from memory import log_action

logger = logging.getLogger("JARVIS.Core.Executor")

class Permission(Enum):
    SAFE = "SAFE"
    CONFIRM = "CONFIRM"
    BLOCKED = "BLOCKED"

class ExecutionResult:
    def __init__(self, success: bool, output: Any = None, error: str = None, observation: str = ""):
        self.success = success
        self.output = output
        self.error = error
        self.observation = observation
    
    def __repr__(self):
        if self.success:
            return f"ExecutionResult(success=True, output={self.output}, observation='{self.observation}')"
        return f"ExecutionResult(success=False, error='{self.error}')"

class ToolExecutor:
    def __init__(self, confirm_callback: Optional[Callable[[str], bool]] = None):
        self.tools: Dict[str, Callable] = {}
        self.confirm_callback = confirm_callback or self._default_confirm
        self._register_tools()

    def _default_confirm(self, message: str) -> bool:
        print(f"\n[CONFIRM REQUIRED] {message}")
        try:
            response = input("Proceed? (y/N): ").strip().lower()
            return response in ['y', 'yes']
        except Exception:
            return False

    def _register_tools(self):
        # Computer & System
        from tools.computer import (
            volume_up, volume_down, volume_set, volume_mute, control_volume,
            control_media, control_window,
            take_screenshot, lock_screen, open_app, close_app,
            get_time, get_date
        )
        # Web & Browser
        from tools.browser import search_web, play_youtube
        from tools.web import get_weather, get_news
        # Vision
        from vision.screen import analyze_screen
        from vision.camera import analyze_camera, look, watch

        self.tools = {
            "volume_up": lambda p: volume_up(),
            "volume_down": lambda p: volume_down(p.get("level", 50)),
            "volume_set": lambda p: volume_set(p.get("level", 50)),
            "volume_mute": lambda p: volume_mute(),
            "set_volume": lambda p: control_volume(p.get("action", "up")),
            "control_media": lambda p: control_media(p.get("action", "play")),
            "control_window": lambda p: control_window(p.get("action", "minimize")),
            "take_screenshot": lambda p: take_screenshot(),
            "lock_screen": lambda p: lock_screen(),
            "open_app": lambda p: open_app(p.get("name", "") or p.get("application_id", "") or p.get("app_name", "") or p.get("target", "") or p.get("app", "")),
            "close_app": lambda p: close_app(p.get("name", "") or p.get("target", "") or p.get("app", "")),
            "search_web": lambda p: search_web(p.get("query", "")),
            "search_google": lambda p: search_web(p.get("query", "")),
            "play_youtube": lambda p: play_youtube(p.get("query", "") or p.get("song", "") or p.get("video", "")),
            "get_weather": lambda p: get_weather(p.get("location", "")),
            "get_news": lambda p: get_news(),
            "get_time": lambda p: get_time(),
            "get_date": lambda p: get_date(),
            "analyze_screen": lambda p: analyze_screen(p.get("question", "") or p.get("prompt", "")),
            "analyze_camera": lambda p: analyze_camera(p.get("prompt", "What do you see?")),
            "look": lambda p: look(p.get("prompt", "What do you see?"), p.get("reason", "")),
            "watch": lambda p: watch(int(p.get("seconds", 4)), p.get("prompt", "Analyze what changed."), p.get("reason", "")),
            "get_system_stats": lambda p: __import__("tools.system", fromlist=["format_system_report"]).format_system_report(),
        }

        # Memory Tools
        from memory.user_memory import user_memory
        self.tools["remember_fact"] = lambda p: user_memory.remember(p.get("key", ""), p.get("value", ""))
        self.tools["retrieve_fact"] = lambda p: user_memory.get_fact(p.get("key", ""))
        self.tools["forget_fact"] = lambda p: user_memory.forget(p.get("key", ""))

        # File Tools
        try:
            from tools.files import list_directory, read_file, write_file, delete_file
            self.tools["list_directory"] = lambda p: list_directory(p.get("path", "."))
            self.tools["read_file"] = lambda p: read_file(p.get("path", ""))
            self.tools["write_file"] = lambda p: write_file(p.get("path", ""), p.get("content", ""))
            self.tools["delete_file"] = lambda p: delete_file(p.get("path", ""))
        except ImportError:
            pass

        # Vision Gestures
        try:
            from vision.gestures import start_gesture_mouse, stop_gesture_mouse
            self.tools["gesture_mouse_start"] = lambda p: start_gesture_mouse()
            self.tools["gesture_mouse_stop"] = lambda p: stop_gesture_mouse()
        except ImportError:
            pass

        # Screen-Aware Computer Actions
        from core.action_schema import execute_computer_action
        self.tools["screen_click"] = lambda p: execute_computer_action("click", p)[1]
        self.tools["screen_double_click"] = lambda p: execute_computer_action("double_click", p)[1]
        self.tools["screen_right_click"] = lambda p: execute_computer_action("right_click", p)[1]
        self.tools["screen_type"] = lambda p: execute_computer_action("type", p)[1]
        self.tools["screen_hotkey"] = lambda p: execute_computer_action("hotkey", p)[1]
        self.tools["screen_scroll"] = lambda p: execute_computer_action("scroll", p)[1]
        self.tools["screen_wait"] = lambda p: execute_computer_action("wait", p)[1]

        # Office & Document Generation
        from tools.office import create_presentation, create_spreadsheet, create_word_document, create_pdf_document
        self.tools["create_presentation"] = lambda p: create_presentation(p.get("title", "Presentation"), p.get("slides", []), p.get("output_path"))
        self.tools["create_spreadsheet"] = lambda p: create_spreadsheet(p.get("title", "Workbook"), p.get("sheets_data", []), p.get("output_path"))
        self.tools["create_word_document"] = lambda p: create_word_document(p.get("title", "Document"), p.get("content", []), p.get("output_path"))
        self.tools["create_pdf_document"] = lambda p: create_pdf_document(p.get("title", "Document"), p.get("content", []), p.get("output_path"))

        # Web & Landing Page Generator
        from tools.web_builder import build_website
        self.tools["build_website"] = lambda p: build_website(p.get("topic", "My Website"), p.get("template_style", "modern"), p.get("output_dir"))

        # Computer & Environment Settings
        from tools.computer_settings import set_brightness, toggle_dark_mode, toggle_wifi, toggle_bluetooth, get_system_settings
        self.tools["set_brightness"] = lambda p: set_brightness(p.get("level", 70))
        self.tools["toggle_dark_mode"] = lambda p: toggle_dark_mode(p.get("enabled", True))
        self.tools["toggle_wifi"] = lambda p: toggle_wifi(p.get("state", "enable"))
        self.tools["toggle_bluetooth"] = lambda p: toggle_bluetooth(p.get("state", "enable"))
        self.tools["get_system_settings"] = lambda p: get_system_settings()

        # Advanced File Processor
        from tools.file_processor import organize_directory, find_large_files, clean_temp_files, compress_files, extract_archive
        self.tools["organize_directory"] = lambda p: organize_directory(p.get("path", "~/Downloads"))
        self.tools["find_large_files"] = lambda p: find_large_files(p.get("path", "~"), p.get("min_mb", 100.0))
        self.tools["clean_temp_files"] = lambda p: clean_temp_files()
        self.tools["compress_files"] = lambda p: compress_files(p.get("source_path", "."), p.get("zip_name"))
        self.tools["extract_archive"] = lambda p: extract_archive(p.get("zip_path", ""), p.get("target_dir"))

        # Media & Content
        from tools.media_controller import spotify_control, get_youtube_transcript_and_summary
        self.tools["spotify_control"] = lambda p: spotify_control(p.get("action", "play"), p.get("query"))
        self.tools["get_youtube_transcript_and_summary"] = lambda p: get_youtube_transcript_and_summary(p.get("url") or p.get("video_id") or "")

        # Productivity & Daily Workflow
        from tools.productivity import set_reminder, get_active_reminders, cancel_reminder, daily_briefing, analyze_clipboard
        self.tools["set_reminder"] = lambda p: set_reminder(p.get("message", ""), p.get("delay_minutes", 10.0), p.get("time_str"))
        self.tools["get_active_reminders"] = lambda p: get_active_reminders()
        self.tools["cancel_reminder"] = lambda p: cancel_reminder(p.get("reminder_id", ""))
        self.tools["daily_briefing"] = lambda p: daily_briefing()
        self.tools["analyze_clipboard"] = lambda p: analyze_clipboard()

        # Social & Messaging
        from tools.social import send_whatsapp_message, check_instagram_dms, reply_instagram_dm
        self.tools["send_whatsapp_message"] = lambda p: send_whatsapp_message(p.get("recipient", "") or p.get("to", "") or p.get("contact", ""), p.get("message", "") or p.get("text", ""))
        self.tools["check_instagram_dms"] = lambda p: check_instagram_dms(p.get("username"), p.get("password"))
        self.tools["reply_instagram_dm"] = lambda p: reply_instagram_dm(p.get("thread_id", ""), p.get("message", ""))

        # Fitness & Health Vision
        from tools.fitness import analyze_meal_nutrition, count_exercise_reps
        self.tools["analyze_meal_nutrition"] = lambda p: analyze_meal_nutrition(p.get("meal_info", ""))
        self.tools["count_exercise_reps"] = lambda p: count_exercise_reps(p.get("exercise_type", "pushup"), p.get("duration_seconds", 30))

        # Smart Home IoT
        from tools.smart_home import discover_smart_devices, control_smart_plug, control_smart_bulb
        self.tools["discover_smart_devices"] = lambda p: discover_smart_devices()
        self.tools["control_smart_plug"] = lambda p: control_smart_plug(p.get("device_alias", ""), p.get("state", "on"))
        self.tools["control_smart_bulb"] = lambda p: control_smart_bulb(p.get("device_alias", ""), p.get("state", "on"), p.get("brightness"))

        # Developer Automation
        from tools.dev_tools import git_quick_status, explain_code_snippet
        self.tools["git_quick_status"] = lambda p: git_quick_status(p.get("repo_path"))
        self.tools["explain_code_snippet"] = lambda p: explain_code_snippet(p.get("code", ""), p.get("language"))

        # Mobile Pairing & Remote Access
        from tools.pairing_manager import pair_mobile, list_paired_devices, revoke_mobile_device
        self.tools["pair_mobile"] = lambda p: pair_mobile()
        self.tools["list_paired_devices"] = lambda p: list_paired_devices()
        self.tools["revoke_mobile_device"] = lambda p: revoke_mobile_device(p.get("device_id", ""))
        from tools.phone_controller import (
            unlock_phone, lock_phone, setup_wireless_adb, connect_wireless_phone,
            open_phone_app, play_phone_youtube, send_phone_whatsapp
        )
        self.tools["unlock_phone"] = lambda p: unlock_phone(p.get("pin"))
        self.tools["lock_phone"] = lambda p: lock_phone()
        self.tools["setup_wireless_phone"] = lambda p: setup_wireless_adb()
        self.tools["connect_wireless_phone"] = lambda p: connect_wireless_phone(p.get("ip", ""), int(p.get("port", 5555)))
        self.tools["open_phone_app"] = lambda p: open_phone_app(p.get("app_name", "") or p.get("name", "") or p.get("app", ""))
        self.tools["play_phone_youtube"] = lambda p: play_phone_youtube(p.get("query", "") or p.get("song", "") or "")
        self.tools["send_phone_whatsapp"] = lambda p: send_phone_whatsapp(p.get("recipient", "") or p.get("to", ""), p.get("message", "") or p.get("text", ""))

        # Smart TV Controller
        from tools.tv_controller import (
            discover_smart_tvs, connect_tv, tv_remote_control,
            tv_launch_app, tv_play_media, tv_input_text
        )
        self.tools["discover_smart_tvs"] = lambda p: discover_smart_tvs()
        self.tools["connect_tv"] = lambda p: connect_tv(p.get("ip", ""), p.get("port"), p.get("tv_type", "auto"))
        self.tools["tv_remote_control"] = lambda p: tv_remote_control(p.get("action", "select"), p.get("tv_ip"))
        self.tools["tv_launch_app"] = lambda p: tv_launch_app(p.get("app_name", "youtube"), p.get("tv_ip"))
        self.tools["tv_play_media"] = lambda p: tv_play_media(p.get("query", ""), p.get("tv_ip"))
        self.tools["tv_input_text"] = lambda p: tv_input_text(p.get("text", ""), p.get("tv_ip"))

        # Autonomous Background Monitors
        from tools.background_monitor import (
            monitor_crypto_price, monitor_website_uptime, monitor_system_resources,
            list_background_monitors, cancel_background_monitor
        )
        self.tools["monitor_crypto_price"] = lambda p: monitor_crypto_price(p.get("coin_id", "bitcoin"), p.get("threshold", 0.0), p.get("condition", "above"), p.get("interval_sec", 60))
        self.tools["monitor_website_uptime"] = lambda p: monitor_website_uptime(p.get("url", ""), p.get("interval_sec", 60))
        self.tools["monitor_system_resources"] = lambda p: monitor_system_resources(p.get("ram_threshold", 85.0), p.get("cpu_threshold", 90.0), p.get("interval_sec", 30))
        self.tools["list_background_monitors"] = lambda p: list_background_monitors()
        self.tools["cancel_background_monitor"] = lambda p: cancel_background_monitor(p.get("monitor_id", ""))

        # Meeting Assistant & Minutes
        from tools.meeting_assistant import start_meeting_recording, stop_meeting_recording
        self.tools["start_meeting_recording"] = lambda p: start_meeting_recording(p.get("meeting_title", "Discussion"))
        self.tools["stop_meeting_recording"] = lambda p: stop_meeting_recording(p.get("meeting_title", "Meeting Minutes"), p.get("participants", ""))

        # Advanced Media Downloads
        from tools.media_controller import download_youtube_audio, download_youtube_video
        self.tools["download_youtube_audio"] = lambda p: download_youtube_audio(p.get("url") or p.get("query") or "")
        self.tools["download_youtube_video"] = lambda p: download_youtube_video(p.get("url") or p.get("query") or "")

        # Window Management & Snapping
        from tools.computer import tile_window_left, tile_window_right, minimize_all_windows, snap_window
        self.tools["tile_window_left"] = lambda p: tile_window_left()
        self.tools["tile_window_right"] = lambda p: tile_window_right()
        self.tools["minimize_all_windows"] = lambda p: minimize_all_windows()
        self.tools["snap_window"] = lambda p: snap_window(p.get("direction", "left"))

        # Advanced Browser Automation
        from tools.browser import (
            browser_navigate, browser_click_element, browser_type_text,
            browser_capture_page, browser_extract_text
        )
        self.tools["browser_navigate"] = lambda p: browser_navigate(p.get("url", ""))
        self.tools["browser_click_element"] = lambda p: browser_click_element(p.get("selector", "") or p.get("text", ""))
        self.tools["browser_type_text"] = lambda p: browser_type_text(p.get("selector", ""), p.get("text", ""))
        self.tools["browser_capture_page"] = lambda p: browser_capture_page(p.get("filename", "web_capture.png"))
        self.tools["browser_extract_text"] = lambda p: browser_extract_text()
        # Obsidian Markdown Memory Vault
        from tools.vault_manager import (
            read_memory_vault, write_memory_vault_note, sync_memory_vault, open_obsidian_vault,
            get_active_priorities, update_active_priorities, log_daily_note, capture_inbox_item,
            read_project_context
        )
        self.tools["read_memory_vault"] = lambda p: read_memory_vault(p.get("category", "all"))
        self.tools["write_memory_vault_note"] = lambda p: write_memory_vault_note(p.get("category", "Projects"), p.get("title", ""), p.get("content", ""))
        self.tools["sync_memory_vault"] = lambda p: sync_memory_vault()
        self.tools["open_obsidian_vault"] = lambda p: open_obsidian_vault()
        self.tools["get_active_priorities"] = lambda p: get_active_priorities()
        self.tools["update_active_priorities"] = lambda p: update_active_priorities(p.get("content", ""))
        self.tools["log_daily_note"] = lambda p: log_daily_note(p.get("entry", ""))
        self.tools["capture_inbox_item"] = lambda p: capture_inbox_item(p.get("text", ""))
        self.tools["read_project_context"] = lambda p: read_project_context(p.get("project", p.get("project_name", "")))

        # Hologram Theme Engine
        from communication.broadcaster import get_broadcaster
        def _set_theme(p):
            theme = p.get("theme") or p.get("color", "orange")
            get_broadcaster().broadcast_theme(theme)
            return f"Holographic theme updated to {theme}, sir."
        self.tools["set_hologram_theme"] = _set_theme

        # LEO Native Tools
        from tools.leo_tools import (
            open_application, manage_obsidian_note, get_system_telemetry
        )
        self.tools["open_application"] = lambda p: open_app(p.get("application_id", "") or p.get("app_name", "") or p.get("name", "") or p.get("app", "") or p.get("target", ""))
        self.tools["manage_obsidian_note"] = lambda p: manage_obsidian_note(p.get("action", "read"), p.get("title", ""), p.get("content", ""))
        self.tools["get_system_telemetry"] = lambda p: get_system_telemetry()

        # Push-to-Talk Voice Engine
        from voice.push_to_talk import start_push_to_talk, stop_push_to_talk
        self.tools["start_push_to_talk"] = lambda p: start_push_to_talk(p.get("hotkey", "HOME"))
        self.tools["stop_push_to_talk"] = lambda p: stop_push_to_talk()


    def get_tool_permission(self, tool_name: str, params: Dict[str, Any] = None) -> Permission:
        params = params or {}
        level, _ = check_permission(tool_name, params)
        return Permission[level.value]

    def execute_step(self, tool: str, params: Dict[str, Any], permission: str = None, goal: str = "") -> ExecutionResult:
        start_t = time.time()
        # Authoritative security check: python ground truth overrides whatever LLM passed
        perm_level, reason = check_permission(tool, params)

        if perm_level == PermissionLevel.BLOCKED:
            err = f"Security Policy BLOCKED tool '{tool}': {reason}"
            logger.warning(f"[Executor] {err}")
            log_action(goal=goal, tool=tool, params=params, permission="BLOCKED", success=False, error=err, duration_ms=0.0)
            return ExecutionResult(False, error=err)

        if perm_level == PermissionLevel.CONFIRM:
            target_desc = f"Execute '{tool}' with params {params}?"
            if not self.confirm_callback(target_desc):
                err = f"User declined execution confirmation for tool '{tool}'."
                log_action(goal=goal, tool=tool, params=params, permission="CONFIRM", success=False, error=err, duration_ms=0.0)
                return ExecutionResult(False, error=err)

        if tool not in self.tools:
            err = f"Tool '{tool}' is not registered in system."
            log_action(goal=goal, tool=tool, params=params, permission=perm_level.value, success=False, error=err, duration_ms=0.0)
            return ExecutionResult(False, error=err)

        try:
            output = self.tools[tool](params)
            duration_ms = (time.time() - start_t) * 1000.0

            # Ground truth verification step
            verification = verify_action(tool, params, output)
            log_action(
                goal=goal,
                tool=tool,
                params=params,
                permission=perm_level.value,
                success=verification.success,
                error="" if verification.success else verification.observation,
                duration_ms=duration_ms
            )

            if not verification.success:
                return ExecutionResult(False, output=output, error=verification.observation, observation=verification.observation)

            return ExecutionResult(True, output=output, observation=verification.observation)
        except Exception as e:
            duration_ms = (time.time() - start_t) * 1000.0
            err_msg = str(e)
            log_action(goal=goal, tool=tool, params=params, permission=perm_level.value, success=False, error=err_msg, duration_ms=duration_ms)
            return ExecutionResult(False, error=err_msg)

    def execute_plan(self, plan) -> List[Dict[str, Any]]:
        results = []
        for step in plan.steps:
            result = self.execute_step(step.tool, step.params, step.permission, goal=plan.goal)
            results.append({
                "tool": step.tool,
                "params": step.params,
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "observation": result.observation
            })
            if not result.success:
                logger.warning(f"[Executor] Step failed: {step.tool} - {result.error}")
                break
        return results