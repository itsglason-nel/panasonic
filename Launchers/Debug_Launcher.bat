@echo off
cd /d "%~dp0.."
echo ==============================================
echo       PMPC DATA LOGGER - DEBUG LAUNCHER
echo ==============================================
echo.
echo Attempting to start the launcher and capture errors...
echo.

python launcher.pyw

echo.
echo ==============================================
echo If you see an error above, take a screenshot of it!
echo If it says "Python was not found", you need to restart your computer.
echo ==============================================
pause
