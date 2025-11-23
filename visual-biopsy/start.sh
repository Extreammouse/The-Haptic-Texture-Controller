#!/bin/bash
# Quick Start Script for Haptic Histology
# Automatically detects serial port and launches the system

echo "=========================================="
echo "  HAPTIC HISTOLOGY - QUICK START"
echo "=========================================="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check for dependencies
echo " Checking dependencies..."
python3 -c "import pygame, cv2, numpy, sklearn, serial" 2>/dev/null
if [ $? -ne 0 ]; then
    echo " Missing dependencies. Installing..."
    pip3 install -r linux_brain/requirements.txt
else
    echo "✓ All dependencies installed"
fi

echo ""
echo " Detecting Arduino..."

SERIAL_PORT=""
if [ "$(uname)" == "Darwin" ]; then
    SERIAL_PORT=$(ls /dev/cu.usbmodem* 2>/dev/null | head -n 1)
    if [ -z "$SERIAL_PORT" ]; then
        SERIAL_PORT=$(ls /dev/cu.usbserial* 2>/dev/null | head -n 1)
    fi
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    SERIAL_PORT=$(ls /dev/ttyACM* 2>/dev/null | head -n 1)
    if [ -z "$SERIAL_PORT" ]; then
        SERIAL_PORT=$(ls /dev/ttyUSB* 2>/dev/null | head -n 1)
    fi
fi

if [ -z "$SERIAL_PORT" ]; then
    echo " No Arduino detected. Running in DEMO mode."
    echo "    (You can still see the visualization without hardware)"
else
    echo "✓ Found Arduino: $SERIAL_PORT"
    echo "  Updating configuration..."
    
    # Update the serial port in haptic_scanner.py
    sed -i.bak "s|serial_port: str = '[^']*'|serial_port: str = '$SERIAL_PORT'|" linux_brain/haptic_scanner.py
fi

echo ""
echo " Launching Haptic Histology Scanner..."
echo "=========================================="
echo ""

cd linux_brain
python3 haptic_scanner.py

echo ""
echo "✓ Session complete. Goodbye!"
