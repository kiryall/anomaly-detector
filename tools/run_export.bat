@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo    Export YOLO model to ONNX
echo ========================================
echo.

if "%~1"=="" (
    set /p MODEL_PATH="Enter path to model (.pt): "
    if "!MODEL_PATH!"=="" (
        goto :end
    )
    python export_to_onnx.py "!MODEL_PATH!"
) else (
    echo Exporting %~1 ...
    echo.
    python export_to_onnx.py %*
)

echo.
echo ========================================
echo    Done
echo ========================================

:end
pause
