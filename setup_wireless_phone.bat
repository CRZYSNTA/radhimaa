@echo off
title JARVIS - Wireless Phone Setup & Unlock Utility
color 0B
setlocal EnableDelayedExpansion

set ADB_BIN="%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"
if not exist %ADB_BIN% (
    set ADB_BIN=adb
)

:MENU
cls
echo ================================================================
echo          JARVIS WIRELESS PHONE CONTROLLER (ADB WI-FI)
echo ================================================================
echo.
echo  [1] 1-Click USB-to-Wireless Switch (Plug USB once, then unplug forever)
echo  [2] Android 11+ Wireless Debugging Pair (No USB cable needed at all)
echo  [3] Connect to Phone Wi-Fi IP directly (e.g. 192.168.1.X:5555)
echo  [4] Test Unlock Phone Wirelessly NOW
echo  [5] Check Active Connected Devices
echo  [6] Exit
echo.
echo ================================================================
set /p CHOICE="Select an option (1-6): "

if "%CHOICE%"=="1" goto USB_TO_WIRELESS
if "%CHOICE%"=="2" goto PAIR_WIRELESS
if "%CHOICE%"=="3" goto CONNECT_IP
if "%CHOICE%"=="4" goto UNLOCK_NOW
if "%CHOICE%"=="5" goto CHECK_DEVICES
if "%CHOICE%"=="6" goto END
goto MENU

:USB_TO_WIRELESS
cls
echo ----------------------------------------------------------------
echo [1-CLICK USB-TO-WIRELESS SWITCH]
echo ----------------------------------------------------------------
echo 1. Connect your phone to this PC via USB cable.
echo 2. Ensure 'USB Debugging' is enabled in Developer Options.
echo.
pause
echo.
echo [Step 1/3] Enabling TCP/IP mode on port 5555...
%ADB_BIN% tcpip 5555
timeout /t 2 /nobreak >nul

echo [Step 2/3] Initializing wireless connection via JARVIS...
python -c "from tools.phone_controller import setup_wireless_adb; print(setup_wireless_adb())"
echo.
echo ----------------------------------------------------------------
echo [SUCCESS] If your phone connected, YOU CAN NOW UNPLUG THE USB CABLE!
echo JARVIS will now be able to wake and unlock your phone completely wirelessly.
echo ----------------------------------------------------------------
echo.
pause
goto MENU

:PAIR_WIRELESS
cls
echo ----------------------------------------------------------------
echo [ANDROID 11+ WIRELESS DEBUGGING PAIRING]
echo ----------------------------------------------------------------
echo On your phone:
echo 1. Open Settings -> Developer Options -> Enable 'Wireless Debugging'.
echo 2. Tap 'Wireless Debugging' -> Tap 'Pair device with pairing code'.
echo 3. You will see an IP address, Pairing Port, and a 6-digit Code.
echo.
set /p PAIR_IP="Enter Phone Wi-Fi IP (e.g. 192.168.1.5): "
set /p PAIR_PORT="Enter Pairing Port (shown under pairing code): "
set /p PAIR_CODE="Enter 6-digit Wi-Fi Pairing Code: "

echo.
echo Pairing with %PAIR_IP%:%PAIR_PORT%...
%ADB_BIN% pair %PAIR_IP%:%PAIR_PORT% %PAIR_CODE%
echo.
echo Now check the MAIN port shown on the Wireless Debugging screen
echo (usually different from the pairing port):
set /p CONN_PORT="Enter Main Connection Port: "

echo.
echo Connecting to %PAIR_IP%:%CONN_PORT%...
%ADB_BIN% connect %PAIR_IP%:%CONN_PORT%
python -c "from tools.phone_controller import save_phone_config; save_phone_config('%PAIR_IP%', %CONN_PORT%)"
echo.
pause
goto MENU

:CONNECT_IP
cls
echo ----------------------------------------------------------------
echo [DIRECT WIRELESS CONNECT]
echo ----------------------------------------------------------------
set /p CONN_IP="Enter Phone IP address (e.g. 192.168.1.15): "
set /p CONN_P="Enter Port (default 5555, press Enter for default): "
if "%CONN_P%"=="" set CONN_P=5555

echo Connecting to %CONN_IP%:%CONN_P%...
%ADB_BIN% connect %CONN_IP%:%CONN_P%
python -c "from tools.phone_controller import save_phone_config; save_phone_config('%CONN_IP%', %CONN_P%)"
echo.
pause
goto MENU

:UNLOCK_NOW
cls
echo ----------------------------------------------------------------
echo [UNLOCK PHONE WIRELESSLY]
echo ----------------------------------------------------------------
set /p UNLOCK_PIN="Enter Phone PIN (or press Enter if swipe-only): "
echo.
echo Dispatching wireless unlock sequence...
python -c "from tools.phone_controller import unlock_phone; print(unlock_phone('%UNLOCK_PIN%'))"
echo.
pause
goto MENU

:CHECK_DEVICES
cls
echo ----------------------------------------------------------------
echo [ACTIVE CONNECTED DEVICES]
echo ----------------------------------------------------------------
%ADB_BIN% devices -l
echo.
python -c "from tools.phone_controller import get_phone_config; print('Saved Wireless Config:', get_phone_config())"
echo.
pause
goto MENU

:END
exit /b 0
