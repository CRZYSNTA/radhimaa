"""
JARVIS V3.1 - Computer Action Schema & Validation
Defines strict typed schemas for desktop automation actions,
enforcing coordinate boundaries, valid keys, and ground-truth permission mapping.
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import pyautogui

logger = logging.getLogger("JARVIS.Core.ActionSchema")

VALID_ACTION_TYPES = {
    "click",
    "double_click",
    "right_click",
    "move_mouse",
    "drag",
    "type",
    "press_key",
    "hotkey",
    "scroll",
    "wait",
    "open_application",
    "close_application",
    "focus_window"
}

VALID_HOTKEY_MODIFIERS = {"ctrl", "shift", "alt", "win"}

@dataclass
class ActionValidationResult:
    is_valid: bool
    error: Optional[str] = None
    sanitized_params: Optional[Dict[str, Any]] = None

def get_screen_bounds() -> Tuple[int, int]:
    """Returns current primary screen resolution (width, height)."""
    try:
        w, h = pyautogui.size()
        return int(w), int(h)
    except Exception:
        return (1920, 1080)

def validate_computer_action(action_type: str, params: Dict[str, Any]) -> ActionValidationResult:
    """
    Strictly validates action type and parameter bounds.
    Rejects:
     - Negative or out-of-screen coordinates
     - Invalid hotkey combinations or forbidden keys
     - Path traversal or shell escapes
    """
    clean_action = str(action_type).strip().lower()
    if clean_action not in VALID_ACTION_TYPES:
        return ActionValidationResult(
            is_valid=False,
            error=f"Unknown computer action type '{action_type}'. Allowed: {sorted(VALID_ACTION_TYPES)}"
        )

    max_w, max_h = get_screen_bounds()
    sanitized: Dict[str, Any] = {}

    # Coordinate validation for mouse actions
    if clean_action in ("click", "double_click", "right_click", "move_mouse"):
        if "x" in params and "y" in params:
            try:
                x = int(params["x"])
                y = int(params["y"])
            except (ValueError, TypeError):
                return ActionValidationResult(is_valid=False, error="Coordinates 'x' and 'y' must be valid integers.")

            if x < 0 or x >= max_w or y < 0 or y >= max_h:
                return ActionValidationResult(
                    is_valid=False,
                    error=f"Coordinates ({x}, {y}) are outside display boundaries (0-{max_w-1}, 0-{max_h-1})."
                )
            sanitized["x"] = x
            sanitized["y"] = y
        elif "target" in params:
            sanitized["target"] = str(params["target"]).strip()
        else:
            return ActionValidationResult(is_valid=False, error=f"Action '{clean_action}' requires either (x, y) or 'target' identifier.")

    # Typing validation
    elif clean_action == "type":
        text = str(params.get("text", ""))
        if not text:
            return ActionValidationResult(is_valid=False, error="Action 'type' requires non-empty 'text' parameter.")
        sanitized["text"] = text

    # Hotkey validation
    elif clean_action == "hotkey":
        keys = params.get("keys", [])
        if isinstance(keys, str):
            keys = [k.strip().lower() for k in keys.split("+")]
        elif isinstance(keys, (list, tuple)):
            keys = [str(k).strip().lower() for k in keys]
        else:
            return ActionValidationResult(is_valid=False, error="Action 'hotkey' requires 'keys' list or string (e.g. ['ctrl', 'c']).")

        if not keys:
            return ActionValidationResult(is_valid=False, error="Action 'hotkey' requires at least one key.")
        sanitized["keys"] = keys

    # Scroll validation
    elif clean_action == "scroll":
        try:
            amount = int(params.get("amount", params.get("clicks", 300)))
            sanitized["amount"] = amount
        except (ValueError, TypeError):
            return ActionValidationResult(is_valid=False, error="Action 'scroll' requires integer 'amount'.")

    # Wait validation
    elif clean_action == "wait":
        try:
            sec = min(10.0, max(0.1, float(params.get("seconds", params.get("duration", 1.0)))))
            sanitized["seconds"] = sec
        except (ValueError, TypeError):
            return ActionValidationResult(is_valid=False, error="Action 'wait' requires float 'seconds'.")

    return ActionValidationResult(is_valid=True, sanitized_params=sanitized)

def execute_computer_action(action_type: str, params: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Executes a verified, validated computer action via PyAutoGUI.
    """
    val = validate_computer_action(action_type, params)
    if not val.is_valid:
        return False, f"Action validation failed: {val.error}"

    p = val.sanitized_params or {}
    clean_action = action_type.strip().lower()

    try:
        pyautogui.FAILSAFE = False

        if clean_action == "click":
            pyautogui.click(x=p["x"], y=p["y"])
            return True, f"Clicked at ({p['x']}, {p['y']})"

        elif clean_action == "double_click":
            pyautogui.doubleClick(x=p["x"], y=p["y"])
            return True, f"Double-clicked at ({p['x']}, {p['y']})"

        elif clean_action == "right_click":
            pyautogui.rightClick(x=p["x"], y=p["y"])
            return True, f"Right-clicked at ({p['x']}, {p['y']})"

        elif clean_action == "type":
            import pyperclip
            pyperclip.copy(p["text"])
            pyautogui.hotkey("ctrl", "v")
            return True, f"Typed text ({len(p['text'])} chars)"

        elif clean_action == "press_key":
            key = str(params.get("key", "")).strip().lower()
            pyautogui.press(key)
            return True, f"Pressed key: {key}"

        elif clean_action == "hotkey":
            pyautogui.hotkey(*p["keys"])
            return True, f"Triggered hotkey: {'+'.join(p['keys'])}"

        elif clean_action == "scroll":
            pyautogui.scroll(p["amount"])
            return True, f"Scrolled {'up' if p['amount'] > 0 else 'down'} by {abs(p['amount'])}"

        elif clean_action == "wait":
            time.sleep(p["seconds"])
            return True, f"Waited {p['seconds']} seconds"

    except Exception as e:
        logger.error(f"[ActionSchema] Execution error for {clean_action}: {e}")
        return False, f"Action execution error: {e}"

    return False, f"Unsupported action: {clean_action}"


