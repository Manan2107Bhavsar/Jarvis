@echo off
title Jarvis WebSocket Server
cd /d "%~dp0"
:loop
cls
echo ================================================================
echo Starting Jarvis WebSocket Server...
echo ================================================================
REM Use the python from the virtual environment to run the server
python websocket_server.py

echo.
echo ================================================================
echo WARNING: WebSocket Server stopped or crashed!
echo Restarting in 2 seconds to keep Neural Network online...
echo Press Ctrl+C to stop the loop.
echo ================================================================
timeout /t 2 >nul
goto loop
