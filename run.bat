@echo off
cd /d "%~dp0"
title WinTokenMon
echo ========================================================
echo Starting WinTokenMon for Windows...
echo ========================================================
python main.py
if %errorlevel% neq 0 (
    echo.
    echo ========================================================
    echo [ERROR] An issue occurred while running WinTokenMon.
    echo See debug.log for details.
    echo ========================================================
    pause
)
