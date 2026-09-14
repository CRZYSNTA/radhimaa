"""
JARVIS V3.0 - Proactive Intelligence Engine
Context-aware, time-aware background evaluation for autonomous assistant engagement.
Evaluates user idle time, rotates contextual focus areas, and triggers timely check-ins,
wellbeing reminders, or system briefings without interrupting the user.
"""

from __future__ import annotations

import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("JARVIS.Core.Proactive")


class JarvisProactiveEngine:
    """
    Evaluates when JARVIS should speak unprompted and constructs rich contextual prompts.
    Rotates between focus areas to guarantee non-repetitive interactions.
    """

    def __init__(
        self,
        min_silence_secs: int = 900,  # 15 minutes of user inactivity
        cooldown_secs: int = 1200,    # 20 minutes between proactive prompts
    ):
        self.min_silence_secs = min_silence_secs
        self.cooldown_secs = cooldown_secs
        self._last_triggered: float = 0.0
        self._rotation: int = 0
        self._enabled: bool = True

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    def should_trigger(self, last_user_interaction: float, is_speaking_or_busy: bool = False) -> bool:
        """
        Determines whether conditions are satisfied for a proactive prompt.
        """
        if not self._enabled or is_speaking_or_busy:
            return False

        now = time.monotonic()
        silence_duration = now - last_user_interaction
        cooldown_duration = now - self._last_triggered

        return silence_duration >= self.min_silence_secs and cooldown_duration >= self.cooldown_secs

    def mark_triggered(self):
        """Records trigger timestamp and advances context rotation."""
        self._last_triggered = time.monotonic()
        self._rotation += 1

    def build_proactive_prompt(
        self,
        user_facts: Optional[List[str]] = None,
        active_tasks: Optional[List[str]] = None,
        system_stats: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Builds an adaptive context snapshot for the LLM.
        """
        now = datetime.now()
        hour = now.hour
        time_str = now.strftime("%A, %B %d, %Y - %I:%M %p")

        # Time of day segment
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 17:
            period = "afternoon"
        elif 17 <= hour < 22:
            period = "evening"
        else:
            period = "late night"

        facts_text = "\n".join([f"- {f}" for f in (user_facts or [])]) or "(None stored)"
        tasks_text = ", ".join(active_tasks or []) or "(No pending tasks)"

        # System health note
        sys_str = ""
        if system_stats:
            sys_str = f"CPU: {system_stats.get('cpu_percent', 'N/A')}% | RAM: {system_stats.get('ram_percent', 'N/A')}%"

        # 3-way rotating focus
        focus_idx = self._rotation % 3
        if focus_idx == 0:
            focus = (
                "Focus on the user's active goals or projects if available. "
                "Offer a relevant insight, concise progress check, or ask how something is proceeding."
            )
        elif focus_idx == 1:
            focus = (
                "Focus on the time of day and the user's ergonomics/wellbeing. "
                "Provide a brief, natural check-in, remind them to hydrate or take a short screen break if late."
            )
        else:
            focus = (
                "Focus on proactive assistance or system status. "
                "Mention readiness to assist with upcoming tasks or summarize system stability."
            )

        prompt_lines = [
            "[PROACTIVE_TRIGGER] JARVIS autonomous check-in activated.",
            f"Current Time: {time_str} ({period})",
            f"System Telemetry: {sys_str}",
            f"User Profile & Facts:\n{facts_text}",
            f"Active Schedule / Tasks: {tasks_text}",
            "",
            "Objective:",
            focus,
            "",
            "Constraints:",
            "- Maximum 1 to 2 sentences.",
            "- Sound natural, professional, warm, and loyal (Tony Stark's JARVIS style).",
            "- Do not mention this prompt or internal triggers.",
            "- Do not execute any tool calls.",
            "- If no meaningful intervention is warranted, return empty string.",
        ]

        return "\n".join(prompt_lines)
