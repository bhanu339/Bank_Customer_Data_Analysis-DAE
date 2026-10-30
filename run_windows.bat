@echo off
setlocal
cd /d "%~dp0"
title Bank Customer Data Analysis System
echo =====================================================
echo Bank Customer Data Analysis System
echo =====================================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 or newer from:
  echo https://www.python.org/downloads/windows/
  echo During installation, enable "Add Python to PATH".
  pause
  exit /b 1
)
python --version
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Could not create virtual environment.
    pause
    exit /b 1
  )
)
echo.
echo Installing required libraries. First run may take a few minutes...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo pip upgrade failed. Check your internet connection.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Package installation failed. Copy this window's error and send it for help.
  pause
  exit /b 1
)
echo.
echo Starting the dashboard...
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 (
  echo The dashboard stopped with an error. Copy the message above.
  pause
)
endlocal
