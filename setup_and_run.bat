@echo off
title Passman - Automatic Setup and Launcher
echo ==========================================
echo    PASSMAN SYSTEM SETUP AND LAUNCHER
echo ==========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your PATH.
    echo Please install Python to run this application.
    pause
    exit /b
)

echo [1/3] Installing/Updating required libraries...
pip install cryptography maskpass --quiet

if not exist "System_Password.txt" (
    echo [2/3] Initializing default system password...
    python "Default System Password.py"
) else (
    echo [2/3] System password already initialized.
)

echo [3/3] Launching Passman GUI...
python "Passman_GUI.py"
pause