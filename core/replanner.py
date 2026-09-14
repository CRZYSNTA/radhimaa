"""
JARVIS V3.0 - Replanning Subsystem
Dynamically formulates alternative action plans when a step fails verification.
Enforces max 2 replan attempts to avoid loops.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from core.planner import ActionPlan, ActionStep, TOOL_REGISTRY
from ai.provider import get_ai_provider

logger = logging.getLogger("JARVIS.Core.Replanner")

MAX_REPLAN_ATTEMPTS = 2

def replan_failed_goal(
    failed_step: ActionStep,
    failure_reason: str,
    goal: str,
    attempt: int = 1
) -> Optional[ActionPlan]:
    """
    Formulates an alternative plan when a step fails verification.
    """
    if attempt > MAX_REPLAN_ATTEMPTS:
        logger.warning(f"[Replanner] Max replan attempts ({MAX_REPLAN_ATTEMPTS}) reached for goal: '{goal}'")
        return None

    logger.info(f"[Replanner] Attempting replan {attempt}/{MAX_REPLAN_ATTEMPTS} for goal: '{goal}'")
    
    context = (
        f"A previous step failed during execution of goal: '{goal}'.\n"
        f"Failed step: tool='{failed_step.tool}', params={failed_step.params}\n"
        f"Failure observation: {failure_reason}\n"
        f"Please provide an alternative, corrected plan using available tools to achieve the goal."
    )

    try:
        provider = get_ai_provider()
        plan_dict = provider.generate_plan(goal=goal, available_tools=TOOL_REGISTRY, context=context)
        if plan_dict and isinstance(plan_dict, dict) and "steps" in plan_dict:
            steps = []
            for s in plan_dict.get("steps", []):
                steps.append(ActionStep(
                    tool=s.get("tool", ""),
                    params=s.get("params", {}),
                    permission=s.get("permission", "SAFE")
                ))
            if steps:
                return ActionPlan(goal=plan_dict.get("goal", goal), steps=steps)
    except Exception as e:
        logger.error(f"[Replanner] Error during replan: {e}")

    return None
