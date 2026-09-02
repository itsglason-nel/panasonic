@echo off
cd /d "%~dp0.."
echo ==============================================
echo       PMPC DATA LOGGER - SYSTEM CHECKER
echo ==============================================
echo.
echo Checking for Python...

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is NOT installed, or NOT added to PATH.
    echo.
    echo To fix this:
    echo 1. Download Python from python.org
    echo 2. Run the installer
    echo 3. CHECK THE BOX "Add Python to PATH" at the bottom!
    echo 4. Click Install Now
) ELSE (
    echo [SUCCESS] Python is installed!
    python --version
    echo.
    echo Checking for required libraries...
    pip install -r requirements.txt
)

echo.
pause
