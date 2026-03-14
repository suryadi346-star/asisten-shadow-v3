#!/bin/bash

# Asisten Shadow v3.0 - Launcher Script

echo "========================================="
echo "   Asisten Shadow v3.0"
echo "   Multi-platform Encrypted Notes"
echo "========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

echo "✓ Python detected"

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
if [ ! -f "venv/.deps_installed" ]; then
    echo "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    touch venv/.deps_installed
    echo "✓ Dependencies installed"
else
    echo "✓ Dependencies OK"
fi

# Run app
echo ""
echo "🚀 Launching Asisten Shadow..."
echo "========================================="
echo ""

cd src
python main.py

# Deactivate
deactivate

echo ""
echo "========================================="
echo "   Thank you for using Asisten Shadow!"
echo "========================================="
