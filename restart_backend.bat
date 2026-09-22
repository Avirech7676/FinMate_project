@echo off
echo Stopping any existing backend processes...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting backend server...
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

pause