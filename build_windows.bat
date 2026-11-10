@echo off
setlocal
cd /d "%~dp0"
py -3.11 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe -c "import struct, sys; assert sys.platform == 'win32' and struct.calcsize('P') == 8, 'Build requires Windows x64 Python'"
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pytest -q
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm OptimizeSuper.spec
if errorlevel 1 goto fail
echo Build created: dist\OptimizeSuper-MTDEV.exe
echo Test on clean Windows 10 and Windows 11 machines before distribution.
pause
exit /b 0
:fail
echo Build failed. Review the errors above.
pause
exit /b 1
