#!/bin/bash

echo "========================================="
echo "pyCruds Installation Script"
echo "========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

if [ ! -d "venv" ]; then
    echo "Error: Failed to create virtual environment."
    exit 1
fi

echo "Virtual environment created successfully."
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "Installation completed successfully!"
    echo "========================================="
    echo ""
    echo "To run the application, use:"
    echo "  ./run.sh"
    echo ""
else
    echo ""
    echo "Error: Failed to install dependencies."
    exit 1
fi
