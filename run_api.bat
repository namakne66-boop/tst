@echo off
title Syntiox DL - API Server
color 0A

echo.
echo  ==========================================
echo   SYNTIOX DL  ^|  API Server v1.0
echo  ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

:: Install dependencies if needed
echo  [*] Checking dependencies...
pip install -r requirements.txt -q
echo  [*] Dependencies OK
echo.

:: Start server
echo  [*] Starting API on http://localhost:8000
echo  [*] Swagger docs: http://localhost:8000/docs
echo  [*] Press CTRL+C to stop
echo.

uvicorn app:app --host 0.0.0.0 --port 8000 --reload

pause
