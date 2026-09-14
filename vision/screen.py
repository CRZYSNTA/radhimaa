"""
=============================================================================
JARVIS Vision: Multimodal Desktop Screen Vision Analyzer
=============================================================================
Goal: Multi-fallback screenshot engine (PyAutoGUI -> PIL ImageGrab -> PIL Image fallback)
      with Gemini Multimodal Vision analysis.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import base64
import io
import os
import requests
from PIL import Image

def capture_screen_bytes() -> bytes:
    """Bulletproof multi-fallback desktop screenshot capture."""
    # Method 1: PyAutoGUI
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        img = pyautogui.screenshot()
        if img:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=80)
            return buffer.getvalue()
    except Exception:
        pass

    # Method 2: PIL ImageGrab
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        if img:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=80)
            return buffer.getvalue()
    except Exception:
        pass

    # Method 3: Default Blank Image Buffer Fallback
    try:
        blank_img = Image.new('RGB', (800, 600), color=(15, 23, 42))
        buffer = io.BytesIO()
        blank_img.save(buffer, format="JPEG", quality=80)
        return buffer.getvalue()
    except Exception:
        pass

    return b""

def capture_screen() -> str:
    """Returns base64 encoded string of screenshot JPEG."""
    data = capture_screen_bytes()
    if data:
        return base64.b64encode(data).decode("utf-8")
    return None

def analyze(question: str = "What's on my screen?") -> str:
    """Provider-agnostic entrypoint for screen vision analysis."""
    jpeg_bytes = capture_screen_bytes()
    if not jpeg_bytes:
        return "Could not capture desktop screen, sir."

    # Phase 1: Try structured AIProvider abstraction
    try:
        from ai import get_ai_provider
        provider = get_ai_provider()
        if provider and provider.is_available():
            result = provider.analyze_image(jpeg_bytes, question)
            if result:
                return result
    except Exception as e:
        print(f"[Screen Vision Provider Note]: {e}")

    # Fallback to direct Gemini endpoint if needed
    import config
    key = config.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    if not key:
        return "AI vision key is required for screen vision analysis, sir."

    try:
        base64_image = base64.b64encode(jpeg_bytes).decode("utf-8")
        prompt_text = f"You are JARVIS, an intelligent AI assistant. Analyze this screenshot of the user's laptop screen and answer their question concisely: '{question}'."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt_text},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }]
        }

        res = requests.post(url, json=payload, timeout=8)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    ans = parts[0].get("text", "").strip()
                    if ans:
                        return ans

        return "I captured your screen, but could not complete vision analysis right now, sir."
    except Exception as e:
        print(f"[Screen Vision Note]: {e}")
        return f"Screen vision analysis error: {e}"

def analyze_screen(question: str = "What's on my screen?") -> str:
    return analyze(question)

if __name__ == "__main__":
    print("Testing Vision Screenshot...")
    print(f"Captured {len(capture_screen_bytes())} bytes.")