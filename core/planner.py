"""
JARVIS Core Planner - Structured JSON Action Planner
Generates validated JSON action plans from natural language goals.
"""
import os
import json
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

config = load_config()
GEMINI_API_KEY = config.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
DEFAULT_MODEL = config.get("DEFAULT_MODEL", "gemini-1.5-flash-8b")
AI_PROVIDER = config.get("AI_PROVIDER", "gemini")

TOOL_REGISTRY = {
    "volume_up": {"description": "Increase system volume", "params": {}, "permission": "SAFE"},
    "volume_down": {"description": "Decrease system volume", "params": {"level": "int (0-100)"}, "permission": "SAFE"},
    "volume_set": {"description": "Set system volume to specific level", "params": {"level": "int (0-100)"}, "permission": "SAFE"},
    "volume_mute": {"description": "Toggle system mute", "params": {}, "permission": "SAFE"},
    "take_screenshot": {"description": "Capture current screen", "params": {}, "permission": "SAFE"},
    "lock_screen": {"description": "Lock the Windows workstation", "params": {}, "permission": "SAFE"},
    "open_app": {"description": "Open an application or website", "params": {"name": "str"}, "permission": "SAFE"},
    "close_app": {"description": "Close an application by name", "params": {"name": "str"}, "permission": "SAFE"},
    "search_web": {"description": "Search the web for information", "params": {"query": "str"}, "permission": "SAFE"},
    "play_youtube": {"description": "Play a video on YouTube", "params": {"query": "str"}, "permission": "SAFE"},
    "get_weather": {"description": "Get current weather", "params": {"location": "str (optional)"}, "permission": "SAFE"},
    "get_time": {"description": "Get current time", "params": {}, "permission": "SAFE"},
    "get_date": {"description": "Get current date", "params": {}, "permission": "SAFE"},
    "get_news": {"description": "Get latest news headlines", "params": {}, "permission": "SAFE"},
    "analyze_screen": {"description": "Analyze current screen content with vision AI", "params": {"question": "str"}, "permission": "SAFE"},
    "analyze_camera": {"description": "Analyze physical environment via webcam", "params": {"prompt": "str"}, "permission": "SAFE"},
    "look": {"description": "Capture single camera frame and analyze physical item or scene via Gemini", "params": {"prompt": "str"}, "permission": "SAFE"},
    "watch": {"description": "Watch camera over time to evaluate motion, exercise form, or transitions via Gemini", "params": {"seconds": "int", "prompt": "str"}, "permission": "SAFE"},
    "gesture_mouse_start": {"description": "Start air-gesture virtual mouse", "params": {}, "permission": "SAFE"},
    "gesture_mouse_stop": {"description": "Stop air-gesture virtual mouse", "params": {}, "permission": "SAFE"},
    "get_system_stats": {"description": "Get CPU, RAM, battery, and disk statistics", "params": {}, "permission": "SAFE"},
    "remember_fact": {"description": "Remember a user preference or fact", "params": {"key": "str", "value": "str"}, "permission": "SAFE"},
    "retrieve_fact": {"description": "Retrieve a user preference or fact", "params": {"key": "str"}, "permission": "SAFE"},
    "list_directory": {"description": "List files in safe directory", "params": {"path": "str"}, "permission": "SAFE"},
    "read_file": {"description": "Read contents of safe file", "params": {"path": "str"}, "permission": "SAFE"},
    "write_file": {"description": "Write text to file in safe directory", "params": {"path": "str", "content": "str"}, "permission": "CONFIRM"},
    "delete_file": {"description": "Delete a file in safe directory", "params": {"path": "str"}, "permission": "CONFIRM"},
    "create_presentation": {"description": "Generate a PowerPoint presentation", "params": {"title": "str", "slides": "list of {title, bullets}"}, "permission": "SAFE"},
    "create_spreadsheet": {"description": "Generate an Excel spreadsheet", "params": {"title": "str", "sheets_data": "dict or 2D list"}, "permission": "SAFE"},
    "create_word_document": {"description": "Generate a Word document (.docx)", "params": {"title": "str", "content": "list of {heading, text}"}, "permission": "SAFE"},
    "create_pdf_document": {"description": "Generate a PDF document", "params": {"title": "str", "content": "list of {heading, text}"}, "permission": "SAFE"},
    "build_website": {"description": "Build a responsive website locally", "params": {"topic": "str", "template_style": "str (modern/dark_tech)"}, "permission": "SAFE"},
    "set_brightness": {"description": "Set display brightness level", "params": {"level": "int (0-100)"}, "permission": "SAFE"},
    "toggle_dark_mode": {"description": "Toggle Windows dark or light theme", "params": {"enabled": "bool"}, "permission": "SAFE"},
    "toggle_wifi": {"description": "Toggle Wi-Fi network interface", "params": {"state": "str (enable/disable)"}, "permission": "CONFIRM"},
    "toggle_bluetooth": {"description": "Toggle Bluetooth adapter", "params": {"state": "str (enable/disable)"}, "permission": "CONFIRM"},
    "get_system_settings": {"description": "Get current Windows display and theme settings", "params": {}, "permission": "SAFE"},
    "organize_directory": {"description": "Organize files in directory into categorized folders", "params": {"path": "str"}, "permission": "CONFIRM"},
    "find_large_files": {"description": "Find files larger than threshold in MB", "params": {"path": "str", "min_mb": "float"}, "permission": "SAFE"},
    "clean_temp_files": {"description": "Purge temporary files to reclaim disk space", "params": {}, "permission": "CONFIRM"},
    "compress_files": {"description": "Compress files/directory into ZIP archive", "params": {"source_path": "str", "zip_name": "str (optional)"}, "permission": "SAFE"},
    "extract_archive": {"description": "Extract ZIP archive", "params": {"zip_path": "str", "target_dir": "str (optional)"}, "permission": "CONFIRM"},
    "spotify_control": {"description": "Control Spotify playback or search", "params": {"action": "str (play/pause/next/prev)", "query": "str (optional)"}, "permission": "SAFE"},
    "get_youtube_transcript_and_summary": {"description": "Fetch transcript and summarize YouTube video", "params": {"url": "str"}, "permission": "SAFE"},
    "set_reminder": {"description": "Set a scheduled timer or reminder", "params": {"message": "str", "delay_minutes": "float", "time_str": "str (optional)"}, "permission": "SAFE"},
    "get_active_reminders": {"description": "Get all active pending reminders", "params": {}, "permission": "SAFE"},
    "cancel_reminder": {"description": "Cancel a pending reminder", "params": {"reminder_id": "str"}, "permission": "SAFE"},
    "daily_briefing": {"description": "Compile comprehensive morning daily briefing", "params": {}, "permission": "SAFE"},
    "analyze_clipboard": {"description": "Analyze and classify current Windows clipboard text", "params": {}, "permission": "SAFE"},
    "send_whatsapp_message": {"description": "Send a WhatsApp message", "params": {"recipient": "str", "message": "str"}, "permission": "CONFIRM"},
    "check_instagram_dms": {"description": "Check recent Instagram direct messages", "params": {}, "permission": "SAFE"},
    "reply_instagram_dm": {"description": "Reply to an Instagram message thread", "params": {"thread_id": "str", "message": "str"}, "permission": "CONFIRM"},
    "analyze_meal_nutrition": {"description": "Analyze meal calories and nutrition from description or photo", "params": {"meal_info": "str"}, "permission": "SAFE"},
    "count_exercise_reps": {"description": "Track workout repetitions via webcam pose analysis", "params": {"exercise_type": "str (pushup/squat)", "duration_seconds": "int"}, "permission": "SAFE"},
    "discover_smart_devices": {"description": "Discover local smart home devices on Wi-Fi", "params": {}, "permission": "SAFE"},
    "control_smart_plug": {"description": "Turn on or off local smart plug", "params": {"device_alias": "str", "state": "str (on/off)"}, "permission": "SAFE"},
    "control_smart_bulb": {"description": "Control smart bulb power and brightness", "params": {"device_alias": "str", "state": "str", "brightness": "int (optional)"}, "permission": "SAFE"},
    "git_quick_status": {"description": "Summarize Git status, branch, and recent changes", "params": {"repo_path": "str (optional)"}, "permission": "SAFE"},
    "explain_code_snippet": {"description": "Explain code snippet logic and structure", "params": {"code": "str", "language": "str (optional)"}, "permission": "SAFE"},
    "pair_mobile": {"description": "Initialize a mobile phone pairing session, generate 6-digit PIN and QR code for remote PC access", "params": {}, "permission": "SAFE"},
    "list_paired_devices": {"description": "List all registered mobile devices paired with JARVIS", "params": {}, "permission": "SAFE"},
    "revoke_mobile_device": {"description": "Revoke access for a paired mobile phone", "params": {"device_id": "str"}, "permission": "CONFIRM"},
}

SYSTEM_PROMPT = f"""You are JARVIS, an AI assistant that creates structured action plans.
You receive a natural language goal and must output a JSON action plan.

Available tools:
{json.dumps(TOOL_REGISTRY, indent=2)}

Rules:
1. Output ONLY valid JSON - no markdown, no extra text
2. Each step must reference a tool from the registry
3. Include "goal", "steps" array with tool, params, permission
4. Use CONFIRM permission for destructive actions
5. Use BLOCKED for unsafe operations
6. Keep plans minimal and logical
7. If the goal is conversational, an identity question, or does not require any tool from the registry, return an empty steps array: {{"goal": "...", "steps": []}}

Example:
{{
  "goal": "prepare laptop for sleep",
  "steps": [
    {{"tool": "volume_set", "params": {{"level": 10}}, "permission": "SAFE"}},
    {{"tool": "take_screenshot", "params": {{}}, "permission": "SAFE"}},
    {{"tool": "lock_screen", "params": {{}}, "permission": "SAFE"}}
  ]
}}"""

@dataclass
class ActionStep:
    tool: str
    params: Dict[str, Any]
    permission: str

@dataclass
class ActionPlan:
    goal: str
    steps: List[ActionStep]

    def to_dict(self) -> Dict:
        return {
            "goal": self.goal,
            "steps": [asdict(s) for s in self.steps]
        }

def call_gemini(prompt: str) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    models = ["gemini-1.5-flash-8b", "gemini-2.5-flash", "gemini-3.6-flash"]
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception:
            continue
    return None

def call_ollama(prompt: str) -> Optional[str]:
    try:
        url = "http://localhost:11434/api/generate"
        payload = {"model": DEFAULT_MODEL, "prompt": prompt, "stream": False}
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            return res.json().get("response", "").strip()
    except Exception:
        pass
    return None

def generate_plan(goal: str, context: str = "") -> Optional[ActionPlan]:
    # Phase 1: Try structured planning via AI Provider abstraction
    try:
        from ai import get_ai_provider
        provider = get_ai_provider()
        plan_dict = provider.generate_plan(goal, TOOL_REGISTRY, context)
        if plan_dict and isinstance(plan_dict, dict) and "steps" in plan_dict:
            steps = []
            for s in plan_dict.get("steps", []):
                # Ensure each step has expected keys
                tool_name = s.get("tool", "")
                params = s.get("params", {})
                perm = s.get("permission", TOOL_REGISTRY.get(tool_name, {}).get("permission", "SAFE"))
                steps.append(ActionStep(tool=tool_name, params=params, permission=perm))
            if steps:
                return ActionPlan(goal=plan_dict.get("goal", goal), steps=steps)
    except Exception as e:
        print(f"[Planner AI Provider Notice]: {e}")

    # Fallback to direct prompt / raw generation if provider didn't return plan
    full_prompt = f"{SYSTEM_PROMPT}\n\nContext: {context}\n\nGoal: {goal}\n\nJSON Plan:"
    
    if AI_PROVIDER == "gemini" and GEMINI_API_KEY:
        response = call_gemini(full_prompt)
    elif AI_PROVIDER == "ollama":
        response = call_ollama(full_prompt)
    else:
        response = call_gemini(full_prompt) or call_ollama(full_prompt)
    
    if not response:
        return None
    
    try:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        data = json.loads(cleaned.strip())
        
        raw_steps = data.get("steps", [])
        steps = [ActionStep(**s) for s in raw_steps if isinstance(s, dict) and s.get("tool") in TOOL_REGISTRY]
        if not steps:
            return None
        return ActionPlan(goal=data.get("goal", goal), steps=steps)
    except Exception as e:
        print(f"[Planner Error] Failed to parse plan: {e}")
        return None

if __name__ == "__main__":
    test_goals = [
        "prepare laptop for sleep",
        "open chrome and search for iron man",
        "play music on youtube",
        "what's the weather like",
    ]
    for goal in test_goals:
        print(f"\n=== Goal: {goal} ===")
        plan = generate_plan(goal)
        if plan:
            print(json.dumps(plan.to_dict(), indent=2))
        else:
            print("Failed to generate plan")