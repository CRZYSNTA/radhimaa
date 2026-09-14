"""
Unit tests for Permissions and Path Sandboxing.
"""

from core.permissions import check_permission, PermissionLevel, is_path_safe

def test_safe_permissions():
    perm, _ = check_permission("volume_up", {})
    assert perm == PermissionLevel.SAFE

    perm, _ = check_permission("get_time", {})
    assert perm == PermissionLevel.SAFE

    perm, _ = check_permission("remember_fact", {"key": "test", "value": "123"})
    assert perm == PermissionLevel.SAFE

def test_confirm_permissions():
    import config
    safe_target = str(config.BASE_DIR / "sample.txt")
    perm, _ = check_permission("delete_file", {"path": safe_target})
    assert perm == PermissionLevel.CONFIRM

def test_blocked_dangerous_operations():
    perm, _ = check_permission("run_shell_cmd", {"cmd": "whoami"})
    assert perm == PermissionLevel.BLOCKED

    perm, _ = check_permission("format_disk", {})
    assert perm == PermissionLevel.BLOCKED

    perm, _ = check_permission("unknown_random_malicious_tool", {})
    assert perm == PermissionLevel.BLOCKED

def test_path_traversal_detection():
    # Attempting to break out with ..
    assert not is_path_safe("../../Windows/System32")
    assert not is_path_safe("C:/Windows/System32/cmd.exe")
    assert not is_path_safe("../../../sensitive.dat")

    # Path traversal in tool params should force BLOCKED
    perm, reason = check_permission("read_file", {"path": "../../Windows/System32/cmd.exe"})
    assert perm == PermissionLevel.BLOCKED
    assert "blocked" in reason.lower()
