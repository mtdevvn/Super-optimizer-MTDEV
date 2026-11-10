@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.11 -m venv .venv
  if errorlevel 1 (
    echo Install Python 3.11 x64 from python.org, including the Python Launcher.
    pause
    exit /b 1
  )
)
.venv\Scripts\python.exe -c "import PySide6, psutil" >nul 2>&1
if errorlevel 1 (
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependency installation failed. Internet access is needed for first installation.
    pause
    exit /b 1
  )
)
.venv\Scripts\python.exe main.py
if errorlevel 1 pause
