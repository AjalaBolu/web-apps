@echo off
REM ============================================================
REM  Network Monitor Agent — Launcher
REM  Double-click this file to start monitoring this device.
REM  No need to open PowerShell or type any commands.
REM ============================================================

REM --- EDIT THESE TWO LINES BEFORE SHARING THIS FILE ---
set MONITOR_API_URL="https://web-apps-z35b.onrender.com"
set MONITOR_API_KEY="7449585715b2ae37f27cb5c2735d53ffe51f2b6d30c32abe91f10333401d3b3c"

REM -------------------------------------------------------

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo Python was not found on this computer.
    echo Please install Python 3 first: https://www.python.org/downloads/
    echo Then run this file again.
    echo.
    pause
    exit /b 1
)

echo Installing required packages the first time this runs...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo.
echo Starting monitoring agent. Leave this window open — closing it stops monitoring.
echo Press Ctrl+C to stop.
echo.
python agent.py

pause
