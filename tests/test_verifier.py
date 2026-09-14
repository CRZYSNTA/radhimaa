"""
Unit tests for Action Verification Subsystem.
"""

import os
import tempfile
from core.verifier import verify_action, VerificationResult
from memory import user_memory

def test_verify_fact_memory():
    user_memory.remember("favorite_hero", "Iron Man")
    res = verify_action("remember_fact", {"key": "favorite_hero"}, "stored")
    assert res.success
    assert "Verified fact" in res.observation

def test_verify_file_write_and_delete():
    temp_file = os.path.join(tempfile.gettempdir(), "jarvis_verifier_test.txt")
    with open(temp_file, "w") as f:
        f.write("verified")

    res_write = verify_action("write_file", {"path": temp_file}, "ok")
    assert res_write.success

    os.remove(temp_file)
    res_delete = verify_action("delete_file", {"path": temp_file}, "ok")
    assert res_delete.success

def test_verify_general_output():
    res_ok = verify_action("get_time", {}, "The current time is 10:00 AM")
    assert res_ok.success

    res_err = verify_action("get_time", {}, "Error: unable to fetch time")
    assert not res_err.success
