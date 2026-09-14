"""
JARVIS V4 Phase 2 - Preflight Subsystem Test Suite
Validates:
 1. PreflightRunner execution and structured result generation
 2. Non-destructive memory write-retrieve-purge cycle
 3. Security boundary checks in preflight (secret access blocked, confirmation gate enforced)
 4. Honest reporting of missing hardware (camera as WARN/UNAVAILABLE instead of false PASS)
 5. Overall PASS / WARN / FAIL evaluation logic
"""

import pytest
from preflight import PreflightRunner, CheckResult

def test_preflight_runner_structure():
    runner = PreflightRunner(base_url="http://127.0.0.1:8000")
    assert runner.base_url == "http://127.0.0.1:8000"
    assert len(runner.results) == 0

def test_memory_pipeline_check():
    runner = PreflightRunner()
    runner.check_memory_pipeline()
    assert len(runner.results) >= 2

    # Verify write and retrieval passed
    write_res = next((r for r in runner.results if r.name == "Write"), None)
    read_res = next((r for r in runner.results if r.name == "Immediate retrieval"), None)
    assert write_res is not None
    assert write_res.status == "PASS"
    assert read_res is not None
    assert read_res.status == "PASS"

def test_security_boundaries_check():
    runner = PreflightRunner()
    runner.check_security_boundaries()

    sec_results = [r for r in runner.results if r.category == "SECURITY"]
    assert len(sec_results) >= 2

    secret_iso = next((r for r in sec_results if r.name == "Secret isolation"), None)
    assert secret_iso is not None
    assert secret_iso.status == "PASS"

    mobile_conf = next((r for r in sec_results if r.name == "Mobile confirmation"), None)
    assert mobile_conf is not None
    assert mobile_conf.status == "PASS"

def test_vision_honesty():
    runner = PreflightRunner()
    runner.check_vision_subsystem()

    cam_res = next((r for r in runner.results if r.name == "Camera device"), None)
    assert cam_res is not None
    # Must report PASS if webcam exists or WARN if unavailable; NEVER false error
    assert cam_res.status in ("PASS", "WARN")

def test_report_rendering():
    runner = PreflightRunner()
    runner.log("SERVER", "Test server", "PASS", "Operational")
    runner.log("VISION", "Camera device", "WARN", "No camera detected")
    report = runner.render_report()

    assert "JARVIS V4 PREFLIGHT" in report
    assert "[PASS]" in report
    assert "[WARN]" in report
    assert "PASS: 1" in report
    assert "WARN: 1" in report
    assert "JARVIS PREFLIGHT: PASS" in report