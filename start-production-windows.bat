@echo off
echo 🚀 Starting Prbal Django Application (Windows Production)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo ✅ Checking Django configuration...
python manage.py check

echo ✅ Starting Waitress production server...
echo 📡 Server will be available at: http://localhost:8000
echo 📊 Health check: http://localhost:8000/health/
echo 📚 API Documentation: http://localhost:8000/swagger/
echo 🛠️  Admin panel: http://localhost:8000/admin/
echo.
echo Press Ctrl+C to stop the server
echo.

waitress-serve --host=0.0.0.0 --port=8000 --threads=4 --connection-limit=1000 prbal_project.wsgi:application 