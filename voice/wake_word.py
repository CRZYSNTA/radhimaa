"""
JARVIS V3.0 - Wake Word Detection Engine
Detects local wake word activation ("Jarvis") and separates wake word from commands.
"""

import re
import time
import threading
import logging
from typing import Optional, Callable, Tuple
import config

logger = logging.getLogger("JARVIS.Voice.WakeWord")

class WakeWordResult(tuple):
    """2-tuple (detected, command) maintaining backward compatibility with optional identity."""
    def __new__(cls, detected: bool, command: str, identity: str = "jarvis"):
        instance = super().__new__(cls, (detected, command))
        instance.identity = identity
        return instance

WAKE_WORD_ALIASES = {
    "jarvis": [
        "jarvis", "service", "travis", "harvest", "javis", "jarv",
        "jarvish", "darvis", "garvis", "tarvis", "charles", "starbucks",
        "jawa", "jarviss"
    ],
    "leo": [
        "leo", "lio", "cleo", "leos", "leeo", "neo"
    ]
}

ACTION_STARTERS = (
    "open ", "launch ", "start ", "run ", "close ", "kill ", "stop ",
    "play ", "pause ", "resume ", "mute ", "unmute ", "volume ",
    "search ", "google ", "find ", "look up ", "browse ",
    "take a screenshot", "take screenshot", "screenshot", "capture screen",
    "lock screen", "lock pc", "lock laptop", "lock computer",
    "what ", "who ", "where ", "when ", "how ", "why ",
    "tell me ", "calculate ", "remind ", "remember ", "forget ",
    "type ", "click ", "press ", "scroll ", "switch ", "minimize ", "maximize "
)

def is_action_command(text: str) -> bool:
    """
    Returns True if utterance expresses an explicit, actionable command
    (e.g., 'open youtube', 'volume up', 'take a screenshot') even without wake word.
    """
    if not text:
        return False
    clean = text.strip().lower().rstrip(".,!?")
    if any(clean.startswith(prefix) for prefix in ACTION_STARTERS):
        return True
    
    # Check simple direct router patterns
    try:
        from core.router import route_intent
        routed = route_intent(clean)
        if routed.get("type") in ("SIMPLE", "GREETING"):
            return True
    except Exception:
        pass

    return False

def check_wake_word(text: str, wake_word: Optional[str] = None) -> Tuple[bool, str]:
    """
    Checks if speech text begins or contains the wake word or phonetic variants.
    Supports both 'jarvis' and 'leo' identities seamlessly.
    Returns (detected: bool, command_stripped: str) with .identity attribute.
    """
    if not text:
        return WakeWordResult(False, "", "jarvis")
    
    clean = text.strip().lower().rstrip(".,!?")

    # If specific wake_word requested, check only that group
    if wake_word:
        target_groups = [(wake_word.strip().lower(), WAKE_WORD_ALIASES.get(wake_word.strip().lower(), [wake_word.strip().lower()]))]
    else:
        # Check both LEO and JARVIS
        target_groups = [
            ("leo", WAKE_WORD_ALIASES["leo"]),
            ("jarvis", WAKE_WORD_ALIASES["jarvis"])
        ]

    for identity, aliases in target_groups:
        targets = [identity] + [a for a in aliases if a != identity]
        for t in targets:
            # Pattern: "hey leo ...", "ok jarvis ...", "leo ..."
            pattern = rf"^(?:hey\s+|ok\s+|hello\s+)?{re.escape(t)}[\s,:\.!-]+(.*)$"
            match = re.search(pattern, clean)
            if match:
                return WakeWordResult(True, match.group(1).strip(), identity)
            
            # Direct single wake word
            if clean == t:
                return WakeWordResult(True, "", identity)
            if clean.startswith(t + " "):
                return WakeWordResult(True, clean[len(t):].strip(), identity)

            # Fallback: wake word mentioned in utterance
            words = clean.split()
            if t in words:
                parts = clean.split(t, 1)
                return WakeWordResult(True, parts[1].strip(" ,:.!-"), identity)

    return WakeWordResult(False, text.strip(), "jarvis")

class WakeWordListener:
    """Continuous background listener for wake word."""

    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        self.callback = callback
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("[WakeWord] Background listener started.")

    def stop(self):
        self.running = False
        logger.info("[WakeWord] Background listener stopped.")

    def _loop(self):
        from voice.speech_to_text import listen_to_user
        while self.running:
            try:
                text = listen_to_user()
                if text:
                    detected, command = check_wake_word(text)
                    if detected:
                        logger.info(f"[WakeWord] Wake word detected! Command: '{command}'")
                        if self.callback:
                            self.callback(command)
                time.sleep(0.3)
            except Exception as e:
                logger.error(f"[WakeWord] Listener loop error: {e}")
                time.sleep(1.0)
