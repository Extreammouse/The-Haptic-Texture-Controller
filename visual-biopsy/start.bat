@echo off
REM Quick Start Script for Haptic Histology (Windows)
REM Automatically detects COM port and launches the system

echo ==========================================
echo   HAPTIC HISTOLOGY - QUICK START
echo ==========================================
echo.

REM Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check for dependencies
echo Checking dependencies...
python -c "import pygame, cv2, numpy, sklearn, serial" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Missing dependencies. Installing...
    pip install -r linux_brain\requirements.txt
) else (
    echo All dependencies installed
)

echo.
echo Detecting Arduino...

REM Note: Automatic COM port detection on Windows requires additional tools
REM For now, we'll let the Python script handle it in demo mode
echo Running Haptic Histology Scanner...
echo If you have an Arduino connected, update the serial_port in haptic_scanner.py
echo.
echo ==========================================
echo.

cd linux_brain
python haptic_scanner.py

echo.
echo Session complete. Goodbye!
pause
