"""
=============================================================================
JARVIS V3.0 - Autonomous Personal AI Assistant (Unified Master Entrypoint)
=============================================================================
Architecture:
 - Multi-Provider AI Brain (Gemini, OpenAI, Local Ollama)
 - Structured JSON Action Planner with Ground-Truth Python Security Permissions
 - Observe -> Plan -> Execute -> Verify -> Replan Loop
 - Persistent SQLite Memory (Conversations, User Preferences, Action Logs)
 - Dual STT (Local faster-whisper + Google Fallback) & Neural Edge-TTS
 - Acoustic Double-Clap & Wake Word Detection
 - Multimodal Vision (Desktop Screen + Optional Webcam)
 - PyAutoGUI Computer Control & Sandboxed File Management
 - Futuristic PySide6 Animated Arc Reactor HUD with Tkinter Fallback
=============================================================================
"""

import os
import sys
import threading
import time
import logging

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import config
from core.agent import get_agent
from voice import speech_to_text, text_to_speech, clap_detection, check_wake_word, is_action_command
from ui import create_overlay, set_ui_state
from memory import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("JARVIS.Main")

def run_agent_loop(agent_instance, ui_instance=None):
    """Continuous Observe-Plan-Execute-Verify Agentic Loop."""
    time.sleep(0.5)
    text_to_speech.speak("Systems online. JARVIS version 3.0 ready for your command, sir.", block=True)

    # 1. Start Double-Clap Listener in background thread (if enabled)
    if getattr(config, "CLAP_ENABLED", False):
        try:
            clap_engine = clap_detection.DualTriggerEngine()
            def _on_clap():
                logger.info("[Main] Double-clap activated!")
                if ui_instance:
                    ui_instance.set_state("LISTENING", "Clap trigger activated!")
                text_to_speech.speak("Yes, sir?", block=False)

            threading.Thread(target=lambda: clap_engine.start(callback=_on_clap), daemon=True).start()
            logger.info("[Main] Double-clap engine active.")
        except Exception as e:
            logger.warning(f"[Main] Double-clap initialization notice: {e}")

    # 2. Main Voice Listening & Command Loop
    while True:
        try:
            # Prevent microphone from recording JARVIS's own speaker voice
            while text_to_speech.is_speaking():
                time.sleep(0.1)

            from core.session import get_session_manager
            sm = get_session_manager()
            in_session = sm.is_session_active()

            if ui_instance:
                if in_session:
                    ui_instance.set_state("LISTENING", "Session active: Listening for command...")
                else:
                    ui_instance.set_state("LISTENING", "Listening for 'Jarvis'...")
            
            prompt_str = "[MIC - SESSION ACTIVE] Speak your command:" if in_session else "[MIC - LISTENING] Say 'Jarvis' or 'Leo':"
            print(f"\n{prompt_str}")

            raw_text = speech_to_text.listen_to_user()
            if raw_text:
                detected_res = check_wake_word(raw_text)
                detected, user_command = detected_res
                identity = getattr(detected_res, "identity", "jarvis")

                # Direct Action Command Fast-Pass:
                # If user speaks an actionable command (e.g. "open youtube", "what time is it"),
                # immediately activate and execute even if "Jarvis" or "Leo" was not explicitly spoken!
                if not detected and is_action_command(raw_text):
                    detected = True
                    user_command = raw_text.strip().rstrip(".,!?")

                # Determine target command text based on session state or wake detection
                if not in_session and not detected:
                    # Ignore background chatter/noise when not awakened
                    continue

                if detected and not user_command:
                    # Solitary wake word
                    logger.info(f"[Main] Wake word detected ({identity}). Starting session.")
                    sm.get_or_create_session(activated_by_wake=True)
                    greeting = "Hello Gowtham, what are we working on today?"
                    if ui_instance:
                        ui_instance.set_state("SPEAKING", "Hello Gowtham")
                    text_to_speech.speak(greeting, block=True)
                    time.sleep(0.3)
                    continue

                target_text = user_command if detected and user_command else raw_text

                # Activate/refresh conversational session for this command
                sm.get_or_create_session(activated_by_wake=True)

                # Check for explicit session termination commands
                if sm.check_termination(target_text):
                    if ui_instance:
                        ui_instance.set_state("SPEAKING", "Standing by...")
                    text_to_speech.speak("Standing by, sir. Call my name if you need anything.", block=True)
                    time.sleep(0.3)
                    continue

                # Check for full app shutdown
                if any(w in target_text.lower() for w in ["shutdown jarvis", "power down"]):
                    if ui_instance:
                        ui_instance.set_state("SPEAKING", "Powering down...")
                    text_to_speech.speak("Powering down systems. Good day, sir!", block=True)
                    break

                # Process command through agentic loop
                result = agent_instance.process_input(target_text)
                reply = result.get("response", "Action completed, sir.")

                # Deliver response via speech synchronously so microphone never captures own voice
                text_to_speech.speak(reply, block=True)
                time.sleep(0.3)
            else:
                if ui_instance:
                    if in_session:
                        ui_instance.set_state("LISTENING", "Session open...")
                    else:
                        ui_instance.set_state("IDLE", "Standing by...")
        except Exception as e:
            logger.error(f"[Main Loop Error]: {e}")
            if ui_instance:
                ui_instance.set_state("ERROR", str(e)[:30])
            time.sleep(1)

def main():
    print("==========================================================")
    print("   [JARVIS / LEO] - ADVANCED PERSONAL AI ASSISTANT        ")
    print("==========================================================")
    print(f" - AI Provider   : {config.AI_PROVIDER}")
    print(f" - Model         : {config.DEFAULT_MODEL}")
    print(f" - Voice Engine  : {config.JARVIS_VOICE}")
    print(f" - UI Framework  : {config.UI_FRAMEWORK}")
    print(f" - Local STT     : {config.USE_LOCAL_STT}")
    print("==========================================================")

    # Initialize memory database
    init_db()

    # Initialize agent
    agent_instance = get_agent()
    agent_instance.start()

    # Launch HUD UI Overlay
    ui_instance, app = create_overlay()

    # Run Agent loop in background thread
    t = threading.Thread(target=run_agent_loop, args=(agent_instance, ui_instance), daemon=True)
    t.start()

    # Main UI Event Loop
    if app:
        sys.exit(app.exec())
    elif hasattr(ui_instance, "run"):
        ui_instance.run()

if __name__ == "__main__":
    main()
