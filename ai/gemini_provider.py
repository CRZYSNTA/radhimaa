"""
JARVIS V3.0 - Gemini AI Provider
Implements text completion, structured JSON action planning, and multimodal vision
using Google's Gemini REST API with multi-model fallback.
"""

import os
import json
import base64
import logging
import requests
from typing import Dict, Any, Optional, List
from ai.provider import AIProvider
import config

logger = logging.getLogger("JARVIS.AI.Gemini")

class GeminiProvider(AIProvider):
    MODELS = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-flash-latest",
        "gemini-3.5-flash",
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite",
        "gemini-1.5-flash-8b",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")

    @property
    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def _post_contents(self, parts: List[Dict[str, Any]], system_instruction: Optional[str] = None, timeout: int = 12) -> Optional[str]:
        if not self.is_available():
            return None

        for model in self.MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload: Dict[str, Any] = {
                "contents": [{"parts": parts}]
            }
            if system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            try:
                res = requests.post(url, json=payload, timeout=timeout)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        part_list = candidates[0].get("content", {}).get("parts", [])
                        if part_list:
                            return part_list[0].get("text", "").strip()
                elif res.status_code in (400, 403, 404):
                    logger.debug(f"[Gemini] Model {model} returned {res.status_code}: {res.text[:100]}")
                    continue
            except Exception as e:
                logger.debug(f"[Gemini] Error calling model {model}: {e}")
                continue

        return None

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        parts = [{"text": prompt}]
        return self._post_contents(parts, system_instruction=system_prompt)

    def stream_text(self, prompt: str, system_prompt: Optional[str] = None):
        """
        Streams generated text from Gemini API using streamGenerateContent.
        Yields text chunks as they arrive.
        """
        if not self.is_available():
            yield from super().stream_text(prompt, system_prompt)
            return

        parts = [{"text": prompt}]
        yielded = False

        for model in self.MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={self.api_key}&alt=sse"
            payload: Dict[str, Any] = {"contents": [{"parts": parts}]}
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

            try:
                res = requests.post(url, json=payload, stream=True, timeout=12)
                if res.status_code == 200:
                    for line in res.iter_lines():
                        if line:
                            decoded = line.decode("utf-8", errors="ignore").strip()
                            if decoded.startswith("data:"):
                                chunk_json = decoded[5:].strip()
                                try:
                                    data = json.loads(chunk_json)
                                    candidates = data.get("candidates", [])
                                    if candidates:
                                        part_list = candidates[0].get("content", {}).get("parts", [])
                                        for p in part_list:
                                            txt = p.get("text", "")
                                            if txt:
                                                yielded = True
                                                yield txt
                                except Exception:
                                    continue
                    if yielded:
                        return
            except Exception as e:
                logger.debug(f"[Gemini Stream] Error on model {model}: {e}")
                continue

        # Fallback to non-streaming if stream was empty
        if not yielded:
            full = self.generate_text(prompt, system_prompt)
            if full:
                yield full

    def generate_plan(self, goal: str, available_tools: Dict[str, Any], context: str = "") -> Optional[Dict[str, Any]]:
        system_instruction = (
            "You are JARVIS, an autonomous Windows AI assistant. Given a user goal, output ONLY a valid JSON action plan.\n"
            "Do NOT include markdown fences, conversational commentary, or any text other than the JSON object.\n"
            "Structure: {\"goal\": str, \"steps\": [{\"tool\": str, \"params\": dict, \"permission\": \"SAFE\"|\"CONFIRM\"|\"BLOCKED\"}]}\n"
            f"Available tools:\n{json.dumps(available_tools, indent=2)}"
        )
        user_prompt = f"Context: {context}\nGoal: {goal}\nJSON Action Plan:"
        response = self._post_contents([{"text": user_prompt}], system_instruction=system_instruction)
        if not response:
            return None

        # Clean JSON markdown fences if returned
        cleaned = response.strip()
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
            logger.error(f"[Gemini] JSON parse error: {e}. Raw response: {response[:150]}")
            return None

    def analyze_image(self, image_bytes: bytes, prompt: str) -> Optional[str]:
        if not image_bytes:
            return None
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        parts = [
            {
                "text": (
                    "You are JARVIS. Look through the camera frame and answer concisely.\n"
                    "Rules: Two sentences maximum, plain spoken prose, no markdown, no bullet points, positional Sir.\n"
                    f"Question: {prompt}"
                )
            },
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64_image
                }
            }
        ]
        return self._post_contents(parts, timeout=15)

    def analyze_frames(self, frames: List[Any], prompt: str = "Analyze the movement or change across these frames.") -> Optional[str]:
        """
        Multimodal analysis of a temporal sequence of frames (for watch tool).
        frames can be a list of (image_bytes, offset_seconds) or list of image_bytes.
        """
        if not frames:
            return None

        parts: List[Dict[str, Any]] = [
            {
                "text": (
                    "You are JARVIS. Watch this sequence of consecutive camera frames captured over time.\n"
                    "Describe what CHANGED or what action occurred between the frames, rather than merely listing static objects.\n"
                    "Adhere strictly to JARVIS rules: two sentences ceiling, plain spoken prose, no markdown, no bullet points, positional Sir.\n"
                    f"User inquiry: {prompt}"
                )
            }
        ]

        for idx, item in enumerate(frames):
            if isinstance(item, tuple) and len(item) == 2:
                img_bytes, offset = item
                label = f"Frame {idx + 1} (+{offset:.1f}s):"
            elif isinstance(item, dict):
                img_bytes = item.get("bytes")
                offset = item.get("offset", idx * 1.0)
                label = f"Frame {idx + 1} (+{offset:.1f}s):"
            else:
                img_bytes = item
                label = f"Frame {idx + 1}:"

            if not img_bytes:
                continue

            b64_image = base64.b64encode(img_bytes).decode("utf-8")
            parts.append({"text": label})
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64_image
                }
            })

        return self._post_contents(parts, timeout=25)

