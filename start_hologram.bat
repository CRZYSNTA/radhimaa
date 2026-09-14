@echo off
title JARVIS V4 - Holographic AI Interface
cd /d "%~dp0"
echo ===================================================
echo     JARVIS V4 - HOLOGRAPHIC 3D AI INTERFACE
echo ===================================================
echo Launching hardware-accelerated desktop hologram...
if exist "C:\Users\gowth\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\gowth\AppData\Local\Programs\Python\Python312\python.exe" -m ui.holographic_window
) else (
    python -m ui.holographic_window
)
pause
