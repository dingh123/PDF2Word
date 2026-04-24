@echo off
REM Build PDF2Word.exe on Windows.
REM
REM Usage (from project root):
REM   build_scripts\build-windows.bat
REM
REM Requires: Python 3.9+ installed and on PATH.
REM Output: dist\PDF2Word\PDF2Word.exe (run or zip the whole folder)

setlocal
cd /d "%~dp0.."

set PYTHON=python
set VENV_DIR=.venv

if not exist "%VENV_DIR%" (
    echo [1/4] Creating virtualenv in %VENV_DIR%
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 goto :fail
)

call "%VENV_DIR%\Scripts\activate.bat"

echo [2/4] Installing build dependencies
python -m pip install --upgrade pip >NUL
pip install -r requirements-build.txt
if errorlevel 1 goto :fail

echo [3/4] Cleaning previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [4/4] Running PyInstaller
pyinstaller pdf2word.spec --noconfirm --clean
if errorlevel 1 goto :fail

echo.
echo Build complete: dist\PDF2Word\PDF2Word.exe
echo To distribute: zip the dist\PDF2Word folder, or use Inno Setup to make an installer.
exit /b 0

:fail
echo.
echo Build failed.
exit /b 1
