@echo off
set TF_CPP_MIN_LOG_LEVEL=2
set CUDA_VISIBLE_DEVICES=
cd /d "%~dp0"
echo.
echo ========================================
echo  Accident Detection System
echo ========================================
echo.
venv\Scripts\python.exe main.py
echo.
echo Application closed.
pause
