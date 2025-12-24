#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run ./install.sh first."
    exit 1
fi

# Activate virtual environment and run the application
source venv/bin/activate
python main.py
