@echo off

cd /d "%~dp0"

where uv >nul 2>&1

if errorlevel 1 (
    echo ERROR: uv not found.
    echo.
    pause
    exit /b 1
)

echo ========================================
echo          ANOMALY DETECTOR
echo ========================================
echo.
echo Starting application...
echo.

uv run --directory app python entrypoint/main.py
