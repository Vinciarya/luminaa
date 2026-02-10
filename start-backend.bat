@echo off
echo ========================================
echo Starting YouTube Summarizer Backend
echo ========================================
echo.

cd backend

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Starting FastAPI server...
echo Backend will be available at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

python main.py
