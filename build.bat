@echo off
setlocal enabledelayedexpansion

:: ============================================================
:: build.bat — сборка anomaly-detector в portable EXE (PyInstaller, --onedir)
:: ============================================================

:: Предотвращает предупреждение uv о жёстких ссылках при разных ФС
set UV_LINK_MODE=copy

echo ============================================
echo  AnomalyDetector Build Script
echo ============================================
echo.

:: 1. Перейти в корень репозитория
cd /d "%~dp0"
echo [1/9] Working directory: %CD%
echo.

:: 2. Проверить наличие uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] uv not found. Please install uv: https://docs.astral.sh/uv/getting-started/installation/
    echo         Or run: pip install uv
    pause
    exit /b 1
)
echo [2/9] uv found:
uv --version
echo.

:: 3. Убедиться, что окружение app активно
echo [3/9] Syncing environment in app/...
pushd app
uv sync
if %errorlevel% neq 0 (
    echo [ERROR] uv sync failed.
    popd
    pause
    exit /b 1
)
echo.

:: 4. Убедиться, что PyInstaller установлен
echo [4/9] Checking PyInstaller...
uv run pyinstaller --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    uv add --dev pyinstaller 2>nul
    echo PyInstaller installed.
) else (
    echo PyInstaller is already installed.
)
uv run pyinstaller --version
popd
echo.

:: 5. Очистить старые артефакты сборки
echo [5/9] Cleaning old build artifacts...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist "AnomalyDetector.spec" del /q "AnomalyDetector.spec"
echo Cleaned.
echo.

:: 6. Запустить PyInstaller
echo [6/9] Running PyInstaller (--onedir)...
echo.
uv run pyinstaller ^
    --name AnomalyDetector ^
    --onedir ^
    --noconfirm ^
    --clean ^
    --console ^
    --collect-all nicegui ^
    --collect-all onnxruntime ^
    --collect-all cv2 ^
    --collect-data onnxruntime ^
    --hidden-import pydantic ^
    --hidden-import openpyxl ^
    --hidden-import numpy ^
    --hidden-import PIL ^
    --hidden-import cv2 ^
    --hidden-import onnxruntime ^
    --paths "%~dp0app" ^
    "app\entrypoint\main.py"

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)
echo.
echo PyInstaller build completed successfully.
echo.

:: 7. Создать структуру release/AnomalyDetector
echo [7/9] Creating release structure...
if exist release rmdir /s /q release
mkdir release\AnomalyDetector
echo Created: release\AnomalyDetector
echo.

:: 8. Скопировать результат сборки
echo [8/9] Copying build output to release...
xcopy /e /i /y dist\AnomalyDetector\*.* release\AnomalyDetector\
if %errorlevel% neq 0 (
    echo [ERROR] Failed to copy dist output.
    pause
    exit /b 1
)
echo Copied dist\AnomalyDetector\*.* -> release\AnomalyDetector\
echo.

:: 9. Создать пустые папки models и data/*
echo [9/9] Creating data directories...
mkdir release\AnomalyDetector\models
mkdir release\AnomalyDetector\data\database
mkdir release\AnomalyDetector\data\output
mkdir release\AnomalyDetector\data\reports
mkdir release\AnomalyDetector\data\logs
echo Created:
echo   release\AnomalyDetector\models\
echo   release\AnomalyDetector\data\database\
echo   release\AnomalyDetector\data\output\
echo   release\AnomalyDetector\data\reports\
echo   release\AnomalyDetector\data\logs\
echo.

:: 10. Скопировать модели, если они есть
echo Checking for model files...
if exist models\best.onnx (
    xcopy /y models\best.onnx release\AnomalyDetector\models\
    echo Copied: models\best.onnx -> release\AnomalyDetector\models\
) else (
    echo Skipped: models\best.onnx not found
)

if exist models\best.json (
    xcopy /y models\best.json release\AnomalyDetector\models\
    echo Copied: models\best.json -> release\AnomalyDetector\models\
) else (
    echo Skipped: models\best.json not found
)
echo.

:: Итоговое сообщение
echo ============================================
echo  BUILD COMPLETED SUCCESSFULLY!
echo ============================================
echo.
echo Output directory:
echo   release\AnomalyDetector\
echo.
echo Contents:
echo   - AnomalyDetector.exe
echo   - _internal\        (dependencies)
echo   - models\           (copy best.onnx / best.json here)
echo   - data\database\
echo   - data\output\
echo   - data\reports\
echo   - data\logs\
echo.
echo Run: release\AnomalyDetector\AnomalyDetector.exe
echo.
pause
