@echo off
chcp 65001 >nul
title JARVIS V4 Holographic AI Operating System
cd /d "%~dp0"
echo =========================================================
echo    LAUNCHING JARVIS / LEO HOLOGRAPHIC DESKTOP APP
echo    - Backend: FastAPI (127.0.0.1:8000)
echo    - UI: Three.js 3D Hologram + Chat Dock + Confirm Modal
echo    - Voice: Push-to-Talk (Hold [HOME] Key)
echo    - Memory: Obsidian Knowledge Vault
echo =========================================================
"C:\Users\gowth\AppData\Local\Programs\Python\Python312\python.exe" desktop_window.py
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%.
    pause
)
