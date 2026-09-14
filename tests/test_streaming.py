"""
Unit and integration tests for Streaming AI and Streaming TTS (JARVIS V3.1).
"""

import pytest
from ai.provider import get_ai_provider
from voice.text_to_speech import speak_stream

def test_ai_provider_stream_interface():
    provider = get_ai_provider()
    assert hasattr(provider, "stream_text")

def test_speak_stream_sentence_buffering(monkeypatch):
    enqueued_sentences = []
    from voice import text_to_speech
    monkeypatch.setattr(text_to_speech._tts_worker, "enqueue", lambda text, block=False: enqueued_sentences.append(text))

    def token_stream():
        yield "Good "
        yield "evening, sir! "
        yield "All systems are functioning "
        yield "at peak efficiency. "
        yield "Standing by for orders."

    speak_stream(token_stream())
    assert len(enqueued_sentences) >= 2
    assert "Good evening, sir!" in enqueued_sentences[0]

