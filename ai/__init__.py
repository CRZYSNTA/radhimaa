"""
JARVIS AI Subsystem
Unified interface for Gemini, OpenAI, and Local (Ollama) providers.
"""

from ai.provider import AIProvider, get_ai_provider
from ai.gemini_provider import GeminiProvider
from ai.openai_provider import OpenAIProvider
from ai.local_provider import LocalProvider

__all__ = [
    "AIProvider",
    "get_ai_provider",
    "GeminiProvider",
    "OpenAIProvider",
    "LocalProvider",
]
