"""
=============================================================================
JARVIS V4 — Native Desktop Application Window
=============================================================================
Architecture:
  Windows Desktop Window (pywebview / Edge WebView2)
    ├── Chat Interface & SSE Streaming
    ├── Animated 3D Hologram (WebGL / Three.js)
    ├── Push-to-Talk Microphone Controls (Home Key)
    └── Action Confirmation Panel (CONFIRM Tier Security Gate)
              │
       Local FastAPI Backend (127.0.0.1:8000)
              │
  ┌───────────┼───────────────┐
Cloud AI   Voice Engine   Obsidian Memory
(Gemini)   (PTT/TTS)      (Vault Manager)
              │
       Windows Tool Executor
=============================================================================
"""

import sys
import os
import time
import socket
import logging
import threading
import asyncio

# Configure UTF-8 console output for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("JARVIS.Desktop")

# Ensure workspace root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from communication.broadcaster import get_broadcaster
from orchestration.chat_service import get_chat_service, ChatRequestDTO
from voice.ptt_engine import get_ptt_engine
from voice import text_to_speech


def is_port_open(host: str = "127.0.0.1", port: int = 8000) -> bool:
    """Checks if the FastAPI server is already listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def free_port_if_stale(port: int = 8000):
    """If port 8000 has a stale process not answering /health, terminate it to run fresh server."""
    if not is_port_open("127.0.0.1", port):
        return
    import requests
    try:
        r = requests.get(f"http://127.0.0.1:{port}/health", timeout=0.5)
        if r.status_code == 200 and r.json().get("version") == "3.0":
            logger.info(f"[Desktop] Live backend version {r.json().get('version')} verified on port {port}.")
            return
    except Exception:
        pass

    logger.warning(f"[Desktop] Stale or non-responsive process found on port {port}. Reclaiming...")
    import subprocess
    try:
        out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
        for line in out.strip().splitlines():
            if "LISTENING" in line:
                pid = line.strip().split()[-1]
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
        time.sleep(0.5)
    except Exception as e:
        logger.debug(f"[Desktop Port Reclamation Warning]: {e}")


def run_telemetry_loop():
    """Periodically broadcasts CPU, RAM, and network telemetry to HUD."""
    import psutil
    broadcaster = get_broadcaster()
    while True:
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            broadcaster.broadcast_system_status(cpu, mem, "CONNECTED")
        except Exception:
            pass
        time.sleep(2.0)


def start_backend_server_if_needed():
    """Starts FastAPI in a background daemon thread if not already running."""
    free_port_if_stale(8000)

    if is_port_open("127.0.0.1", 8000):
        logger.info("[Desktop] FastAPI server already active on http://127.0.0.1:8000")
        return None

    logger.info("[Desktop] Launching FastAPI backend server on http://127.0.0.1:8000...")
    import uvicorn
    from server import app

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True, name="FastAPI-Worker")
    t.start()

    # Wait until port is responsive
    for _ in range(50):
        if is_port_open("127.0.0.1", 8000):
            logger.info("[Desktop] FastAPI backend server is live.")
            return server
        time.sleep(0.1)

    logger.warning("[Desktop] FastAPI server startup timed out. Proceeding anyway.")
    return server


def handle_ptt_transcript(transcript: str):
    """
    Invoked by PushToTalkEngine when speech is recognized from the Home key.
    Sends transcript to ChatService and dispatches voice / visual response.
    """
    clean_text = (transcript or "").strip()
    if not clean_text:
        return

    broadcaster = get_broadcaster()
    # 1. Broadcast user message to Holographic Chat Dock
    broadcaster._broadcast_payload({"event": "user_message", "text": clean_text})

    # 2. Process query with ChatService
    service = get_chat_service()
    dto = ChatRequestDTO(
        message=clean_text,
        conversation_id="desktop-ptt",
        user_id="desktop_voice_user"
    )

    try:
        # Run async handle in background worker
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resp = loop.run_until_complete(service.handle(dto))
        loop.close()

        if resp.requires_confirmation:
            tool_payload = resp.confirmation_payload or {}
            broadcaster._broadcast_payload({
                "event": "confirmation_required",
                "tool": tool_payload.get("tool", "propose_note_update"),
                "arguments": tool_payload.get("arguments", {}),
                "conversation_id": resp.conversation_id
            })
            spoken = "I have drafted the note update, sir. Please review and confirm the action in the authorization panel."
            broadcaster.broadcast_assistant_text(spoken)
            text_to_speech.speak(spoken)
        else:
            reply = resp.content or "Action completed, sir."
            broadcaster.broadcast_assistant_text(reply)
            text_to_speech.speak(reply)
    except Exception as e:
        logger.error(f"[Desktop Voice Handler Error]: {e}")
        err_msg = f"System notice: {e}"
        broadcaster.broadcast_assistant_text(err_msg)
        text_to_speech.speak(err_msg)


def run_hands_free_voice_loop():
    """
    Continuous background acoustic listener for wake words ('Jarvis', 'Leo')
    and direct actionable commands ('system telemetry', 'open notepad', etc.).
    Runs concurrently with the Push-to-Talk engine.
    """
    logger.info("[Desktop Voice] Hands-free acoustic listener active. Say 'Jarvis' or 'Leo' to speak hands-free...")
    from voice import speech_to_text, text_to_speech
    from voice.wake_word import check_wake_word, is_action_command
    from core.session import get_session_manager

    sm = get_session_manager()
    broadcaster = get_broadcaster()

    # Initial warm-up pause
    time.sleep(2.0)

    while True:
        try:
            # Wait if assistant is speaking or PTT is actively recording
            ptt = get_ptt_engine()
            while text_to_speech.is_speaking() or (ptt and ptt.is_recording):
                time.sleep(0.15)

            # Capture acoustic input from user's microphone
            raw_text = speech_to_text.listen_to_user()
            if not raw_text:
                continue

            # If user activated PTT in the meantime, ignore hands-free pass
            if ptt and ptt.is_recording:
                continue

            in_session = sm.is_session_active()
            detected_res = check_wake_word(raw_text)
            detected, user_command = detected_res
            identity = getattr(detected_res, "identity", "jarvis")

            # Direct action command fast-pass
            if not detected and is_action_command(raw_text):
                detected = True
                user_command = raw_text.strip().rstrip(".,!?")

            if not in_session and not detected:
                continue

            target_text = user_command if detected and user_command else raw_text

            if not target_text and detected:
                # Solitary wake word (e.g. user just said "Jarvis" or "Leo")
                sm.get_or_create_session(activated_by_wake=True)
                greeting = "Yes, sir? I am listening."
                broadcaster.broadcast_assistant_text(greeting)
                text_to_speech.speak(greeting)
                continue

            logger.info(f"[Desktop Voice Detected]: '{target_text}' (Wake: {detected})")
            sm.get_or_create_session(activated_by_wake=True)
            handle_ptt_transcript(target_text)

        except Exception as e:
            logger.debug(f"[Desktop Voice Listener Notice]: {e}")
            time.sleep(0.3)


def main():
    logger.info("=========================================================")
    logger.info("  STARTING JARVIS / LEO HOLOGRAPHIC DESKTOP OPERATING APP")
    logger.info("=========================================================")

    # 1. Ensure FastAPI server is running
    start_backend_server_if_needed()

    # 2. Ensure ADB server daemon is running persistently & auto-reconnect wireless phone
    try:
        from tools.phone_controller import ensure_adb_server_running, auto_reconnect_wireless
        threading.Thread(
            target=lambda: (ensure_adb_server_running(), auto_reconnect_wireless()),
            daemon=True,
            name="Phone-ADB-Worker"
        ).start()
    except Exception as e:
        logger.debug(f"[Desktop Phone Init Note]: {e}")

    # 3. Generate Mobile Companion Pairing QR and session on Desktop
    try:
        from tools.pairing_manager import pair_mobile
        threading.Thread(target=pair_mobile, daemon=True, name="Mobile-Pairing-Worker").start()
    except Exception as e:
        logger.debug(f"[Desktop Mobile Pairing Init Note]: {e}")

    # 4. Initialize Push-To-Talk Engine (Home key)
    try:
        ptt = get_ptt_engine(on_transcript=handle_ptt_transcript)
        logger.info("[Desktop] Push-to-Talk initialized. Hold [HOME] or click [MIC] to speak.")
    except Exception as e:
        logger.warning(f"[Desktop] Could not initialize PTT listener: {e}")
        ptt = None

    # 3. Launch continuous hands-free voice listener thread
    voice_thread = threading.Thread(target=run_hands_free_voice_loop, daemon=True, name="HandsFree-Voice-Worker")
    voice_thread.start()

    # 4. Launch periodic hardware telemetry broadcast thread
    telemetry_thread = threading.Thread(target=run_telemetry_loop, daemon=True, name="Telemetry-Worker")
    telemetry_thread.start()

    # 5. Create native desktop window using pywebview (Edge WebView2)
    import webview

    target_url = "http://127.0.0.1:8000/interface/index.html"

    logger.info(f"[Desktop] Creating WebGL desktop window pointing to {target_url}...")
    window = webview.create_window(
        title="JARVIS V4 — Holographic AI Operating Interface",
        url=target_url,
        width=1280,
        height=840,
        min_size=(960, 640),
        resizable=True,
        background_color="#000000"
    )

    def on_closed():
        logger.info("[Desktop] Window closed by user. Terminating session.")
        if ptt:
            ptt.interrupt()
        text_to_speech.stop()

    window.events.closed += on_closed

    try:
        # Start GUI main loop with debug enabled (allows right-click Inspect)
        webview.start(debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        if ptt:
            ptt.interrupt()
        text_to_speech.stop()
        logger.info("[Desktop] App shut down cleanly.")


if __name__ == "__main__":
    main()
