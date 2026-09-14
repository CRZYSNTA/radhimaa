"""
JARVIS V4 - Authoritative AI Gateway
Unifies all model interactions behind a single authoritative gateway.
Eliminates divergent AI brains across desktop, API, and mobile callers.
"""

from __future__ import annotations

import time
import logging
from typing import List, Dict, Any, Optional, AsyncIterator

from ai.contracts import AIRequest, AIResponse, Message, Role, TokenUsage, ToolCall
from config_v4.settings import get_settings

logger = logging.getLogger("JARVIS.Orchestration.AIGateway")


class AuthoritativeAIGateway:
    """
    Authoritative AI Gateway implementation.
    Routes requests through configured providers with cascading fallbacks,
    latency tracking, correlation ID preservation, and error normalization.
    """

    def __init__(self):
        self.settings = get_settings()

    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.perf_counter()
        correlation_id = request.correlation_id

        # 1. Prepare prompt and conversation text
        system_prompt = request.system_prompt or "You are JARVIS, an authoritative and polite AI assistant."
        messages = request.messages

        last_user_message = ""
        for m in reversed(messages):
            if str(m.role).lower() in ("user", "role.user"):
                last_user_message = m.content
                break

        if not last_user_message and messages:
            last_user_message = messages[-1].content

        # 2. Provider selection and fallback cascade
        from ai.provider import get_ai_provider

        preferred_provider_type = request.model or self.settings.ai.provider
        # If user passed a model name like 'gemini-1.5-flash', treat provider as gemini
        if "gemini" in preferred_provider_type.lower():
            provider_type = "gemini"
        elif "gpt" in preferred_provider_type.lower() or "openai" in preferred_provider_type.lower():
            provider_type = "openai"
        elif "ollama" in preferred_provider_type.lower() or "local" in preferred_provider_type.lower():
            provider_type = "ollama"
        else:
            provider_type = self.settings.ai.provider

        provider = get_ai_provider(provider_type)
        provider_name = provider.name if provider else "unknown"

        content = None
        error_msg = None

        if provider and provider.is_available():
            try:
                # Format full context if multiple messages
                if len(messages) > 1:
                    full_context = "\n".join([f"{m.role}: {m.content}" for m in messages[:-1]])
                    prompt_text = f"Context:\n{full_context}\n\nUser: {last_user_message}"
                else:
                    prompt_text = last_user_message

                content = provider.generate_text(prompt_text, system_prompt=system_prompt)
            except Exception as e:
                logger.warning(f"[AIGateway] Provider '{provider_name}' raised error: {e}. Trying fallback cascade...")
                error_msg = str(e)

        # Fallback if primary returned nothing
        if not content:
            from ai.gemini_provider import GeminiProvider
            from ai.openai_provider import OpenAIProvider
            from ai.local_provider import LocalProvider

            fallbacks = [GeminiProvider(), OpenAIProvider(), LocalProvider()]
            for fb in fallbacks:
                if fb.is_available() and fb.name != provider_name:
                    try:
                        logger.info(f"[AIGateway] Attempting fallback provider: {fb.name}")
                        content = fb.generate_text(last_user_message, system_prompt=system_prompt)
                        if content:
                            provider_name = fb.name
                            break
                    except Exception as fb_err:
                        logger.debug(f"[AIGateway] Fallback {fb.name} failed: {fb_err}")

        # Final safe fallback response if all AI models are unreachable
        if not content:
            content = f"I processed your request, sir. All external AI models are currently unreachable. Standing by."
            provider_name = "system_fallback"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return AIResponse(
            content=content,
            model=request.model or self.settings.ai.default_model,
            provider=provider_name,
            latency_ms=round(elapsed_ms, 2),
            correlation_id=correlation_id,
            usage=TokenUsage(
                prompt_tokens=len(last_user_message) // 4,
                completion_tokens=len(content) // 4,
                total_tokens=(len(last_user_message) + len(content)) // 4
            )
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        response = await self.generate(request)
        yield response.content

    async def embed(self, texts: List[str]) -> List[List[float]]:
        # Lightweight zero-dependency fallback vector embedding (deterministic hash-based)
        # Replaced by pgvector / true embedding model in Phase 2
        embeddings = []
        for text in texts:
            vec = [float((hash(text + str(i)) % 1000) / 1000.0) for i in range(128)]
            embeddings.append(vec)
        return embeddings


_gateway_instance: Optional[AuthoritativeAIGateway] = None


def get_ai_gateway() -> AuthoritativeAIGateway:
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = AuthoritativeAIGateway()
    return _gateway_instance
