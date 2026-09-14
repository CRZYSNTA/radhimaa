"""
Unit tests for Push-to-Talk voice engine and interruption mechanics.
"""

from voice.ptt_engine import PushToTalkEngine
from voice import text_to_speech


def test_ptt_interruption_stops_playback():
    engine = PushToTalkEngine(key_name="home")
    initial_gen = engine._active_generation_id

    # Trigger interrupt
    engine.interrupt()

    # Verify generation id incremented (invalidating pending responses)
    assert engine._active_generation_id == initial_gen + 1
    # Verify playback stopped
    assert text_to_speech.is_speaking() is False


def test_ptt_key_resolution():
    engine = PushToTalkEngine(key_name="home")
    assert engine.key_name == "home"
    assert engine.is_recording is False
