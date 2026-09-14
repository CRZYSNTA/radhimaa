"""
JARVIS V4 Voice: Text-to-Speech Engine (LEO Full Stack)
Supports:
1. ElevenLabs Adam (pNInz6obpgDQGcFmaJgB / eleven_turbo_v2_5)
2. Microsoft Edge-TTS neural speech (en-GB-RyanNeural) as zero-config fallback
3. Sentence-streaming TTS
4. Real-time signal bus emission (.voice_state: idle, listening, thinking, speaking)
   driving the ai-visualizer living circuit board face on port 8790.
"""

import os
import sys
import time
import json
import queue
import asyncio
import logging
import threading
import requests
from pathlib import Path
from typing import Optional

import edge_tts
import pygame
import config

logger = logging.getLogger("JARVIS.Voice.TTS")

SIGNAL_DIRS = [
    Path("d:/agent/backtalk"),
    Path(config.BASE_DIR),
]



def emit_voice_state(state: str):
    """Emits voice state signal to signal bus for ai-visualizer."""
    for s_dir in SIGNAL_DIRS:
        if s_dir.exists():
            try:
                (s_dir / ".voice_state").write_text(state, encoding="utf-8")
            except Exception:
                pass


import re

def format_speech_text(text: str) -> str:
    """
    Sanitizes and prepares text for speech synthesis according to JARVIS acoustic rules:
    - Strips markdown formatting (headers, bold, backticks, bullets, links)
    - Strips raw URLs
    - Normalizes timestamps and common percentages phonetically
    """
    if not text:
        return ""

    t = text.strip()

    # 1. Remove markdown links [title](url) -> title
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)

    # 2. Remove raw URLs
    t = re.sub(r'https?://\S+', '', t)

    # 3. Strip code blocks and inline backticks
    t = re.sub(r'```[\s\S]*?```', '', t)
    t = re.sub(r'`([^`]+)`', r'\1', t)

    # 4. Strip markdown bold / italics (**bold**, *italic*, __bold__, _italic_)
    t = re.sub(r'[*_]{1,3}([^*_]+)[*_]{1,3}', r'\1', t)

    # 5. Strip markdown headers (# Header) and blockquotes (> Quote)
    t = re.sub(r'^[#>]+\s*', '', t, flags=re.MULTILINE)

    # 6. Strip bullet points and list numbers at line starts
    t = re.sub(r'^\s*[-*+]\s+', '', t, flags=re.MULTILINE)
    t = re.sub(r'^\s*\d+\.\s+', '', t, flags=re.MULTILINE)

    # 7. Convert percentages (e.g., 50% -> 50 percent)
    t = re.sub(r'(\d+)\s*%', r'\1 percent', t)

    # 8. Convert simple 24/12 hr times like 08:30 or 14:00 to words where appropriate
    def _time_sub(m):
        hh = int(m.group(1))
        mm = int(m.group(2))
        words_num = {
            0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
            6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
            11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
            15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen",
            19: "nineteen", 20: "twenty", 30: "thirty", 40: "forty", 50: "fifty"
        }
        h_str = words_num.get(hh, str(hh))
        if mm == 0:
            return f"{h_str} hundred"
        elif mm < 10:
            return f"{h_str} oh {words_num.get(mm, str(mm))}"
        elif mm in words_num:
            return f"{h_str} {words_num[mm]}"
        else:
            tens = (mm // 10) * 10
            units = mm % 10
            return f"{h_str} {words_num.get(tens, '')} {words_num.get(units, '')}".strip()

    t = re.sub(r'\b([01]?\d|2[0-3]):([0-5]\d)\b', _time_sub, t)

    # 9. Collapse multiple whitespace/newlines into clean spaces
    t = re.sub(r'\s+', ' ', t).strip()

    return t


class TTSWorker:
    """Threaded audio output worker handling speech queue with visualizer bus sync."""
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.running = True
        self.is_speaking = False
        self.last_spoke_time = 0.0
        emit_voice_state("idle")
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def enqueue(self, text: str, block: bool = True):
        if not text or not text.strip():
            return
        if block:
            self._speak_sync(text)
        else:
            self.speech_queue.put(text)

    def stop(self):
        """Immediately interrupts playback and drains queued utterances."""
        try:
            while not self.speech_queue.empty():
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
        except Exception:
            pass
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.is_speaking = False
        emit_voice_state("idle")


    def _speak_sync(self, text: str):
        spoken_text = format_speech_text(text)
        if not spoken_text:
            return
        self.is_speaking = True
        emit_voice_state("speaking")
        try:
            from voice.audio_ducking import get_audio_ducker
            get_audio_ducker().duck()
        except Exception:
            pass
        try:
            from communication.broadcaster import get_broadcaster
            get_broadcaster().broadcast_state("SPEAKING", spoken_text[:35])
            get_broadcaster().broadcast_assistant_text(spoken_text)
            get_broadcaster().broadcast_audio_level(0.7)
        except Exception:
            pass
        try:
            print(f"[JARVIS/LEO]: {spoken_text}")
            import tempfile
            audio_file = os.path.join(tempfile.gettempdir(), f"jarvis_speech_{int(time.time()*1000)}.mp3")

            synthesized = False

            # 1. Fish Audio AI (Tier-1) if API key is present
            fish_key = os.environ.get("FISH_AUDIO_API_KEY") or getattr(config, "FISH_AUDIO_API_KEY", "")
            tts_engine = getattr(config, "TTS_ENGINE", "fish_audio").lower()
            if fish_key and tts_engine in ("fish_audio", "fish", "auto"):
                try:
                    url = "https://api.fish.audio/v1/tts"
                    headers = {
                        "Authorization": f"Bearer {fish_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "text": spoken_text,
                        "format": "mp3"
                    }
                    voice_id = os.environ.get("FISH_AUDIO_VOICE_ID") or getattr(config, "FISH_AUDIO_VOICE_ID", "")
                    if voice_id:
                        payload["reference_id"] = voice_id

                    resp = requests.post(url, json=payload, headers=headers, timeout=8)
                    if resp.status_code == 200:
                        with open(audio_file, "wb") as f:
                            f.write(resp.content)
                        synthesized = True
                        logger.info("[TTS] Fish Audio AI voice synthesis succeeded.")
                    elif resp.status_code == 402:
                        logger.warning("[TTS Fish Audio Notice]: Insufficient API credit (HTTP 402). Falling back to secondary engine.")
                    else:
                        logger.warning(f"[TTS Fish Audio Notice]: HTTP {resp.status_code} - {resp.text[:100]}. Falling back.")
                except Exception as e:
                    logger.warning(f"[TTS Fish Audio Notice]: {e}. Falling back.")

            # 2. ElevenLabs Adam (pNInz6obpgDQGcFmaJgB) if API key is present
            if not synthesized:
                el_key = os.environ.get("ELEVENLABS_API_KEY")
                if el_key:
                    try:
                        voice_id = getattr(config, "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
                        model_id = getattr(config, "ELEVENLABS_MODEL", "eleven_turbo_v2_5")
                        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                        headers = {
                            "xi-api-key": el_key,
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "text": spoken_text,
                            "model_id": model_id,
                            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                        }
                        resp = requests.post(url, json=payload, headers=headers, timeout=8)
                        if resp.status_code == 200:
                            with open(audio_file, "wb") as f:
                                f.write(resp.content)
                            synthesized = True
                            logger.info("[TTS] ElevenLabs Adam voice synthesis succeeded.")
                    except Exception as e:
                        logger.warning(f"[TTS ElevenLabs Notice]: {e}")

            # 3. Edge-TTS Neural Fallback (RyanNeural / British cadence)
            if not synthesized:
                voice_name = getattr(config, "JARVIS_VOICE", "en-GB-RyanNeural")
                async def _generate():
                    communicate = edge_tts.Communicate(spoken_text, voice_name)
                    await communicate.save(audio_file)

                asyncio.run(_generate())
                synthesized = os.path.exists(audio_file)

            # Playback via PyGame Mixer
            if synthesized and os.path.exists(audio_file):
                pygame.mixer.init()
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()

                start_t = time.time()
                while pygame.mixer.music.get_busy() and (time.time() - start_t < 25.0):
                    pygame.time.Clock().tick(20)

                pygame.mixer.music.stop()
                pygame.mixer.quit()

                time.sleep(0.05)
                if os.path.exists(audio_file):
                    try:
                        os.remove(audio_file)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"[TTS Error]: {e}")
        finally:
            self.is_speaking = False
            self.last_spoke_time = time.time()
            emit_voice_state("idle")
            try:
                from voice.audio_ducking import get_audio_ducker
                get_audio_ducker().unduck()
            except Exception:
                pass
            try:
                from communication.broadcaster import get_broadcaster
                get_broadcaster().broadcast_audio_level(0.0)
                get_broadcaster().broadcast_state("IDLE", "Standing by.")
            except Exception:
                pass

    def _run(self):
        while self.running:
            try:
                text = self.speech_queue.get(timeout=0.5)
                self._speak_sync(text)
                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[TTS Worker Error]: {e}")


_tts_worker = TTSWorker()


def speak(text: str, block: bool = True):
    """
    Synthesizes neural speech and plays aloud.
    Args:
        text: Utterance text
        block: If True, blocks until audio finishes playing. If False, non-blocking queue.
    """
    _tts_worker.enqueue(text, block=block)


def speak_stream(token_generator):
    """
    Consumes a generator of text chunks, buffers into complete sentences,
    and immediately queues each sentence for TTS playback with sub-second latency.
    """
    buffer = ""
    delimiters = {".", "!", "?", "\n"}

    for chunk in token_generator:
        if not chunk:
            continue
        buffer += chunk
        while any(d in buffer for d in delimiters):
            earliest_idx = min(buffer.find(d) for d in delimiters if d in buffer)
            sentence = buffer[:earliest_idx + 1].strip()
            buffer = buffer[earliest_idx + 1:].lstrip()
            if sentence:
                speak(sentence, block=False)

    if buffer.strip():
        speak(buffer.strip(), block=False)


def is_speaking() -> bool:
    """Returns True if speech output is currently active."""
    return _tts_worker.is_speaking


def stop():
    """Immediately stops speech playback and flushes queued utterances."""
    _tts_worker.stop()

