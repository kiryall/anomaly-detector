@echo off

cd /d "%~dp0"

where uv >nul 2>&1

if errorlevel 1 (
    echo ERROR: uv не найден.
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

if errorlevel 1 (
    echo.
    echo ========================================
    echo        APPLICATION ERROR
    echo ========================================
    echo.
    pause
)
