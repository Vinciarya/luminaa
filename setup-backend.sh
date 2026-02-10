#!/bin/bash

echo "========================================"
echo "YouTube Summarizer - Backend Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo "Please install Python 3.9+ from https://www.python.org/"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
cd backend
python3 -m venv venv

echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo "[3/5] Installing dependencies..."
pip install -r requirements.txt

echo "[4/5] Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "========================================"
    echo "IMPORTANT: Edit backend/.env file"
    echo "========================================"
    echo ""
    echo "You need to add your API keys:"
    echo "1. Get FREE Gemini keys from: https://aistudio.google.com/apikey"
    echo "2. Get FREE Redis URL from: https://upstash.com/"
    echo ""
    echo "Opening .env file..."
    ${EDITOR:-nano} .env
else
    echo ".env file already exists, skipping..."
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Make sure you added your API keys to backend/.env"
echo "2. Run: cd backend"
echo "3. Run: python main.py"
echo ""
echo "Backend will start at: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
