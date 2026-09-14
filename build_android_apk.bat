@echo off
title Build JARVIS Android APK
echo ===================================================
echo     JARVIS - BUILD NATIVE ANDROID APK
echo ===================================================
cd /d "%~dp0\android_app"
call gradlew.bat assembleDebug
echo.
echo Build finished!
echo APK Output: android_app\app\build\outputs\apk\debug\app-debug.apk
pause
