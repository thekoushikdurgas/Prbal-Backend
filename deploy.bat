@echo off
REM Django Production Deployment Script for Windows
echo 🚀 Starting Django Production Deployment...

REM Configuration variables
set PROJECT_DIR=%CD%
set VENV_DIR=%PROJECT_DIR%\venv
set REQUIREMENTS_FILE=%PROJECT_DIR%\requirements.txt
set ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo ❌ ERROR: .env file not found! Please create it from production.env.example
    pause
    exit /b 1
)

echo ✅ Activating virtual environment...
call "%ACTIVATE_SCRIPT%"

echo ✅ Installing/updating dependencies...
python -m pip install --upgrade pip
pip install -r "%REQUIREMENTS_FILE%" --no-cache-dir

echo ✅ Running Django checks...
python manage.py check --deploy

echo ✅ Collecting static files...
python manage.py collectstatic --noinput --clear

echo ✅ Running database migrations...
python manage.py migrate --noinput

echo ✅ Creating cache table...
python manage.py createcachetable

echo ✅ Testing Django configuration...
python manage.py check

echo 🎉 Deployment preparation completed successfully!
echo 🔍 You can now start the production server with: gunicorn -c gunicorn.conf.py prbal_project.wsgi:application

echo Press any key to start Gunicorn server...
pause

echo ✅ Starting Gunicorn production server...
gunicorn -c gunicorn.conf.py prbal_project.wsgi:application 