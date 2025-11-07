@echo off
cd /d "%~dp0"
echo Starting Accident Detection System...
echo Press 'q' in the video window to quit
echo.
venv\Scripts\python.exe main.py
if errorlevel 1 (
    echo.
    echo Error occurred. Check the output above.
    pause
)















