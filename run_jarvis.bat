@echo off
setlocal
title Jarvis Launcher

cd /d "%~dp0"

echo ================================================================
echo Jarvis Portable Launcher
echo ================================================================

REM Define venv path in User Profile to avoid OneDrive sync issues
set "VENV_PATH=%USERPROFILE%\.jarvis_venv"

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in your PATH.
    echo Please install Python 3.x and try again.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "%VENV_PATH%" (
    echo Creating virtual environment at %VENV_PATH%...
    python -m venv "%VENV_PATH%"
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
    
    REM Upgrade pip immediately after creation
    "%VENV_PATH%\Scripts\python.exe" -m pip install --upgrade pip
)

REM Activate virtual environment
call "%VENV_PATH%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install/Update dependencies
echo Checking dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error: Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    echo Warning: requirements.txt not found. Skipping dependency installation.
)

:loop
cls
echo ================================================================
echo Starting Jarvis WebSocket Server...
echo ================================================================

python websocket_server.py

echo.
echo ================================================================
echo WARNING: WebSocket Server stopped or crashed!
echo Restarting in 2 seconds...
echo Press Ctrl+C to stop.
echo ================================================================
timeout /t 2 >nul
goto loop
