"""
JARVIS V3.0 - Reliable Automated Test Runner
Invokes pytest directly via sys.executable to bypass WindowsApps execution alias permissions issues.
"""

import os
import sys
import shutil
import subprocess

def find_python_with_pytest():
    candidate_exes = [
        sys.executable,
        r"C:\Users\gowth\AppData\Local\Programs\Python\Python312\python.exe",
        shutil.which("python"),
        shutil.which("py")
    ]
    for exe in candidate_exes:
        if exe and os.path.exists(exe):
            check = subprocess.run([exe, "-m", "pytest", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if check.returncode == 0:
                return exe
    return sys.executable

def main():
    python_exe = find_python_with_pytest()
    args = [python_exe, "-m", "pytest"] + sys.argv[1:]
    if len(sys.argv) == 1:
        args.extend(["tests", "-v"])
    print(f"[TEST RUNNER] Executing: {' '.join(args)}")
    res = subprocess.run(args)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
