"""
JARVIS V3.0 - OpenAI AI Provider
Implements text completion, structured JSON action planning, and multimodal vision
using OpenAI's API (gpt-4o-mini / gpt-4o).
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional, List
from ai.provider import AIProvider
import config

logger = logging.getLogger("JARVIS.AI.OpenAI")

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        self.model = "gpt-4o-mini"
        self._client = None

    @property
    def name(self) -> str:
        return "openai"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("sk-") and len(self.api_key) > 20)

    def _get_client(self):
        if self._client is None and self.is_available():
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.error(f"[OpenAI] Client init error: {e}")
        return self._client

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        client = self._get_client()
        if not client:
            return None
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"[OpenAI] generate_text failed: {e}")
            return None

    def generate_plan(self, goal: str, available_tools: Dict[str, Any], context: str = "") -> Optional[Dict[str, Any]]:
        client = self._get_client()
        if not client:
            return None
        try:
            system_prompt = (
                "You are JARVIS, an autonomous Windows AI assistant. Given a user goal, output ONLY a valid JSON action plan.\n"
                "Do NOT include markdown formatting or commentary.\n"
                "Format: {\"goal\": str, \"steps\": [{\"tool\": str, \"params\": dict, \"permission\": \"SAFE\"|\"CONFIRM\"|\"BLOCKED\"}]}\n"
                f"Available tools:\n{json.dumps(available_tools, indent=2)}"
            )
            user_content = f"Context: {context}\nGoal: {goal}\nJSON Action Plan:"
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content.strip()
            return json.loads(raw)
        except Exception as e:
            logger.error(f"[OpenAI] generate_plan failed: {e}")
            return None

    def analyze_image(self, image_bytes: bytes, prompt: str) -> Optional[str]:
        client = self._get_client()
        if not client or not image_bytes:
            return None
        try:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"You are JARVIS. Analyze this image concisely: {prompt}"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                        }
                    ]
                }
            ]
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"[OpenAI] analyze_image failed: {e}")
            return None
