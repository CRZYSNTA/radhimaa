"""
JARVIS V3.0 Core Agent - Autonomous Orchestrator Loop
Manages Observe -> Plan -> Execute -> Verify -> Replan loop with
persistent memory, authoritative permissions, and multimodal capabilities.
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, List

from core.planner import generate_plan, ActionPlan, ActionStep
from core.executor import ToolExecutor, ExecutionResult
from core.context import ConversationMemory, get_memory
from core.replanner import replan_failed_goal
from memory.user_memory import user_memory
import config

logger = logging.getLogger("JARVIS.Core.Agent")

class JarvisAgent:
    def __init__(self, 
                 ai_provider: Optional[str] = None,
                 ai_model: Optional[str] = None,
                 confirm_callback: Optional[callable] = None):
        self.ai_provider = ai_provider or getattr(config, "AI_PROVIDER", "gemini")
        self.ai_model = ai_model or getattr(config, "DEFAULT_MODEL", "gemini-1.5-flash-8b")
        self.executor = ToolExecutor(confirm_callback)
        self.memory = get_memory()
        self.running = False
        
        os.environ["AI_PROVIDER"] = self.ai_provider
        os.environ["DEFAULT_MODEL"] = self.ai_model

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Core Observe -> Plan -> Execute -> Verify -> Replan pipeline."""
        if not user_input or not user_input.strip():
            return {"success": False, "response": "Empty input received, sir.", "plan": None, "results": []}

        # 1. Session tracking & fact extraction heuristic
        from core.session import get_session_manager
        sm = get_session_manager()
        session = sm.get_or_create_session()

        from ui.events import get_event_bus, TaskStepEvent
        event_bus = get_event_bus()
        event_bus.emit_state("THINKING", user_input[:30])

        user_memory.extract_and_remember(user_input)
        self.memory.add_message("user", user_input)

        # 2. Fast-Path Intent Router (<0.05s response for common tools and greetings)
        from core.router import route_intent
        routed = route_intent(user_input)

        if routed.get("type") == "GREETING":
            reply = routed.get("response", "Greetings, sir!")
            self.memory.add_message("assistant", reply)
            session.record_turn(user_input, reply)
            event_bus.emit_state("SPEAKING", reply[:30])
            return {"success": True, "response": reply, "plan": None, "results": []}

        if routed.get("type") == "CONVERSATION":
            reply = routed.get("response")
            if not reply:
                reply = self._fallback_response(user_input)
            self.memory.add_message("assistant", reply)
            session.record_turn(user_input, reply)
            event_bus.emit_state("SPEAKING", reply[:30])
            return {"success": True, "response": reply, "plan": None, "results": []}

        if routed.get("type") == "SIMPLE" and routed.get("tool"):
            tool_name = routed["tool"]
            params = routed.get("params", {})
            event_bus.emit_state("EXECUTING", f"Running {tool_name}")
            exec_res = self.executor.execute_step(tool_name, params, "SAFE", goal=user_input)
            reply = str(exec_res.output or exec_res.observation or "Action completed, sir.")
            self.memory.add_message("assistant", reply)
            session.record_turn(user_input, reply)
            event_bus.emit_state("SPEAKING", reply[:30])
            return {
                "success": exec_res.success,
                "response": reply,
                "plan": {"goal": user_input, "steps": [{"tool": tool_name, "params": params}]},
                "results": [{"tool": tool_name, "success": exec_res.success, "output": exec_res.output, "error": exec_res.error}]
            }

        # 3. Complex Multi-Step Path: Build context including active session memory
        event_bus.emit_state("PLANNING", "Formulating action plan...")
        session_ctx = sm.get_context()
        context = self.memory.get_context_string()
        if session_ctx:
            context += f"\nCurrent Session Context: {session_ctx}"

        plan = generate_plan(user_input, context)

        if not plan:
            fallback = self._fallback_response(user_input)
            self.memory.add_message("assistant", fallback)
            session.record_turn(user_input, fallback)
            event_bus.emit_state("SPEAKING", fallback[:30])
            return {"success": True, "response": fallback, "plan": None, "results": []}

        self.memory.add_goal(plan.goal)

        # 4. Execute plan with step verification and live HUD task updates
        results = []
        total_steps = len(plan.steps)
        for idx, step in enumerate(plan.steps, start=1):
            task_step = TaskStepEvent(
                task_id=session.session_id,
                step_index=idx,
                total_steps=total_steps,
                step_description=f"{step.tool} ({idx}/{total_steps})",
                tool_name=step.tool
            )
            event_bus.emit_state("EXECUTING", f"Step {idx}/{total_steps}: {step.tool}", task_step=task_step)
            exec_res = self.executor.execute_step(step.tool, step.params, step.permission, goal=plan.goal)
            
            event_bus.emit_state("VERIFYING", f"Verifying {step.tool}...")
            step_dict = {
                "tool": step.tool,
                "params": step.params,
                "success": exec_res.success,
                "output": exec_res.output,
                "error": exec_res.error,
                "observation": exec_res.observation
            }
            results.append(step_dict)
            if not exec_res.success:
                break

        failed_steps = [r for r in results if not r["success"]]

        # 5. Replanning Loop if a step failed
        if failed_steps:
            failed_info = failed_steps[0]
            failed_step_obj = ActionStep(
                tool=failed_info["tool"],
                params=failed_info["params"],
                permission="SAFE"
            )
            event_bus.emit_state("REPLANNING", f"Replanning {failed_info['tool']}...")
            logger.info(f"[Agent] Step {failed_info['tool']} failed. Initiating replanner...")
            replan = replan_failed_goal(
                failed_step=failed_step_obj,
                failure_reason=failed_info.get("error", "Verification failed"),
                goal=plan.goal,
                attempt=1
            )
            if replan:
                event_bus.emit_state("EXECUTING", f"Executing revised plan ({len(replan.steps)} steps)")
                logger.info(f"[Agent] Revised plan formulated with {len(replan.steps)} steps. Executing...")
                replan_results = self.executor.execute_plan(replan)
                results.extend(replan_results)
                failed_steps = [r for r in replan_results if not r["success"]]

        successful_steps = [r for r in results if r["success"]]

        if failed_steps:
            response = f"Plan partially executed. Issue encountered: {failed_steps[0]['tool']} - {failed_steps[0]['error']}"
        else:
            outputs = [str(r.get("output") or r.get("observation") or "").strip() for r in results if r.get("output") or r.get("observation")]
            valid_outputs = [o for o in outputs if o and not any(k in o.lower() for k in ("action completed", "true", "none", "null", "{}"))]
            if len(results) == 1 and valid_outputs:
                response = valid_outputs[0]
            else:
                response = f"Completed: {plan.goal}. Successfully executed {len(successful_steps)} steps, sir."
            self.memory.complete_goal(plan.goal)

        self.memory.add_message("assistant", response)
        session.record_turn(user_input, response)
        event_bus.emit_state("SPEAKING", response[:30])

        return {
            "success": len(failed_steps) == 0,
            "response": response,
            "plan": plan.to_dict() if plan else None,
            "results": results
        }

    def _fallback_response(self, user_input: str) -> str:
        q = user_input.lower()
        if "time" in q and "timer" not in q:
            from tools.computer import get_time
            return get_time()
        if "date" in q:
            from tools.computer import get_date
            return get_date()
        if "weather" in q:
            from tools.web import get_weather
            return get_weather("")
        if "news" in q:
            from tools.web import get_news
            return get_news()

        # Query unified conversational AI brain with LEO / JARVIS persona
        try:
            from server import process_query_with_brain
            reply = process_query_with_brain(user_input)
            if reply and not reply.startswith("I received an empty") and "unreachable" not in reply:
                return reply
        except Exception:
            pass

        try:
            from server import fetch_ai_brain_reply
            reply = fetch_ai_brain_reply(user_input)
            if reply and not reply.startswith("I received an empty"):
                return reply
        except Exception:
            pass

        return f"Standing by on your request: '{user_input}', sir."

    def process_voice_command(self, text: str) -> Dict[str, Any]:
        return self.process_input(text)

    def process_request(self, user_query: str) -> str:
        res = self.process_input(user_query)
        if isinstance(res, dict):
            return res.get("response", str(res))
        return str(res)

    def process_vision_query(self, question: str) -> Dict[str, Any]:
        from vision.screen import analyze_screen
        result = analyze_screen(question)
        self.memory.add_message("user", f"[Vision] {question}")
        self.memory.add_message("assistant", result)
        return {"success": True, "response": result, "plan": None, "results": []}

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model,
            "memory_facts": len(self.memory.facts),
            "active_goals": self.memory.session_goals,
            "history_length": len(self.memory.history),
            "registered_tools": list(self.executor.tools.keys())
        }

    def start(self):
        self.running = True
        logger.info("[Agent] JARVIS Agent started")

    def process_instruction(self, instruction: str) -> Dict[str, Any]:
        """Bridge compatibility method: executes instruction and returns normalized keys."""
        res = self.process_input(instruction)
        actions = []
        for r in res.get("results", []):
            if isinstance(r, dict) and "tool" in r:
                actions.append(r["tool"])
        return {
            "success": res.get("success", True),
            "reply": res.get("response", ""),
            "response": res.get("response", ""),
            "actions": actions,
            "plan": res.get("plan"),
            "results": res.get("results", [])
        }

    def stop(self):
        self.running = False
        logger.info("[Agent] JARVIS Agent stopped")

# Backward compatibility and alternative naming aliases
JARVISAgent = JarvisAgent

_global_agent: Optional[JarvisAgent] = None

def get_agent() -> JarvisAgent:
    global _global_agent
    if _global_agent is None:
        _global_agent = JarvisAgent(config.AI_PROVIDER, config.DEFAULT_MODEL)
    return _global_agent

if __name__ == "__main__":
    agent = get_agent()
    agent.start()
    test_queries = [
        "What time is it?",
        "Remember that my name is Tony",
        "What is my name?",
    ]
    for tq in test_queries:
        print(f"\n>>> Input: {tq}")
        res = agent.process_input(tq)
        print("Response:", res.get("response"))