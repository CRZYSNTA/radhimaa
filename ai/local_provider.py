"""
JARVIS V3.0 - Local / Ollama AI Provider
Provides offline, local LLM support via Ollama REST API.
"""

import os
import json
import base64
import logging
import requests
from typing import Dict, Any, Optional, List
from ai.provider import AIProvider
import config

logger = logging.getLogger("JARVIS.AI.Local")

class LocalProvider(AIProvider):
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or config.OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")
        self.model = model or config.DEFAULT_MODEL or "llama3.2:1b"

    @property
    def name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        """Check if local Ollama server is running."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=1.5)
            return res.status_code == 200
        except Exception:
            return False

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        try:
            url = f"{self.base_url}/api/generate"
            payload: Dict[str, Any] = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            if system_prompt:
                payload["system"] = system_prompt
            res = requests.post(url, json=payload, timeout=20)
            if res.status_code == 200:
                return res.json().get("response", "").strip()
        except Exception as e:
            logger.debug(f"[Ollama] generate_text error: {e}")
        return None

    def generate_plan(self, goal: str, available_tools: Dict[str, Any], context: str = "") -> Optional[Dict[str, Any]]:
        system = (
            "You are JARVIS, an autonomous Windows AI assistant. Given a user goal, output ONLY a valid JSON action plan.\n"
            "Format: {\"goal\": str, \"steps\": [{\"tool\": str, \"params\": dict, \"permission\": \"SAFE\"|\"CONFIRM\"|\"BLOCKED\"}]}\n"
            f"Available tools:\n{json.dumps(available_tools, indent=2)}"
        )
        prompt = f"Context: {context}\nGoal: {goal}\nJSON Action Plan:"
        raw = self.generate_text(prompt, system_prompt=system)
        if not raw:
            return None
        
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"[Ollama] JSON parse error: {e}")
            return None

    def analyze_image(self, image_bytes: bytes, prompt: str) -> Optional[str]:
        if not image_bytes:
            return None
        try:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": "moondream" if "moondream" in self.model else "llava",
                "prompt": f"Analyze this image: {prompt}",
                "images": [b64_image],
                "stream": False
            }
            res = requests.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                return res.json().get("response", "").strip()
        except Exception as e:
            logger.debug(f"[Ollama] Vision analysis error: {e}")
        return "Local vision model unavailable."
