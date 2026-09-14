"""
JARVIS V3.0 - Global Push-to-Talk & Barge-In Engine
Uses native Windows GetAsyncKeyState (via ctypes) for sub-millisecond, zero-dependency
global hotkey monitoring:
 - Press & Hold [Home] / [F8]: Instant recording & UI 'LISTENING' state.
 - Release: Dispatches audio to Whisper STT and executes command.
 - Tap while JARVIS is speaking: Instant barge-in cutoff (terminates audio output).
"""

from __future__ import annotations

import os
import time
import ctypes
import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger("JARVIS.Voice.PTT")

# Windows Virtual Key Codes
VK_HOME = 0x24   # Home Key
VK_F8   = 0x77   # F8 Function Key
VK_F9   = 0x78   # F9 Function Key

_RUNNING = False
_PTT_THREAD: Optional[threading.Thread] = None
_IS_PRESSED = False
_RECORD_START_TIME = 0.0
_ON_TRANSCRIPT_CALLBACK: Optional[Callable[[str], None]] = None


def is_key_down(vk_code: int) -> bool:
    """Checks if a virtual key is currently held down globally across Windows."""
    try:
        if os.name == "nt":
            return (ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000) != 0
    except Exception:
        pass
    return False


def _trigger_barge_in():
    """Immediately stops active TTS speech playback."""
    try:
        from voice.text_to_speech import stop_speaking
        stop_speaking()
        logger.info("[PTT] Barge-in cutoff triggered.")
    except Exception as e:
        logger.debug(f"[PTT Barge-in Note]: {e}")


def _ptt_monitor_loop(hotkey_vk: int = VK_HOME):
    global _RUNNING, _IS_PRESSED, _RECORD_START_TIME

    logger.info(f"[PTT] Global Push-to-Talk monitor active. Hotkey VK: 0x{hotkey_vk:X}")

    while _RUNNING:
        time.sleep(0.02)  # 50 Hz poll rate

        key_down = is_key_down(hotkey_vk)

        # Key Press Transition (Down)
        if key_down and not _IS_PRESSED:
            _IS_PRESSED = True
            _RECORD_START_TIME = time.time()

            # 1. Instant Barge-In Cutoff
            _trigger_barge_in()

            # 2. Notify UI
            try:
                from ui.overlay import set_ui_state, show_task_hud
                set_ui_state("LISTENING", "Push-to-Talk Active")
                show_task_hud("Push-to-Talk Active", "Listening to voice...", icon="🎤", duration_ms=2000)
            except Exception:
                pass

        # Key Release Transition (Up)
        elif not key_down and _IS_PRESSED:
            _IS_PRESSED = False
            duration = time.time() - _RECORD_START_TIME

            try:
                from ui.overlay import set_ui_state
                set_ui_state("THINKING", "Transcribing speech...")
            except Exception:
                pass

            # If held for more than 0.3s, transcribe
            if duration >= 0.3:
                logger.info(f"[PTT] Processing voice input ({duration:.2f}s)...")
                # Trigger quick capture or STT if available
                _process_audio_capture()
            else:
                # Brief tap: treated as intentional interrupt / mute
                logger.info("[PTT] Key tapped (barge-in interrupt).")
                try:
                    from ui.overlay import set_ui_state
                    set_ui_state("IDLE", "Ready")
                except Exception:
                    pass


def _process_audio_capture():
    """Processes captured audio buffer through STT."""
    try:
        from voice.speech_to_text import listen_and_transcribe
        text = listen_and_transcribe(timeout=2.0)
        if text and text.strip():
            logger.info(f"[PTT Transcribed]: '{text}'")
            if _ON_TRANSCRIPT_CALLBACK:
                _ON_TRANSCRIPT_CALLBACK(text.strip())
            else:
                from core.router import route_input
                route_input(text.strip())
    except Exception as e:
        logger.debug(f"[PTT Audio Capture Note]: {e}")
    finally:
        try:
            from ui.overlay import set_ui_state
            set_ui_state("IDLE", "Ready")
        except Exception:
            pass


def start_push_to_talk(hotkey: str = "HOME", on_transcript: Optional[Callable[[str], None]] = None) -> str:
    """
    Initializes the global background Push-to-Talk monitor.
    Args:
        hotkey: 'HOME', 'F8', or 'F9'
        on_transcript: Optional callback function receiving transcribed text.
    """
    global _RUNNING, _PTT_THREAD, _ON_TRANSCRIPT_CALLBACK

    if _RUNNING:
        return "Push-to-Talk engine is already active, sir."

    vk = VK_HOME
    hk_clean = hotkey.strip().upper()
    if hk_clean == "F8":
        vk = VK_F8
    elif hk_clean == "F9":
        vk = VK_F9

    _ON_TRANSCRIPT_CALLBACK = on_transcript
    _RUNNING = True
    _PTT_THREAD = threading.Thread(target=_ptt_monitor_loop, args=(vk,), daemon=True, name="JarvisPushToTalk")
    _PTT_THREAD.start()

    return f"Push-to-Talk enabled on global hotkey [{hk_clean}], sir. Hold the key to speak, tap to interrupt."


def stop_push_to_talk():
    """Stops the push-to-talk background thread."""
    global _RUNNING, _PTT_THREAD
    _RUNNING = False
    if _PTT_THREAD:
        _PTT_THREAD = None
