@echo off
echo ========================================
echo YouTube Summarizer - Backend Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
cd backend
python -m venv venv

echo [2/5] Activating virtual environment...
call venv\Scripts\activate

echo [3/5] Installing dependencies...
pip install -r requirements.txt

echo [4/5] Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo.
    echo ========================================
    echo IMPORTANT: Edit backend\.env file
    echo ========================================
    echo.
    echo You need to add your API keys:
    echo 1. Get FREE Gemini keys from: https://aistudio.google.com/apikey
    echo 2. Get FREE Redis URL from: https://upstash.com/
    echo.
    echo Press any key to open .env file...
    pause >nul
    notepad .env
) else (
    echo .env file already exists, skipping...
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure you added your API keys to backend\.env
echo 2. Run: cd backend
echo 3. Run: python main.py
echo.
echo Backend will start at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
pause
