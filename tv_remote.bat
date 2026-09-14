@echo off
title JARVIS Smart TV Controller
color 0A
setlocal EnableDelayedExpansion

:MENU
cls
echo ================================================================
echo            JARVIS UNIVERSAL SMART TV REMOTE CONTROL
echo ================================================================
python -c "from tools.tv_controller import get_tv_config; cfg=get_tv_config(); print('Active TV:', cfg.get('tv_name', 'None'), '| IP:', cfg.get('tv_ip', 'Not Set'), '| Protocol:', cfg.get('tv_type', 'None'))"
echo ================================================================
echo.
echo  [1] Scan Local Wi-Fi for Smart TVs (Auto-Discovery)
echo  [2] Connect Directly to TV IP (e.g. 192.168.1.X)
echo.
echo  --- REMOTE CONTROLS ---
echo  [P] Power Toggle (Wake / Sleep)
echo  [W] UP          [S] DOWN        [A] LEFT        [D] RIGHT
echo  [O] OK / SELECT [B] BACK        [H] HOME        [M] MUTE
echo  [+] VOLUME UP   [-] VOLUME DOWN [SPACE] PLAY/PAUSE
echo.
echo  --- APPS & MEDIA ---
echo  [Y] Launch YouTube     [N] Launch Netflix      [V] Launch Prime Video
echo  [T] Type Text / Search [K] Play Video Query
echo.
echo  [Q] Exit
echo.
echo ================================================================
set /p ACTION="Select a command or press a key: "

if /i "%ACTION%"=="1" goto SCAN_TVS
if /i "%ACTION%"=="2" goto CONNECT_TV
if /i "%ACTION%"=="P" goto POWER
if /i "%ACTION%"=="W" goto KEY_UP
if /i "%ACTION%"=="S" goto KEY_DOWN
if /i "%ACTION%"=="A" goto KEY_LEFT
if /i "%ACTION%"=="D" goto KEY_RIGHT
if /i "%ACTION%"=="O" goto KEY_OK
if /i "%ACTION%"=="B" goto KEY_BACK
if /i "%ACTION%"=="H" goto KEY_HOME
if /i "%ACTION%"=="M" goto KEY_MUTE
if /i "%ACTION%"=="+" goto VOL_UP
if /i "%ACTION%"=="-" goto VOL_DOWN
if /i "%ACTION%"=="Y" goto APP_YOUTUBE
if /i "%ACTION%"=="N" goto APP_NETFLIX
if /i "%ACTION%"=="V" goto APP_PRIME
if /i "%ACTION%"=="T" goto TYPE_TEXT
if /i "%ACTION%"=="K" goto PLAY_VIDEO
if /i "%ACTION%"=="Q" goto END
goto MENU

:SCAN_TVS
cls
echo Scanning local subnet for Smart TVs...
python -c "from tools.tv_controller import discover_smart_tvs; print(discover_smart_tvs())"
echo.
pause
goto MENU

:CONNECT_TV
cls
set /p TVIP="Enter TV IP address (e.g. 192.168.1.10): "
python -c "from tools.tv_controller import connect_tv; print(connect_tv('%TVIP%'))"
echo.
pause
goto MENU

:POWER
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('power'))"
goto MENU

:KEY_UP
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('up'))"
goto MENU

:KEY_DOWN
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('down'))"
goto MENU

:KEY_LEFT
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('left'))"
goto MENU

:KEY_RIGHT
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('right'))"
goto MENU

:KEY_OK
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('select'))"
goto MENU

:KEY_BACK
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('back'))"
goto MENU

:KEY_HOME
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('home'))"
goto MENU

:KEY_MUTE
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('mute'))"
goto MENU

:VOL_UP
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('volume_up'))"
goto MENU

:VOL_DOWN
python -c "from tools.tv_controller import tv_remote_control; print(tv_remote_control('volume_down'))"
goto MENU

:APP_YOUTUBE
python -c "from tools.tv_controller import tv_launch_app; print(tv_launch_app('youtube'))"
goto MENU

:APP_NETFLIX
python -c "from tools.tv_controller import tv_launch_app; print(tv_launch_app('netflix'))"
goto MENU

:APP_PRIME
python -c "from tools.tv_controller import tv_launch_app; print(tv_launch_app('prime'))"
goto MENU

:TYPE_TEXT
cls
set /p QUERY="Enter text to type into TV search: "
python -c "from tools.tv_controller import tv_input_text; print(tv_input_text('%QUERY%'))"
goto MENU

:PLAY_VIDEO
cls
set /p VID="Enter video name or YouTube URL to play on TV: "
python -c "from tools.tv_controller import tv_play_media; print(tv_play_media('%VID%'))"
goto MENU

:END
exit /b 0
