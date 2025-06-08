@echo off
echo 🚀 Starting Prbal Backend Production Server...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Gunicorn with the configuration file
echo ✅ Starting Gunicorn server on port 8000...
gunicorn -c gunicorn.conf.py prbal_project.wsgi:application

pause 