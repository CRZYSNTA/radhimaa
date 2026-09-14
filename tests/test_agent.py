"""
Unit tests for JarvisAgent and Replanning pipeline.
"""

from core.agent import JarvisAgent
from core.planner import ActionPlan, ActionStep
from core.executor import ToolExecutor

def test_agent_initialization():
    agent = JarvisAgent()
    status = agent.get_status()
    assert "registered_tools" in status
    assert "volume_set" in status["registered_tools"]
    assert "get_system_stats" in status["registered_tools"]

def test_executor_safe_step():
    executor = ToolExecutor()
    res = executor.execute_step("get_time", {}, "SAFE")
    assert res.success
    assert "current time is" in str(res.output).lower()

def test_executor_blocked_step():
    executor = ToolExecutor()
    res = executor.execute_step("run_shell_cmd", {"cmd": "dir"}, "SAFE")
    assert not res.success
    assert "blocked" in res.error.lower()

def test_agent_plan_execution():
    agent = JarvisAgent()
    plan = ActionPlan(
        goal="check time and date",
        steps=[
            ActionStep(tool="get_time", params={}, permission="SAFE"),
            ActionStep(tool="get_date", params={}, permission="SAFE"),
        ]
    )
    results = agent.executor.execute_plan(plan)
    assert len(results) == 2
    assert all(r["success"] for r in results)
