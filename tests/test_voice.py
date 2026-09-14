"""
Unit tests for Voice and Wake Word.
"""

from voice.wake_word import check_wake_word
from voice import is_speaking

def test_wake_word_detection():
    # Hey Jarvis pattern
    detected, cmd = check_wake_word("Hey Jarvis what time is it")
    assert detected
    assert cmd == "what time is it"

    # Jarvis prefix pattern
    detected, cmd = check_wake_word("jarvis take a screenshot")
    assert detected
    assert cmd == "take a screenshot"

    # Direct name call
    detected, cmd = check_wake_word("jarvis")
    assert detected
    assert cmd == ""

    # Non-wake word utterance
    detected, cmd = check_wake_word("what is the weather today")
    assert not detected
    assert cmd == "what is the weather today"

def test_tts_status():
    assert not is_speaking()

def test_audio_normalization():
    import numpy as np
    from voice.speech_to_text import normalize_audio
    
    # 1. Quiet audio test: amplitude ~2000 should be boosted towards 24000
    quiet = (np.sin(np.linspace(0, 100, 1000)) * 2000).astype(np.int16)
    boosted = normalize_audio(quiet, target_peak=24000.0, max_gain=12.0)
    assert np.max(np.abs(boosted)) > np.max(np.abs(quiet))
    assert np.max(np.abs(boosted)) <= 32767
    
    # 2. Pure silence test: amplitude < 80 should not be amplified
    silence = np.zeros(500, dtype=np.int16)
    assert np.array_equal(normalize_audio(silence), silence)

def test_recognizer_threshold_clamping():
    from voice.speech_to_text import get_recognizer
    rec = get_recognizer()
    assert rec.dynamic_energy_threshold is False
    assert 200 <= rec.energy_threshold <= 900

def test_transcribe_pcm_silence():
    import numpy as np
    from voice.speech_to_text import transcribe_pcm
    silent_pcm = np.zeros(1600, dtype=np.int16).tobytes()
    # Pure silence must quickly return empty string without hanging
    assert transcribe_pcm(silent_pcm) == ""

def test_repetition_hallucination_filter():
    from voice.speech_to_text import is_repetition_hallucination
    # Repetitive loops should be flagged as hallucinations
    assert is_repetition_hallucination("i'm not gonna get you. i'm not gonna get you. i'm not gonna get you.")
    assert is_repetition_hallucination("i'm not a real man. i'm not a real man. i'm not a real man.")
    assert is_repetition_hallucination("thank you thank you thank you")
    assert is_repetition_hallucination("yes yes yes yes")
    
    # Legitimate natural commands must NOT be flagged
    assert not is_repetition_hallucination("turn on the lights and open chrome")
    assert not is_repetition_hallucination("jarvis what is the current weather in new york")
    assert not is_repetition_hallucination("lock my pc and pause music")

def test_microphone_selection_excludes_loopback():
    from voice.speech_to_text import _get_best_mic_index
    import speech_recognition as sr
    best_idx = _get_best_mic_index()
    if best_idx is not None:
        names = sr.Microphone.list_microphone_names()
        selected_name = names[best_idx].lower()
        bad_keywords = ["stereo mix", "wave out", "what u hear", "loopback"]
        assert not any(bad in selected_name for bad in bad_keywords)


