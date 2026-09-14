"""
=============================================================================
JARVIS Core: Intent Router (Simple Fast-Path vs Complex Multi-Step Path)
=============================================================================
Goal: Route simple direct voice requests directly to tools in <0.05s,
      and route complex multi-step requests to the LLM Planner.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import re

def route_intent(user_query: str) -> dict:
    """Routes user query to either simple direct tool call or complex LLM plan."""
    if not user_query:
        return {"type": "SIMPLE", "tool": None, "params": {}}

    q = user_query.lower().strip()

    # Fast Path Simple Tool Mappings
    if "lock" in q and ("screen" in q or "laptop" in q or "pc" in q):
        return {"type": "SIMPLE", "tool": "lock_screen", "params": {}}

    if "screenshot" in q or "capture screen" in q:
        return {"type": "SIMPLE", "tool": "take_screenshot", "params": {}}

    # Vision & Camera Fast-Paths (JARVIS look / watch)
    if any(k in q for k in ("watch me", "watch this", "watch my form", "watch what happens", "did that work", "am i doing this right")):
        sec = 4
        num_m = re.search(r'\b(\d+)\s*(?:seconds?|s)\b', q)
        if num_m:
            sec = max(2, min(10, int(num_m.group(1))))
        return {"type": "SIMPLE", "tool": "watch", "params": {"seconds": sec, "prompt": user_query}}

    if any(k in q for k in ("look at me", "look at this", "what am i holding", "read this label", "what do you see in the camera", "look through camera", "take a look", "what's in front of me", "what is in front of me")):
        return {"type": "SIMPLE", "tool": "look", "params": {"prompt": user_query}}

    if q in ("look", "look around", "what do you see"):
        return {"type": "SIMPLE", "tool": "look", "params": {"prompt": "Describe what is in front of the camera."}}

    if ("volume" in q or "mute" in q or "unmute" in q) and "tv" not in q:
        num_match = re.search(r'\b(\d{1,3})\b', q)
        if num_match:
            lvl = max(0, min(100, int(num_match.group(1))))
            return {"type": "SIMPLE", "tool": "set_volume", "params": {"level": lvl}}
        if "unmute" in q:
            return {"type": "SIMPLE", "tool": "set_volume", "params": {"action": "unmute"}}
        if "mute" in q:
            return {"type": "SIMPLE", "tool": "set_volume", "params": {"action": "mute"}}
        action = "up" if "up" in q or "increase" in q else ("down" if "down" in q or "decrease" in q else "up")
        return {"type": "SIMPLE", "tool": "set_volume", "params": {"action": action}}

    # -----------------------------------------------------------------------
    # YouTube / Song / Video Playback Fast-Paths
    # Handles: "open animals song in youtube", "play animals song on youtube", "open youtube", etc.
    # -----------------------------------------------------------------------
    if q in ("open youtube", "launch youtube", "go to youtube", "youtube", "start youtube"):
        return {"type": "SIMPLE", "tool": "play_youtube", "params": {"query": ""}}

    yt_match = re.search(r'^(?:open|play|search|search for|find)\s+(.+?)\s+(?:in|on)\s+youtube$', q)
    if yt_match and not ("on tv" in q or "tv" in q):
        song_query = yt_match.group(1).strip()
        return {"type": "SIMPLE", "tool": "play_youtube", "params": {"query": song_query}}

    song_prefix_match = re.search(r'^(?:open|play|listen to)\s+(?:song|video|track|music)\s+(.+)$', q)
    if song_prefix_match and not ("on tv" in q or "tv" in q):
        song_query = song_prefix_match.group(1).strip()
        if " on spotify" in song_query or " spotify" in song_query:
            clean_q = song_query.replace(" on spotify", "").replace(" spotify", "").strip()
            return {"type": "SIMPLE", "tool": "spotify_control", "params": {"action": "play", "query": clean_q}}
        clean_q = song_query.replace(" on youtube", "").replace(" youtube", "").strip()
        return {"type": "SIMPLE", "tool": "play_youtube", "params": {"query": clean_q}}

    # Specific Song / Video Playback Requests (e.g. "play animal song", "play despacito")
    if q.startswith("play ") and len(q.split()) > 1 and not ("on tv" in q or "tv" in q):
        song_query = re.sub(r"^play\s+", "", q).strip().rstrip(".")
        if " on spotify" in song_query or " spotify" in song_query:
            clean_q = song_query.replace(" on spotify", "").replace(" spotify", "").strip()
            return {"type": "SIMPLE", "tool": "spotify_control", "params": {"action": "play", "query": clean_q}}
        if " on youtube" in song_query or " youtube" in song_query:
            clean_q = song_query.replace(" on youtube", "").replace(" youtube", "").strip()
            return {"type": "SIMPLE", "tool": "play_youtube", "params": {"query": clean_q}}
        return {"type": "SIMPLE", "tool": "play_youtube", "params": {"query": song_query}}

    # -----------------------------------------------------------------------
    # Social Messaging & WhatsApp Fast-Paths
    # Handles: "send message to mom: hello", "send whatsapp to 9876543210: are you free", "send message", etc.
    # -----------------------------------------------------------------------
    if any(q.startswith(k) for k in ("send message", "send a message", "send whatsapp", "send a whatsapp", "whatsapp ")):
        raw = user_query.strip()
        # "send message to <recipient>: <message>" or "send message to <recipient> saying <message>"
        m = re.search(r'^(?:send\s+(?:a\s+)?(?:whatsapp\s+)?message|send\s+(?:a\s+)?whatsapp|whatsapp)\s+to\s+([^:]+?)[:\s]+(?:saying\s+|that\s+)?(.+)$', raw, re.IGNORECASE)
        if m:
            recip = m.group(1).strip()
            msg_text = m.group(2).strip()
            return {"type": "SIMPLE", "tool": "send_whatsapp_message", "params": {"recipient": recip, "message": msg_text}}

        # "send message to <recipient>" (without message body)
        m_recip_only = re.search(r'^(?:send\s+(?:a\s+)?(?:whatsapp\s+)?message|send\s+(?:a\s+)?whatsapp|whatsapp)\s+to\s+([^:]+)$', raw, re.IGNORECASE)
        if m_recip_only:
            recip = m_recip_only.group(1).strip()
            return {"type": "SIMPLE", "tool": "send_whatsapp_message", "params": {"recipient": recip, "message": ""}}

        # "send message: <message>" or "send message <message>"
        m_msg_only = re.search(r'^(?:send\s+(?:a\s+)?(?:whatsapp\s+)?message|send\s+(?:a\s+)?whatsapp|whatsapp)[:\s]+(.+)$', raw, re.IGNORECASE)
        if m_msg_only:
            msg_text = m_msg_only.group(1).strip()
            return {"type": "SIMPLE", "tool": "send_whatsapp_message", "params": {"recipient": "", "message": msg_text}}

        return {"type": "SIMPLE", "tool": "send_whatsapp_message", "params": {"recipient": "", "message": ""}}

    # Playback Media Key Toggles (pause, resume, skip, etc.)
    if q in ("play", "pause", "resume", "pause music", "resume music", "skip", "next track", "previous track"):
        action = "play" if "play" in q or "resume" in q else ("pause" if "pause" in q else "next")
        return {"type": "SIMPLE", "tool": "control_media", "params": {"action": action}}

    if "minimize" in q or "maximize" in q or "close window" in q:
        action = "minimize" if "minimize" in q else ("maximize" if "maximize" in q else "close")
        return {"type": "SIMPLE", "tool": "control_window", "params": {"action": action}}

    if "time" in q and "timer" not in q:
        return {"type": "SIMPLE", "tool": "get_time", "params": {}}

    if (re.search(r'\bdate\b', q) or "today" in q) and "weather" not in q:
        return {"type": "SIMPLE", "tool": "get_date", "params": {}}

    if "telemetry" in q or "system telemetry" in q:
        return {"type": "SIMPLE", "tool": "get_system_telemetry", "params": {}}

    # -----------------------------------------------------------------------
    # Desktop Application Launching Fast-Paths
    # Handles: "open whatsapp", "open chrome", "launch notepad", "open <any app>"
    # -----------------------------------------------------------------------
    known_apps = (
        "whatsapp", "telegram", "discord", "chrome", "google chrome", "edge", "microsoft edge",
        "notepad", "calculator", "calc", "terminal", "cmd", "powershell", "task manager", "taskmgr",
        "settings", "explorer", "files", "file explorer", "spotify", "camera", "photos", "paint",
        "vscode", "vs code", "code", "word", "excel", "powerpoint", "obsidian", "browser", "youtube",
        "clock", "alarms", "store", "microsoft store"
    )
    if q.startswith("open app ") or q.startswith("launch app ") or (q.startswith("open ") and any(a in q for a in known_apps)) or (q.startswith("launch ") and any(a in q for a in known_apps)):
        matched_app = None
        for a in known_apps:
            if a in q:
                matched_app = a
                break
        if matched_app:
            if matched_app == "youtube":
                return {"type": "SIMPLE", "tool": "play_youtube", "params": {"query": ""}}
            return {"type": "SIMPLE", "tool": "open_app", "params": {"name": matched_app}}

    # Generic dynamic application launch for any other Windows app
    if q.startswith("open ") or q.startswith("launch "):
        app_cand = re.sub(r'^(?:open\s+app|launch\s+app|open|launch)[:\s]+', '', q).strip()
        reserved = ("note", "vault", "memory", "priorities", "phone", "tv", "camera", "reminder", "clipboard", "url", "link")
        if app_cand and len(app_cand.split()) <= 3 and not any(app_cand.startswith(r) for r in reserved):
            if "youtube" in app_cand:
                return {"type": "SIMPLE", "tool": "play_youtube", "params": {"query": ""}}
            return {"type": "SIMPLE", "tool": "open_app", "params": {"name": app_cand}}

    if q.startswith("read note ") or q.startswith("view note "):
        note_name = re.sub(r'^(read note|view note)[:\s]+', '', user_query, flags=re.IGNORECASE).strip()
        return {"type": "SIMPLE", "tool": "read_note", "params": {"relative_path": note_name}}

    if q.startswith("propose note ") or q.startswith("update note ") or q.startswith("propose update "):
        parts = re.sub(r'^(propose note|update note|propose update)[:\s]+', '', user_query, flags=re.IGNORECASE).split(":", 1)
        target = parts[0].strip()
        content = parts[1].strip() if len(parts) > 1 else "Updated entry"
        return {"type": "SIMPLE", "tool": "propose_note_update", "params": {"relative_path": target, "content": content}}

    if "battery" in q or "system status" in q or "cpu" in q or "ram" in q or "system stats" in q:
        return {"type": "SIMPLE", "tool": "get_system_stats", "params": {}}

    if "briefing" in q or "morning update" in q or "daily update" in q:
        return {"type": "SIMPLE", "tool": "daily_briefing", "params": {}}

    if "clipboard" in q and ("analyze" in q or "check" in q or "read" in q or "what is" in q or "inspect" in q):
        return {"type": "SIMPLE", "tool": "analyze_clipboard", "params": {}}

    if "clean temp" in q or "clear temp" in q or "purge temp" in q or "clean temporary" in q:
        return {"type": "SIMPLE", "tool": "clean_temp_files", "params": {}}

    if "brightness" in q:
        level = 100 if "max" in q or "high" in q else (30 if "low" in q or "dim" in q else 70)
        return {"type": "SIMPLE", "tool": "set_brightness", "params": {"level": level}}

    if "dark mode" in q or "dark theme" in q:
        return {"type": "SIMPLE", "tool": "toggle_dark_mode", "params": {"enabled": True}}

    if "light mode" in q or "light theme" in q:
        return {"type": "SIMPLE", "tool": "toggle_dark_mode", "params": {"enabled": False}}

    if "show reminders" in q or "list reminders" in q or "active reminders" in q or "get reminders" in q:
        return {"type": "SIMPLE", "tool": "get_active_reminders", "params": {}}

    if "spotify" in q:
        action = "play" if "play" in q else ("pause" if "pause" in q else "toggle")
        return {"type": "SIMPLE", "tool": "spotify_control", "params": {"action": action}}

    if any(k in q for k in ("pair my mobile", "pair mobile", "pair phone", "connect mobile", "connect phone", "connect my phone")):
        return {"type": "SIMPLE", "tool": "pair_mobile", "params": {}}

    if any(k in q for k in ("unlock phone", "unlock my phone", "open my phone", "unlock it wirelessly", "unlock wirelessly", "unlock phone wirelessly")):
        pin_match = re.search(r'\b\d{4,8}\b', q)
        pin = pin_match.group(0) if pin_match else ""
        return {"type": "SIMPLE", "tool": "unlock_phone", "params": {"pin": pin}}

    if any(k in q for k in ("setup wireless phone", "setup wireless adb", "enable wireless phone", "connect wireless phone", "connect phone wirelessly")):
        ip_match = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', q)
        if ip_match:
            return {"type": "SIMPLE", "tool": "connect_wireless_phone", "params": {"ip": ip_match.group(1), "port": 5555}}
        return {"type": "SIMPLE", "tool": "setup_wireless_phone", "params": {}}

    if any(k in q for k in ("lock phone", "lock my phone")):
        return {"type": "SIMPLE", "tool": "lock_phone", "params": {}}

    # Smart TV Fast-Paths
    if any(k in q for k in ("discover tv", "find tv", "search for tv", "scan for tv", "find my tv", "detect tv", "access tv", "access my tv")):
        return {"type": "SIMPLE", "tool": "discover_smart_tvs", "params": {}}

    if "connect tv" in q or "connect to tv" in q:
        ip_match = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', q)
        ip = ip_match.group(1) if ip_match else ""
        return {"type": "SIMPLE", "tool": "connect_tv", "params": {"ip": ip}}

    if any(k in q for k in ("turn on tv", "turn off tv", "power tv", "switch on tv", "switch off tv")):
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "power"}}

    if any(k in q for k in ("tv volume up", "volume up on tv", "turn up tv")):
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "volume_up"}}

    if any(k in q for k in ("tv volume down", "volume down on tv", "turn down tv")):
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "volume_down"}}

    if any(k in q for k in ("mute tv", "unmute tv")):
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "mute"}}

    if "on tv" in q and any(a in q for a in ("youtube", "netflix", "prime", "spotify", "disney")):
        for a in ("youtube", "netflix", "prime", "spotify", "disney"):
            if a in q:
                return {"type": "SIMPLE", "tool": "tv_launch_app", "params": {"app_name": a}}

    if any(k in q for k in ("tv ok", "tv select", "tv enter")):
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "select"}}

    if "tv up" in q:
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "up"}}

    if "tv down" in q:
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "down"}}

    if "tv left" in q:
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "left"}}

    if "tv right" in q:
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "right"}}

    if "tv back" in q:
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "back"}}

    if "tv home" in q:
        return {"type": "SIMPLE", "tool": "tv_remote_control", "params": {"action": "home"}}

    if any(k in q for k in ("list paired devices", "paired phones", "paired devices")):
        return {"type": "SIMPLE", "tool": "list_paired_devices", "params": {}}

    if "tile left" in q or "snap left" in q:
        return {"type": "SIMPLE", "tool": "tile_window_left", "params": {}}

    if "tile right" in q or "snap right" in q:
        return {"type": "SIMPLE", "tool": "tile_window_right", "params": {}}

    if "minimize all" in q or "show desktop" in q:
        return {"type": "SIMPLE", "tool": "minimize_all_windows", "params": {}}

    if "start meeting recording" in q or "record meeting" in q or "start recording meeting" in q:
        return {"type": "SIMPLE", "tool": "start_meeting_recording", "params": {"meeting_title": "Team Discussion"}}

    if "stop meeting recording" in q or "stop recording meeting" in q or "end meeting recording" in q:
        return {"type": "SIMPLE", "tool": "stop_meeting_recording", "params": {"meeting_title": "Meeting Minutes"}}

    if "list monitors" in q or "show monitors" in q or "background monitors" in q:
        return {"type": "SIMPLE", "tool": "list_background_monitors", "params": {}}

    if "open vault" in q or "open memory vault" in q or "open obsidian" in q:
        return {"type": "SIMPLE", "tool": "open_obsidian_vault", "params": {}}

    if "read vault" in q or "show vault" in q or "read memory vault" in q or "view vault" in q:
        return {"type": "SIMPLE", "tool": "read_memory_vault", "params": {"category": "all"}}

    if "sync vault" in q or "sync memory vault" in q:
        return {"type": "SIMPLE", "tool": "sync_memory_vault", "params": {}}

    # LEO Vault & Workflow Fast-Paths
    if any(k in q for k in ("active priorities", "my priorities", "what are my priorities", "open priorities", "show priorities")):
        return {"type": "SIMPLE", "tool": "get_active_priorities", "params": {}}

    if any(q.startswith(k) for k in ("log daily", "daily note", "log to daily", "log today")):
        clean_entry = re.sub(r'^(log daily note|log daily|daily note|log to daily note|log today)[:\s]+', '', q).strip()
        return {"type": "SIMPLE", "tool": "log_daily_note", "params": {"entry": clean_entry or q}}

    if any(q.startswith(k) for k in ("inbox ", "save to inbox", "add to inbox", "capture thought")):
        clean_item = re.sub(r'^(save to inbox|add to inbox|capture thought|inbox)[:\s]+', '', q).strip()
        return {"type": "SIMPLE", "tool": "capture_inbox_item", "params": {"text": clean_item or q}}

    if any(p in q for p in ("polacraft", "canvs", "screenplay", "screenplays")):
        matched_p = "polacraft" if "polacraft" in q else ("canvs" if "canvs" in q else "screenplays")
        return {"type": "SIMPLE", "tool": "read_project_context", "params": {"project": matched_p}}



    # Holographic AI Theme Fast-Paths
    if any(k in q for k in ("switch to ", "activate ", "change theme to ", "set theme to ", "theme ")) and any(c in q for c in ("blue", "green", "orange", "cyan", "purple", "red", "white", "amber", "warning mode")):
        for c in ("blue", "green", "orange", "cyan", "purple", "red", "white", "amber"):
            if c in q:
                return {"type": "SIMPLE", "tool": "set_hologram_theme", "params": {"theme": c}}
        if "warning mode" in q:
            return {"type": "SIMPLE", "tool": "set_hologram_theme", "params": {"theme": "red"}}

    # Identity & Assistant Persona Fast-Paths
    identity_triggers = (
        "who are you", "who am i talking to", "who am i speaking with", "who am i speaking to",
        "what is your name", "what's your name", "who is this",
        "tell me about yourself", "what are you", "introduce yourself",
        "who made you", "who created you", "who is leo", "who is jarvis",
        "are you jarvis", "are you leo"
    )
    if any(k in q for k in identity_triggers):
        return {
            "type": "CONVERSATION",
            "response": "You are talking to JARVIS, also responding as LEO - your personal AI assistant and workflow partner, Gowtham. I'm running locally on your workstation to help manage your projects, desktop, memory vault, and workflows."
        }

    # Capabilities Fast-Paths
    capability_triggers = (
        "what can you do", "what are your capabilities", "what can i ask you",
        "help me understand what you can do", "how can you help me"
    )
    if any(k in q for k in capability_triggers):
        return {
            "type": "CONVERSATION",
            "response": "I can assist you with local desktop automation, managing your Obsidian memory vault and projects like Polacraft and Canvs, controlling media and smart devices, running system diagnostics, taking notes, and answering complex technical and creative questions."
        }

    # Greetings
    greeting_triggers = (
        "hello", "hi", "hey", "jarvis", "hey jarvis", "leo", "hey leo",
        "are you there", "good morning", "good evening", "good afternoon",
        "wake up", "wake up jarvis", "wake up leo", "hey there", "are you online"
    )
    if q in greeting_triggers or any(q.startswith(g) for g in ("hello jarvis", "hello leo", "hey jarvis", "hey leo", "good morning", "good afternoon", "good evening")):
        return {"type": "GREETING", "response": "Hello Gowtham, what are we working on today?"}

    # Complex Path Multi-Step Request
    return {"type": "COMPLEX", "query": user_query}

if __name__ == "__main__":
    print("Testing Router...")
    print(route_intent("volume up"))
    print(route_intent("Jarvis, I'm going to sleep. Prepare my laptop."))
