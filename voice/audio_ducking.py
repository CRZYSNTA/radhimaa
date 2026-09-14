"""
JARVIS V4 - Background Audio Ducking Subsystem
Ducks background media volume (Spotify, browsers, media players) during
voice interaction (listening and speaking) and restores volume with debouncing.
Extracted and modernized from D:\\agent\\backtalk\\backtalk\\ducking.py.
"""

from __future__ import annotations

import sys
import time
import logging
import threading
from typing import Optional

logger = logging.getLogger("JARVIS.Voice.Ducking")

DEFAULT_DUCK_PERCENT = 0.35  # Duck background to 35% of current
RESTORE_DEBOUNCE_S = 0.6     # Debounce time before restoring volume


class AudioDucker:
    """
    Manages background audio attenuation during assistant speech and listening.
    Thread-safe and debounced so rapid speech chunks do not cause audio pumping.
    """

    def __init__(self, duck_percent: float = DEFAULT_DUCK_PERCENT, debounce_s: float = RESTORE_DEBOUNCE_S):
        self.duck_percent = duck_percent
        self.debounce_s = debounce_s
        self._lock = threading.Lock()
        self._original_volume: Optional[float] = None
        self._is_ducked: bool = False
        self._timer: Optional[threading.Timer] = None

        # Attempt to initialize Windows Core Audio (pycaw) if available
        self._endpoint_volume = None
        self._init_endpoint_volume()

    def _init_endpoint_volume(self):
        """Attempts to bind to Windows master endpoint volume controller."""
        if sys.platform == "win32":
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                speakers = AudioUtilities.GetSpeakers()
                interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self._endpoint_volume = cast(interface, POINTER(IAudioEndpointVolume))
                logger.debug("[AudioDucker] Windows IAudioEndpointVolume bound successfully.")
            except Exception as e:
                logger.debug(f"[AudioDucker] pycaw not available ({e}); using software fallback.")
                self._endpoint_volume = None

    def get_current_volume(self) -> float:
        """Returns current volume as a float between 0.0 and 1.0."""
        if self._endpoint_volume:
            try:
                return float(self._endpoint_volume.GetMasterVolumeLevelScalar())
            except Exception:
                pass
        return 0.75  # Default baseline fallback

    def set_volume(self, level: float) -> None:
        """Sets current master volume between 0.0 and 1.0."""
        level = max(0.0, min(1.0, float(level)))
        if self._endpoint_volume:
            try:
                self._endpoint_volume.SetMasterVolumeLevelScalar(level, None)
                return
            except Exception:
                pass

    def duck(self) -> None:
        """
        Ducks background media volume when speech or listening starts.
        Cancels any pending volume restoration.
        """
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None

            if self._is_ducked:
                return  # Already ducked

            current = self.get_current_volume()
            if current <= 0.15:
                # Volume is already low, do not duck further
                return

            self._original_volume = current
            target = max(0.10, current * self.duck_percent)
            self._is_ducked = True
            self.set_volume(target)
            logger.info(f"[AudioDucker] Ducked audio: {int(current * 100)}% -> {int(target * 100)}%")

    def unduck(self, debounce: Optional[float] = None) -> None:
        """
        Schedules debounced volume restoration.
        If new speech begins within debounce interval, restoration is canceled.
        """
        delay = debounce if debounce is not None else self.debounce_s
        with self._lock:
            if not self._is_ducked or self._original_volume is None:
                return

            if self._timer:
                self._timer.cancel()

            self._timer = threading.Timer(delay, self._restore)
            self._timer.daemon = True
            self._timer.start()

    def _restore(self) -> None:
        """Restores original pre-ducked volume."""
        with self._lock:
            if self._is_ducked and self._original_volume is not None:
                orig = self._original_volume
                self.set_volume(orig)
                logger.info(f"[AudioDucker] Restored audio volume to {int(orig * 100)}%")
                self._original_volume = None
                self._is_ducked = False
            self._timer = None

    def restore_now(self) -> None:
        """Immediate synchronous restoration on shutdown."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None
        self._restore()


_DUCKER_INSTANCE: Optional[AudioDucker] = None
_DUCKER_LOCK = threading.Lock()


def get_audio_ducker() -> AudioDucker:
    """Returns singleton AudioDucker instance."""
    global _DUCKER_INSTANCE
    with _DUCKER_LOCK:
        if _DUCKER_INSTANCE is None:
            _DUCKER_INSTANCE = AudioDucker()
        return _DUCKER_INSTANCE
