@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title JARVIS + LEO Unified Operating Environment
cd /d "%~dp0"
echo ========================================================
echo      JARVIS + LEO UNIFIED MASTER SYSTEM (V4.0)
echo ========================================================
set "PY_BIN=C:\Users\gowth\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY_BIN%" set "PY_BIN=python"

echo  - Single Unified Assistant: "Jarvis" / "Leo" (Gowtham's Operator)
echo  - Obsidian Memory Vault: C:\Users\gowth\das and co
echo  - Central FastAPI Server: http://localhost:8000
echo  - 3D Holographic Viewport: http://localhost:8000/hologram
echo  - Living Visualizer: http://localhost:8790
echo ========================================================

:: 1. Start Central Server in background
echo Starting Central Server ^& Mobile Gateway...
start "JARVIS Central Server" cmd /c "%PY_BIN% server.py"

:: 2. Wait for server socket initialization
timeout /t 2 /nobreak >nul

:: 3. Launch 3D Holographic Window
echo Launching 3D Holographic Window...
start "JARVIS 3D Hologram" cmd /c "%PY_BIN% -m ui.holographic_window"

:: 4. Start Living Visualizer on port 8790
echo Starting Living Visualizer (Port 8790)...
start "Living Visualizer" cmd /c "%PY_BIN% leo/ai-visualizer/server.py"

:: 5. Launch Unified Voice & Task Assistant
echo Launching Unified Voice Assistant Loop...
"%PY_BIN%" main.py

pause
