@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title JARVIS + LEO Assistant
cd /d "%~dp0"
echo Starting JARVIS + LEO Assistant...
"C:\Users\gowth\AppData\Local\Programs\Python\Python312\python.exe" main.py
pause

