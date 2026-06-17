@echo off
title Passman - Password Management System Launcher
echo Starting Passman...

:: Check for required libraries and install if missing
echo Verifying dependencies...
pip install cryptography maskpass --quiet

:: Run the main GUI script
python "Passman_GUI.py"

if %errorlevel% neq 0 (
    echo.
    echo Application exited with an error.
    pause
)