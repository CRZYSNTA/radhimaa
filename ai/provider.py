"""
JARVIS V3.0 - AI Provider Abstraction
Defines the standard interface for LLM backends (Gemini, OpenAI, Ollama/Local)
and provides automatic fallback handling.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger("JARVIS.AI")

class AIProvider(ABC):
    """Abstract Base Class for AI intelligence providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if credentials and connectivity are valid."""
        pass

    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Generate a direct text completion."""
        pass

    def stream_text(self, prompt: str, system_prompt: Optional[str] = None):
        """
        Yields text chunks incrementally.
        Default implementation calls generate_text and yields the result.
        """
        result = self.generate_text(prompt, system_prompt)
        if result:
            yield result

    @abstractmethod
    def generate_plan(self, goal: str, available_tools: Dict[str, Any], context: str = "") -> Optional[Dict[str, Any]]:
        """Generate a validated JSON action plan dictionary."""
        pass

    @abstractmethod
    def analyze_image(self, image_bytes: bytes, prompt: str) -> Optional[str]:
        """Analyze an image with multimodal vision."""
        pass

_provider_cache: Dict[str, AIProvider] = {}

def get_ai_provider(provider_type: Optional[str] = None) -> AIProvider:
    """
    Factory function returning the configured or requested AIProvider.
    If the selected provider is unavailable, cascades through available fallbacks:
    Gemini -> OpenAI -> Ollama/Local.
    """
    import config

    requested = (provider_type or config.AI_PROVIDER).lower()
    
    # Lazy imports to prevent circular dependencies
    from ai.gemini_provider import GeminiProvider
    from ai.openai_provider import OpenAIProvider
    from ai.local_provider import LocalProvider

    if requested not in _provider_cache:
        if requested == "gemini":
            _provider_cache["gemini"] = GeminiProvider()
        elif requested == "openai":
            _provider_cache["openai"] = OpenAIProvider()
        elif requested in ("ollama", "local"):
            _provider_cache["ollama"] = LocalProvider()
        else:
            _provider_cache[requested] = GeminiProvider()

    active_provider = _provider_cache.get(requested)
    if active_provider and active_provider.is_available():
        return active_provider

    # Fallback cascade
    fallbacks = [GeminiProvider(), OpenAIProvider(), LocalProvider()]
    for p in fallbacks:
        if p.is_available():
            logger.info(f"[AI] Falling back to available provider: {p.name}")
            return p

    # If none available, return the requested one so errors can be surfaced clearly
    return active_provider or GeminiProvider()
