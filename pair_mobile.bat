@echo off
title JARVIS Mobile Device Pairing
echo ===================================================
echo     JARVIS V3.0 - MOBILE DEVICE PAIRING
echo ===================================================
echo Initializing pairing session...
"C:\Users\gowth\AppData\Local\Programs\Python\Python312\python.exe" -m tools.pairing_manager
echo.
echo Point your mobile phone camera at the QR code above or open the URL displayed.
echo Press any key to exit pairing display.
pause >nul
