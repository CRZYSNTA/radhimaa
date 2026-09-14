"""
JARVIS V3.0 - Productivity, Reminders & Daily Briefing Tools
Provides local scheduled reminders, intelligent clipboard inspection,
and comprehensive daily briefing compilation.
"""

from __future__ import annotations

import re
import time
import uuid
import datetime
import threading
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("JARVIS.Tools.Productivity")

_ACTIVE_REMINDERS: List[Dict[str, Any]] = []

def _reminder_worker(rem_id: str, message: str, delay_sec: float):
    """Background thread that waits and announces reminder."""
    time.sleep(delay_sec)
    # Check if still active
    global _ACTIVE_REMINDERS
    matching = [r for r in _ACTIVE_REMINDERS if r["id"] == rem_id]
    if matching:
        _ACTIVE_REMINDERS = [r for r in _ACTIVE_REMINDERS if r["id"] != rem_id]
        logger.info(f"[Reminder Triggered]: {message}")
        try:
            from voice.text_to_speech import speak
            speak(f"Reminder, sir: {message}", block=False)
        except Exception:
            print(f"\n🔔 [REMINDER]: {message}\n")

def set_reminder(message: str, delay_minutes: float = 10.0, time_str: Optional[str] = None) -> str:
    """
    Schedules an audible and visual reminder.
    Args:
        message: The reminder note or message.
        delay_minutes: Minutes to wait before triggering.
        time_str: Optional specific time like '14:30' or '5:00 PM'.
    """
    if not message:
        return "Please specify what you would like to be reminded about, sir."

    delay_sec = max(1.0, float(delay_minutes) * 60.0)

    if time_str:
        try:
            # Parse target time today
            now = datetime.datetime.now()
            clean_t = time_str.strip().upper()
            target_dt = None
            for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p"):
                try:
                    parsed = datetime.datetime.strptime(clean_t, fmt)
                    target_dt = now.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
                    if target_dt < now:
                        # If time already passed today, schedule for tomorrow
                        target_dt += datetime.timedelta(days=1)
                    break
                except ValueError:
                    continue
            if target_dt:
                delay_sec = max(1.0, (target_dt - now).total_seconds())
        except Exception as e:
            logger.debug(f"[Reminder Time Parse Note]: {e}")

    rem_id = str(uuid.uuid4())[:6]
    trigger_time = datetime.datetime.now() + datetime.timedelta(seconds=delay_sec)
    
    reminder_entry = {
        "id": rem_id,
        "message": message,
        "set_at": datetime.datetime.now().strftime("%I:%M %p"),
        "trigger_at": trigger_time.strftime("%I:%M %p"),
        "delay_sec": delay_sec
    }
    _ACTIVE_REMINDERS.append(reminder_entry)

    th = threading.Thread(target=_reminder_worker, args=(rem_id, message, delay_sec), daemon=True)
    th.start()

    logger.info(f"[Productivity] Reminder scheduled: '{message}' at {reminder_entry['trigger_at']}")
    return f"Reminder set for {reminder_entry['trigger_at']}: '{message}', sir."

def get_active_reminders() -> str:
    """Returns a formatted list of all active pending reminders."""
    if not _ACTIVE_REMINDERS:
        return "You have no active reminders scheduled at this time, sir."

    lines = ["Active Reminders:"]
    for r in _ACTIVE_REMINDERS:
        lines.append(f"- [{r['id']}] At {r['trigger_at']}: {r['message']}")
    return "\n".join(lines)

def cancel_reminder(reminder_id: str) -> str:
    """Cancels a scheduled reminder by its ID or keyword match."""
    global _ACTIVE_REMINDERS
    target = reminder_id.strip().lower()

    to_remove = [r for r in _ACTIVE_REMINDERS if r["id"].lower() == target or target in r["message"].lower()]
    if not to_remove:
        return f"No matching reminder found for '{reminder_id}', sir."

    _ACTIVE_REMINDERS = [r for r in _ACTIVE_REMINDERS if r not in to_remove]
    return f"Cancelled {len(to_remove)} reminder(s), sir."

def daily_briefing() -> str:
    """
    Compiles a comprehensive morning/daily briefing report including greeting,
    date, time, weather, system status, active reminders, and news headlines.
    """
    now = datetime.datetime.now()
    hour = now.hour
    if hour < 12:
        salutation = "Good morning, sir."
    elif hour < 17:
        salutation = "Good afternoon, sir."
    else:
        salutation = "Good evening, sir."

    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%I:%M %p")

    sections = [
        f"### {salutation}",
        f"Today is **{date_str}**, the time is currently **{time_str}**."
    ]

    # Weather
    try:
        from tools.web import get_weather
        weather_info = get_weather()
        if weather_info and "Unable" not in weather_info:
            sections.append(f"**Weather**: {weather_info}")
    except Exception:
        pass

    # Hardware Telemetry
    try:
        from tools.system import get_system_stats
        stats = get_system_stats()
        cpu = stats.get("cpu_percent", "N/A")
        ram = stats.get("ram_percent", "N/A")
        bat = stats.get("battery_percent", "N/A")
        bat_str = f" | Battery: {bat}%" if bat != "N/A" else ""
        sections.append(f"**System Health**: CPU: {cpu}% | RAM: {ram}%{bat_str}")
    except Exception:
        pass

    # Reminders
    if _ACTIVE_REMINDERS:
        sections.append(f"**Reminders**: You have {len(_ACTIVE_REMINDERS)} pending reminder(s) today.")
    else:
        sections.append("**Reminders**: Your schedule is currently clear.")

    # News Headline
    try:
        from tools.web import get_news
        news = get_news()
        if news and "failed" not in news.lower():
            sections.append(f"**Top News**:\n{news}")
    except Exception:
        pass

    return "\n\n".join(sections)

def analyze_clipboard() -> str:
    """
    Reads and analyzes the current Windows clipboard buffer, classifying content
    (URL, Code, Email, JSON, Path, or Plain Text) and suggesting next actions.
    """
    try:
        import pyperclip
        content = pyperclip.paste()
    except Exception:
        try:
            import subprocess
            res = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"], capture_output=True, text=True, timeout=3)
            content = res.stdout.strip()
        except Exception as e:
            return f"Unable to access clipboard: {e}"

    if not content or not content.strip():
        return "The clipboard is currently empty, sir."

    text = content.strip()
    preview = text[:120] + ("..." if len(text) > 120 else "")

    # URL Detection
    if re.match(r"^https?://[^\s]+$", text):
        return f"Clipboard contains a URL:\n**{text}**\n\n*Action options: I can open this in your browser or scrape its content for you.*"

    # JSON Detection
    if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
        try:
            import json
            parsed = json.loads(text)
            keys = list(parsed.keys()) if isinstance(parsed, dict) else f"List with {len(parsed)} items"
            return f"Clipboard contains structured JSON data:\nKeys/Structure: {keys}\nPreview: `{preview}`"
        except Exception:
            pass

    # Code Block Detection
    code_indicators = ["def ", "class ", "import ", "const ", "function ", "public class", "SELECT ", "<div>", "return "]
    if any(ind in text for ind in code_indicators):
        line_count = len(text.split("\n"))
        return f"Clipboard contains a code snippet ({line_count} lines):\n```\n{preview}\n```\n*Action options: I can explain this code, format it, or save it to a script.*"

    # Email Detection
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    if emails:
        return f"Clipboard contains email address(es): {', '.join(emails)}"

    # Default text analysis
    word_count = len(text.split())
    return f"Clipboard contains text ({word_count} words, {len(text)} chars):\n\"{preview}\""
