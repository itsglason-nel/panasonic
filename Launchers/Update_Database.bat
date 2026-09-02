@echo off
cd /d "%~dp0.."
echo ==============================================
echo       PMPC DATA LOGGER - DATABASE UPDATER
echo ==============================================
echo.
echo Running database migrations...
echo.

python tools\run_migration.py

echo.
echo ==============================================
echo If you see "Database migration completed successfully!", 
echo you can close this window and start the system.
echo ==============================================
pause
