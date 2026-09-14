@echo off
title Install JARVIS APK to Connected Android Phone
echo ===================================================
echo     INSTALL JARVIS COMPANION APK VIA USB (ADB)
echo ===================================================
echo Checking for connected Android devices...
"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" devices
echo.
echo Installing JARVIS_Companion.apk to your phone...
"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" install -r "%~dp0android_app\app\build\outputs\apk\debug\app-debug.apk"
echo.
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] JARVIS Companion App installed on your phone!
) else (
    echo [NOTE] If no device was detected, enable 'USB Debugging' in your phone's Developer Options and reconnect.
    echo Alternatively, copy 'JARVIS_Companion.apk' from your Desktop to your phone and install it directly.
)
pause
