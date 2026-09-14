@echo off
REM JARVIS V3.0 Automated Test Suite Runner
python run_tests.py %*
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Test suite failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
echo [SUCCESS] All tests passed!
