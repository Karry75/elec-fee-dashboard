@echo off
REM Manual sync entry point (Windows). Runs the unified sync: pull -> merge -> compute_warn -> sync_log.
REM Default source is "excel" (reads the two local Excel files). Set SYNC_SOURCE=mysql to pull from DB.
cd /d "%~dp0"
python run_sync.py %*
if errorlevel 1 (
    echo [ERR] sync failed with exit code %errorlevel%
    exit /b 1
)
echo [OK] sync finished.
