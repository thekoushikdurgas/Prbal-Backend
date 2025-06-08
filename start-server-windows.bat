@echo off
echo Starting Prbal Backend Server on Windows...
echo.
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

REM Activate virtual environment if it exists
if exist "abc\Scripts\activate.bat" (
    echo Activating virtual environment...
    call abc\Scripts\activate.bat
)

REM Start the server using Waitress (Windows-compatible)
waitress-serve --host=0.0.0.0 --port=8000 --threads=8 prbal_project.wsgi:application 