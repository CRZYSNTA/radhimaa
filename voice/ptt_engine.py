"""
Push-to-Talk Voice Engine for Leo/Jarvis
Monitors the global 'Home' key using pynput, manages explicit processing states:
idle -> listening -> transcribing -> thinking -> speaking
Features instant interruption: new speech or Home press cancels active playback
and invalidates pending generation.
"""

from __future__ import annotations

import io
import time
import wave
import queue
import logging
import threading
import numpy as np
from pathlib import Path
from typing import Optional, Callable

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    keyboard = None
    PYNPUT_AVAILABLE = False

from communication.broadcaster import get_broadcaster
from voice import text_to_speech
from voice import speech_to_text

logger = logging.getLogger("JARVIS.Voice.PTT")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class PushToTalkEngine:
    """
    Global Home-key Push-to-Talk and Audio Pipeline Controller.
    """

    def __init__(self, key_name: str = "home", on_transcript_callback: Optional[Callable[[str], None]] = None):
        self.key_name = key_name.lower()
        self.on_transcript = on_transcript_callback
        self._broadcaster = get_broadcaster()

        self.is_recording = False
        self._held = False
        self._audio_frames = []
        self._audio_stream = None
        self._pa = None

        self._active_generation_id = 0
        self._lock = threading.Lock()

        # Keyboard listener (optional: requires pynput)
        if PYNPUT_AVAILABLE and keyboard is not None:
            self._target_key = keyboard.Key.home if self.key_name == "home" else getattr(keyboard.Key, self.key_name, keyboard.Key.home)
            self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self._listener.daemon = True
            self._listener.start()
            logger.info(f"[PTT] Initialized Push-to-Talk listener on key: {self.key_name}")
        else:
            self._target_key = None
            self._listener = None
            logger.info("[PTT] Optional pynput dependency unavailable; global hotkey hook disabled.")

    def interrupt(self):
        """Immediately interrupts speech playback and invalidates pending synthesis."""
        with self._lock:
            self._active_generation_id += 1
        text_to_speech.stop()
        try:
            from voice.audio_ducking import get_audio_ducker
            get_audio_ducker().restore_now()
        except Exception:
            pass
        self._broadcaster.broadcast_state("IDLE", "Interrupted")
        logger.info("[PTT] Active audio playback interrupted.")

    def _on_press(self, key):
        if key == self._target_key:
            if not self._held:
                self._held = True
                # Interruption: If assistant was speaking, cut it off immediately!
                if text_to_speech.is_speaking():
                    self.interrupt()
                self._start_recording()

    def _on_release(self, key):
        if key == self._target_key:
            if self._held:
                self._held = False
                self._stop_recording_and_process()

    def _start_recording(self):
        if self.is_recording:
            return
        self.is_recording = True
        self._audio_frames = []
        try:
            from voice.audio_ducking import get_audio_ducker
            get_audio_ducker().duck()
        except Exception:
            pass
        self._broadcaster.broadcast_state("LISTENING", "Holding Home key...")
        logger.info("[PTT] State: LISTENING")

        def _record_thread():
            chunk = 1024
            mic_idx = speech_to_text._get_best_mic_index()
            channels = speech_to_text._get_mic_channels(mic_idx)
            rate = 44100 if channels >= 2 else 16000

            if not PYAUDIO_AVAILABLE:
                logger.error("[PTT] PyAudio not available.")
                return

            try:
                pa = pyaudio.PyAudio()
                open_kwargs = {
                    "format": pyaudio.paInt16,
                    "channels": channels,
                    "rate": rate,
                    "input": True,
                    "frames_per_buffer": chunk
                }
                if mic_idx is not None:
                    open_kwargs["input_device_index"] = mic_idx

                stream = pa.open(**open_kwargs)
                while self.is_recording:
                    data = stream.read(chunk, exception_on_overflow=False)
                    self._audio_frames.append(data)

                    # Calculate live volume level (RMS) for 3D Hologram oscilloscope
                    if channels >= 2:
                        raw_arr = np.frombuffer(data, dtype=np.int16).reshape(-1, channels)
                        mono_data = (raw_arr[:, 0].astype(np.int32) + raw_arr[:, 1].astype(np.int32)) // 2
                    else:
                        mono_data = np.frombuffer(data, dtype=np.int16)

                    rms = np.sqrt(np.mean(mono_data.astype(np.float32) ** 2)) if len(mono_data) > 0 else 0
                    normalized_level = min(1.0, float(rms) / 3500.0)
                    self._broadcaster.broadcast_audio_level(normalized_level)

                stream.stop_stream()
                stream.close()
                pa.terminate()
            except Exception as e:
                logger.error(f"[PTT Recording Error]: {e}")

        t = threading.Thread(target=_record_thread, daemon=True)
        t.start()

    def toggle_listening(self):
        """Toggles listening state on/off (e.g. for UI mic button click)."""
        if self.is_recording:
            self._stop_recording_and_process()
        else:
            if text_to_speech.is_speaking():
                self.interrupt()
            self._start_recording()

    def _stop_recording_and_process(self):
        if not self.is_recording:
            return
        self.is_recording = False
        try:
            from voice.audio_ducking import get_audio_ducker
            get_audio_ducker().unduck()
        except Exception:
            pass
        self._broadcaster.broadcast_audio_level(0.0)
        self._broadcaster.broadcast_state("TRANSCRIBING", "Processing speech...")
        logger.info("[PTT] State: TRANSCRIBING")

        # Snapshot current generation id to verify validity upon completion
        with self._lock:
            current_gen = self._active_generation_id

        def _process_audio():
            if not self._audio_frames:
                self._broadcaster.broadcast_state("IDLE", "Standing by")
                return

            mic_idx = speech_to_text._get_best_mic_index()
            channels = speech_to_text._get_mic_channels(mic_idx)
            rate = 44100 if channels >= 2 else 16000

            raw_bytes = b"".join(self._audio_frames)
            if channels >= 2:
                raw_arr = np.frombuffer(raw_bytes, dtype=np.int16).reshape(-1, channels)
                mono_arr = ((raw_arr[:, 0].astype(np.int32) + raw_arr[:, 1].astype(np.int32)) // 2).astype(np.int16)
            else:
                mono_arr = np.frombuffer(raw_bytes, dtype=np.int16)

            # Resample to 16000 Hz if recorded at 44100 Hz
            if rate != 16000 and len(mono_arr) > 1:
                target_samples = int(len(mono_arr) * 16000 / rate)
                if target_samples > 0:
                    pcm_16k = np.interp(
                        np.linspace(0, len(mono_arr), target_samples, endpoint=False),
                        np.arange(len(mono_arr)),
                        mono_arr
                    ).astype(np.int16).tobytes()
                else:
                    pcm_16k = mono_arr.tobytes()
            else:
                pcm_16k = mono_arr.tobytes()

            # Transcribe via Faster-Whisper
            transcript = speech_to_text.transcribe_pcm(pcm_16k, sample_rate=16000)
            transcript = (transcript or "").strip()

            # Check if this turn was superseded by a new press
            with self._lock:
                if current_gen != self._active_generation_id:
                    logger.info("[PTT] Utterance invalidated by newer interaction.")
                    return

            if not transcript:
                logger.info("[PTT] Silence / No speech detected.")
                self._broadcaster.broadcast_state("IDLE", "Standing by")
                return

            logger.info(f"[PTT User Spoke]: '{transcript}'")
            self._broadcaster.broadcast_state("THINKING", transcript[:30])

            # Forward to conversation handler
            if self.on_transcript:
                self.on_transcript(transcript)

        threading.Thread(target=_process_audio, daemon=True).start()


_ptt_instance: Optional[PushToTalkEngine] = None

def get_ptt_engine(on_transcript: Optional[Callable[[str], None]] = None) -> PushToTalkEngine:
    global _ptt_instance
    if _ptt_instance is None:
        _ptt_instance = PushToTalkEngine(key_name="home", on_transcript_callback=on_transcript)
    elif on_transcript:
        _ptt_instance.on_transcript = on_transcript
    return _ptt_instance
