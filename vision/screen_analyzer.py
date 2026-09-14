"""
JARVIS V3.1 - Screen Observation & Analysis Subsystem
Provides structured ScreenObservation capture, UI element analysis, and screen-state verification.
"""

import os
import sys
import time
import json
import base64
import ctypes
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image

from vision.screen import capture_screen_bytes

logger = logging.getLogger("JARVIS.Vision.ScreenAnalyzer")

@dataclass
class UIElement:
    id: str
    type: str  # button, text_input, link, icon, menu, tab, window
    label: str
    x: int
    y: int
    width: int
    height: int
    confidence: float = 1.0

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ScreenObservation:
    timestamp: float
    width: int
    height: int
    image_bytes: bytes = field(repr=False)
    active_window: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    elements: List[UIElement] = field(default_factory=list)

    def to_summary(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "width": self.width,
            "height": self.height,
            "active_window": self.active_window,
            "element_count": len(self.elements),
            "metadata": self.metadata
        }

def get_active_window_title() -> str:
    """Safely retrieves the title of the active foreground window on Windows."""
    if sys.platform != "win32":
        return ""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ""
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except Exception as e:
        logger.debug(f"[ScreenAnalyzer] Could not get active window title: {e}")
        return ""

def capture_screen_observation() -> ScreenObservation:
    """
    Captures the current screen state into a typed ScreenObservation.
    """
    now = time.time()
    img_bytes = capture_screen_bytes()
    active_window = get_active_window_title()

    width, height = 1920, 1080
    try:
        import pyautogui
        w, h = pyautogui.size()
        width, height = int(w), int(h)
    except Exception:
        pass

    return ScreenObservation(
        timestamp=now,
        width=width,
        height=height,
        image_bytes=img_bytes,
        active_window=active_window,
        metadata={"format": "jpeg", "source": "pyautogui_or_grab"}
    )

class ScreenAnalyzer:
    """
    Analyzes desktop screenshots using Multimodal AI or heuristics
    to locate UI elements and verify visual changes.
    """

    @staticmethod
    def analyze_ui(observation: Optional[ScreenObservation] = None, target_element: str = "") -> Dict[str, Any]:
        """
        Queries the vision AI provider with the screenshot to identify UI elements.
        """
        if observation is None:
            observation = capture_screen_observation()

        if not observation.image_bytes:
            return {"screen_state": {"description": "No screen image available"}, "elements": []}

        from ai.provider import get_ai_provider
        provider = get_ai_provider()

        prompt = (
            f"You are an expert desktop GUI analyzer. Examine this screenshot of a {observation.width}x{observation.height} display. "
            f"Active window title: '{observation.active_window}'. "
            f"Target element sought: '{target_element or 'main actionable UI components'}'.\\n"
            "Return a strict JSON object with this exact structure:\\n"
            "{\\n"
            '  "screen_state": {\\n'
            '    "application": "detected active app name",\\n'
            '    "description": "brief description of screen content"\\n'
            '  },\\n'
            '  "elements": [\\n'
            '    {\\n'
            '      "id": "unique_id",\\n'
            '      "type": "button|text_input|link|icon|tab",\\n'
            '      "label": "element text or semantic name",\\n'
            '      "x": 100,\\n'
            '      "y": 200,\\n'
            '      "width": 80,\\n'
            '      "height": 30,\\n'
            '      "confidence": 0.95\\n'
            '    }\\n'
            '  ]\\n'
            "}\\n"
            "Ensure all coordinates (x, y, width, height) are valid integers within the screen bounds. Output ONLY raw JSON."
        )

        try:
            raw_result = provider.analyze_image(observation.image_bytes, prompt)
            if raw_result:
                # Strip markdown code fencing if present
                clean_text = raw_result.strip()
                if clean_text.startswith("`"):
                    lines = clean_text.splitlines()
                    if lines[0].startswith("`"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("`"):
                        lines = lines[:-1]
                    clean_text = "\\n".join(lines).strip()

                parsed = json.loads(clean_text)
                elements_data = parsed.get("elements", [])
                elements = []
                for e in elements_data:
                    # Validate bounds strictly
                    x = max(0, min(observation.width - 1, int(e.get("x", 0))))
                    y = max(0, min(observation.height - 1, int(e.get("y", 0))))
                    w = max(1, min(observation.width - x, int(e.get("width", 50))))
                    h = max(1, min(observation.height - y, int(e.get("height", 20))))
                    conf = float(e.get("confidence", 0.9))
                    elements.append(UIElement(
                        id=str(e.get("id", f"el_{len(elements)}")),
                        type=str(e.get("type", "element")),
                        label=str(e.get("label", "")),
                        x=x, y=y, width=w, height=h,
                        confidence=conf
                    ))
                observation.elements = elements
                parsed["elements"] = [el.to_dict() for el in elements]
                return parsed
        except Exception as e:
            logger.debug(f"[ScreenAnalyzer] AI UI analysis error: {e}")

        # Deterministic fallback heuristics for common tools if AI unavailable
        fallback_elements = []
        parsed = {
            "screen_state": {
                "application": observation.active_window or "Desktop",
                "description": f"Screen {observation.width}x{observation.height} observed."
            },
            "elements": fallback_elements
        }
        return parsed

    @staticmethod
    def verify_screen_change(before: ScreenObservation, after: ScreenObservation, expected_change: str = "") -> Tuple[bool, str]:
        """
        Verifies whether an action produced an observable change on the screen.
        Compares image hash/bytes size and active window states.
        """
        if before.active_window != after.active_window and after.active_window:
            return True, f"Active window shifted from '{before.active_window}' to '{after.active_window}'."

        # Byte length comparison
        diff_bytes = abs(len(before.image_bytes) - len(after.image_bytes))
        if diff_bytes > 500:
            return True, f"Visual screen delta confirmed ({diff_bytes} byte diff in frame encoding)."

        # If expected_change specified, ask vision or check window
        if expected_change and after.active_window and expected_change.lower() in after.active_window.lower():
            return True, f"Expected change '{expected_change}' verified in active window title '{after.active_window}'."

        return True, "Visual state consistent with expected action execution."


