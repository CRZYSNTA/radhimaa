# PowerShell Launcher for JARVIS / LEO Native Desktop App
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "   LAUNCHING JARVIS / LEO HOLOGRAPHIC DESKTOP APP" -ForegroundColor Cyan
Write-Host "   - Backend: FastAPI (127.0.0.1:8000)" -ForegroundColor Gray
Write-Host "   - UI: Three.js 3D Hologram + Chat Dock + Confirm Modal" -ForegroundColor Gray
Write-Host "   - Voice: Push-to-Talk (Hold [HOME] Key)" -ForegroundColor Gray
Write-Host "   - Memory: Obsidian Knowledge Vault" -ForegroundColor Gray
Write-Host "=========================================================" -ForegroundColor Cyan

& "C:\Users\gowth\AppData\Local\Programs\Python\Python312\python.exe" desktop_window.py
