@echo off
title JARVIS Phone Unlock Utility (Wireless / USB)
echo ======================================================
echo       JARVIS ANDROID PHONE UNLOCK (WIRELESS / USB)
echo ======================================================
echo.

set PIN=%1
if "%PIN%"=="" (
    set /p PIN="Enter phone PIN (press Enter for swipe-only or saved PIN): "
)

echo.
echo Waking phone and unlocking wirelessly...
python -c "from tools.phone_controller import unlock_phone; print(unlock_phone('%PIN%'))"
echo.
pause
