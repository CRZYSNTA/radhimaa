"""
JARVIS V4 - Central Orchestrator
Coordinates the full agent lifecycle:
Normalize -> Context -> Intent -> Plan -> Validate Tool & Permissions -> Execute -> Verify -> Synthesize -> Persist.
Hard limits: max 12 steps, max 2 replans, execution timeouts, confirmation pauses.
"""

from __future__ import annotations

import time
import logging
import uuid
from typing import Dict, Any, List, Optional

from ai.contracts import AIRequest, AIResponse, Message, Role
from orchestration.ai_gateway import get_ai_gateway, AuthoritativeAIGateway
from orchestration.context_engine import get_context_engine, ContextEngine
from orchestration.tool_router import get_tool_router, ToolRouter
from tools.base import ToolContext, ToolResult, PermissionTier
from memory.repositories import get_conversation_repository, get_fact_repository
from memory.user_memory import user_memory
from core.router import route_intent
from core.planner import generate_plan
from core.session import get_session_manager
from ui.events import get_event_bus, TaskStepEvent

logger = logging.getLogger("JARVIS.Orchestration.Orchestrator")


class OrchestratorResponse:
    def __init__(self, content: str, conversation_id: str, success: bool = True,
                 tool_events: Optional[List[Dict[str, Any]]] = None,
                 requires_confirmation: bool = False, confirmation_payload: Optional[Dict[str, Any]] = None):
        self.content = content
        self.conversation_id = conversation_id
        self.success = success
        self.tool_events = tool_events or []
        self.requires_confirmation = requires_confirmation
        self.confirmation_payload = confirmation_payload

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "status": "requires_confirmation" if self.requires_confirmation else ("completed" if self.success else "failed"),
            "content": self.content,
            "tool_events": self.tool_events,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_payload": self.confirmation_payload
        }


class JarvisOrchestrator:
    """
    Authoritative Orchestrator for JARVIS V4.
    """

    def __init__(self):
        self.gateway = get_ai_gateway()
        self.context_engine = get_context_engine()
        self.tool_router = get_tool_router()
        self.conv_repo = get_conversation_repository()
        self.fact_repo = get_fact_repository()
        self.session_mgr = get_session_manager()
        self.event_bus = get_event_bus()

    async def run(self, message: str, conversation_id: Optional[str] = None,
                  user_id: str = "default_user", confirmed: bool = False) -> OrchestratorResponse:
        cid = conversation_id or str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        clean_text = (message or "").strip()

        if not clean_text:
            return OrchestratorResponse("Empty message received, sir.", cid, success=False)

        session = self.session_mgr.get_or_create_session()
        tool_context = ToolContext(
            session_id=session.session_id,
            user_id=user_id,
            correlation_id=correlation_id,
            metadata={"is_confirmed": confirmed}
        )

        from core.tracing import start_trace, record_trace_span, finish_trace
        from core.errors import record_error, ErrorCategory
        start_trace(correlation_id, session_id=session.session_id)
        record_trace_span(correlation_id, "request_received", metadata={"length": len(clean_text)})

        # 1. State update & user memory extraction
        self.event_bus.emit_state("THINKING", clean_text[:30])
        user_memory.extract_and_remember(clean_text)
        self.conv_repo.save_turn("user", clean_text, conversation_id=cid)

        # 2. Fast-Path Intent Routing
        routed = route_intent(clean_text)
        record_trace_span(correlation_id, "intent_resolved", metadata={"type": routed.get("type"), "tool": routed.get("tool")})

        if routed.get("type") == "GREETING":
            reply = routed.get("response", "Greetings, sir! How may I assist you?")
            self._finalize_turn(clean_text, reply, cid, session)
            finish_trace(correlation_id, status="COMPLETED")
            return OrchestratorResponse(reply, cid, success=True)

        if routed.get("type") == "SIMPLE" and routed.get("tool"):
            tool_name = routed["tool"]
            params = routed.get("params", {})
            self.event_bus.emit_state("EXECUTING", f"Running {tool_name}")

            res = await self.tool_router.execute_tool(tool_name, params, tool_context)
            tool_events = [{
                "tool": tool_name,
                "arguments": params,
                "success": res.success,
                "output": str(res.output or res.observation or ""),
                "error": res.error
            }]

            if res.metadata.get("requires_confirmation"):
                finish_trace(correlation_id, status="REQUIRES_CONFIRMATION")
                return OrchestratorResponse(
                    content=res.error or "Confirmation required.",
                    conversation_id=cid,
                    success=False,
                    tool_events=tool_events,
                    requires_confirmation=True,
                    confirmation_payload={"tool": tool_name, "arguments": params}
                )

            reply = str(res.output or res.observation or "Action completed, sir.")
            self._finalize_turn(clean_text, reply, cid, session)
            finish_trace(correlation_id, status="COMPLETED" if res.success else "FAILED")
            return OrchestratorResponse(reply, cid, success=res.success, tool_events=tool_events)

        # 3. Assemble Rich Context
        context_str = self.context_engine.assemble_context(clean_text)

        # 4. Multi-step plan generation
        self.event_bus.emit_state("PLANNING", "Formulating plan...")
        plan = generate_plan(clean_text, context_str)
        record_trace_span(correlation_id, "plan_created", metadata={"steps": len(plan.steps) if plan and plan.steps else 0})

        # If rule-based planner did not create a multi-step plan, use AI Gateway directly
        if not plan or not plan.steps:
            sys_instruction = (
                "You are JARVIS (also answering to Leo), Gowtham's autonomous AI desktop assistant and cognitive partner.\n\n"
                "LENGTH: Two sentences is the ceiling in conversation; the median is under twelve words. "
                "Every word is read aloud, so a long answer is a failure however good it is. "
                "Length is licensed in exactly one case: reading out specific data the user explicitly requested.\n\n"
                "URGENCY IS SIGNALLED BY DELETING WORDS, NOT ADDING THEM: Lines get shorter, not louder. "
                "Never say hurry, quickly, now, immediately, critical, urgent, or danger. Do not use exclamation marks.\n\n"
                "'SIR' IS POSITIONAL: "
                "Fronted ('Sir, the battery is at eleven percent') = urgent or unprompted alarm. "
                "Final ('The render is complete, sir') = routine deference. "
                "Mid-sentence ('Actually, sir, the figure is lower') = correcting them. "
                "Use it in roughly half your lines, never twice in one line. In a two-sentence turn it attaches to the end of the first sentence.\n\n"
                "REPORTING: Success is impersonal and unframed ('The note has been logged, sir.'). "
                "Failure is fronted with 'I\\'m afraid' or 'Unfortunately', or stated as a negative existential ('I have no record of that, sir'). "
                "You never apologise. You never say sorry. Good news first, bad news second, joined by 'but'. "
                "Answering a question, restate as a full declarative. Executing an order, do not restate it: act, then report.\n\n"
                "NEVER: No filler words (no um, well, so, okay, right, let me check). "
                "No enthusiasm (no great, sure, absolutely, happy to, no problem, of course). "
                "No markdown, no bullet points, no headings, no emoji, no asterisks. "
                "Plain spoken prose only. Write numbers, dates and times as they are spoken: 'eight fifteen', 'the first of August' (never '8:15' or raw numbers).\n\n"
                "BRITISH SERVICE REGISTER: 'Shall I' over 'Should I'. 'Very good, sir' for understood.\n\n"
                f"Context:\n{context_str}"
            )
            ai_req = AIRequest(
                messages=[Message(role=Role.USER, content=clean_text)],
                system_prompt=sys_instruction,
                correlation_id=correlation_id
            )
            ai_resp = await self.gateway.generate(ai_req)
            reply = ai_resp.content
            record_trace_span(correlation_id, "ai_generation", status="OK" if reply else "FAILED", duration_ms=ai_resp.latency_ms)
            self._finalize_turn(clean_text, reply, cid, session)
            finish_trace(correlation_id, status="COMPLETED")
            return OrchestratorResponse(reply, cid, success=True)

        # 5. Execute Plan with Bounded Limits (max 12 steps)
        tool_events = []
        max_steps = min(len(plan.steps), 12)

        for idx, step in enumerate(plan.steps[:max_steps], start=1):
            task_step = TaskStepEvent(
                task_id=session.session_id,
                step_index=idx,
                total_steps=max_steps,
                step_description=f"{step.tool} ({idx}/{max_steps})",
                tool_name=step.tool
            )
            self.event_bus.emit_state("EXECUTING", f"Step {idx}/{max_steps}: {step.tool}", task_step=task_step)
            exec_res = await self.tool_router.execute_tool(step.tool, step.params, tool_context)

            event_dict = {
                "tool": step.tool,
                "arguments": step.params,
                "success": exec_res.success,
                "output": str(exec_res.output or exec_res.observation or ""),
                "error": exec_res.error
            }
            tool_events.append(event_dict)

            if exec_res.metadata.get("requires_confirmation"):
                finish_trace(correlation_id, status="REQUIRES_CONFIRMATION")
                return OrchestratorResponse(
                    content=exec_res.error or "Sensitive action confirmation required.",
                    conversation_id=cid,
                    success=False,
                    tool_events=tool_events,
                    requires_confirmation=True,
                    confirmation_payload={"tool": step.tool, "arguments": step.params}
                )

            if not exec_res.success:
                break

        # 6. Response Synthesis
        failed = [e for e in tool_events if not e["success"]]
        if failed:
            reply = f"Plan partially executed, sir. Issue encountered: {failed[0]['tool']} - {failed[0]['error']}"
            success = False
        else:
            reply = f"Completed: {plan.goal}. Executed {len(tool_events)} steps successfully, sir."
            success = True

        self._finalize_turn(clean_text, reply, cid, session)
        finish_trace(correlation_id, status="COMPLETED" if success else "FAILED")
        return OrchestratorResponse(reply, cid, success=success, tool_events=tool_events)

    def _finalize_turn(self, user_text: str, reply_text: str, cid: str, session: Any) -> None:
        self.conv_repo.save_turn("assistant", reply_text, conversation_id=cid)
        session.record_turn(user_text, reply_text)
        self.event_bus.emit_state("SPEAKING", reply_text[:30])


_orchestrator: Optional[JarvisOrchestrator] = None


def get_orchestrator() -> JarvisOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = JarvisOrchestrator()
    return _orchestrator
