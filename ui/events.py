"""
JARVIS V3.1 - Centralized UI Event & Task Progress Bus
Thread-safe event system dispatching state and step-level task progress
from background agent threads to the PySide6 HUD.
"""

import time
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("JARVIS.UI.Events")

@dataclass
class TaskStepEvent:
    task_id: str
    step_index: int
    total_steps: int
    step_description: str
    tool_name: str
    status: str = "EXECUTING"  # PENDING, EXECUTING, COMPLETED, FAILED

@dataclass
class AgentStateEvent:
    state: str  # IDLE, LISTENING, THINKING, PLANNING, OBSERVING, EXECUTING, VERIFYING, REPLANNING, SPEAKING, CONFIRMATION_REQUIRED, ERROR
    details: str = ""
    task_step: Optional[TaskStepEvent] = None
    timestamp: float = field(default_factory=time.time)

class EventBus:
    """
    Simple publisher-subscriber event bus for UI decoupled notifications.
    """
    def __init__(self):
        self._listeners: List[Callable[[AgentStateEvent], None]] = []

    def subscribe(self, callback: Callable[[AgentStateEvent], None]):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[AgentStateEvent], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def publish(self, event: AgentStateEvent):
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.debug(f"[EventBus Error]: {e}")

    def emit_state(self, state: str, details: str = "", task_step: Optional[TaskStepEvent] = None):
        evt = AgentStateEvent(state=state, details=details, task_step=task_step)
        self.publish(evt)

_global_event_bus = EventBus()

def get_event_bus() -> EventBus:
    return _global_event_bus


