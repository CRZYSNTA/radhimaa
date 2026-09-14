"""
JARVIS Voice Subsystem
Includes faster-whisper STT, Google STT fallback, wake word detection,
neural Edge-TTS, and acoustic double-clap engine.
"""

from voice.speech_to_text import listen_to_user, transcribe_pcm
from voice.text_to_speech import speak, is_speaking
from voice.wake_word import check_wake_word, WakeWordListener, is_action_command
from voice.clap_detection import DualTriggerEngine

__all__ = [
    "listen_to_user",
    "transcribe_pcm",
    "speak",
    "is_speaking",
    "check_wake_word",
    "is_action_command",
    "WakeWordListener",
    "DualTriggerEngine",
]