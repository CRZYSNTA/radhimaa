"""
Unit tests for Sandboxed File Tools.
"""

import os
from pathlib import Path
from tools.files import write_file, read_file, list_directory, delete_file
import config

def test_file_crud_in_sandbox():
    test_file = str(Path(config.BASE_DIR) / "test_pytest_file.txt")
    
    # Write
    write_res = write_file(test_file, "Hello from JARVIS tests!")
    assert "successfully written" in write_res.lower()
    assert os.path.exists(test_file)

    # Read
    content = read_file(test_file)
    assert content == "Hello from JARVIS tests!"

    # List
    dir_listing = list_directory(str(config.BASE_DIR))
    assert "test_pytest_file.txt" in dir_listing

    # Delete
    del_res = delete_file(test_file)
    assert "deleted successfully" in del_res.lower()
    assert not os.path.exists(test_file)

def test_file_sandbox_rejections():
    # Path traversal
    res = write_file("../../dangerous.txt", "exploit")
    assert "access denied" in res.lower()

    # Outside safe roots
    res_read = read_file("C:/Windows/System32/drivers/etc/hosts")
    assert "access denied" in res_read.lower()
