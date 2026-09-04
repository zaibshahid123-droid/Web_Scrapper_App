@echo off
echo ================================================
echo   WebScraper Pro — Setup Script
echo ================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/5] Installing dependencies...
pip install -r requirements.txt

echo [3/5] Running migrations...
python manage.py migrate

echo [4/5] Creating superuser...
echo Please create your admin account:
python manage.py createsuperuser

echo [5/5] Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ================================================
echo   Setup complete!
echo   Run:  venv\Scripts\activate ^& python manage.py runserver
echo   Then open: http://127.0.0.1:8000
echo ================================================
pause
