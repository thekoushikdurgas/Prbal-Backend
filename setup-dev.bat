@echo off
echo 🔧 Setting up Django Development Environment on Windows...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo ✅ Creating virtual environment...
    python -m venv venv
)

echo ✅ Activating virtual environment...
call venv\Scripts\activate.bat

echo ✅ Upgrading pip...
python -m pip install --upgrade pip

echo ✅ Installing requirements...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  WARNING: .env file not found!
    echo Creating .env from production.env.example...
    copy production.env.example .env
    echo ❗ Please edit .env file with your actual configuration values
)

echo ✅ Running initial Django setup...
python manage.py check

echo ✅ Creating database migrations...
python manage.py makemigrations

echo ✅ Running migrations...
python manage.py migrate

echo ✅ Collecting static files...
python manage.py collectstatic --noinput

echo 🎉 Development environment setup completed!
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Create a superuser: python manage.py createsuperuser
echo 3. Start development server: python manage.py runserver
echo 4. For production, use: deploy.bat
echo.
pause 