@echo off
REM start.bat - Production mode launcher (pywebview desktop)
REM Builds the Vue frontend, then launches the desktop app.

echo [start.bat] Building Vue frontend...
cd frontend
npm run build
if errorlevel 1 (
    echo [ERROR] Frontend build failed.
    pause
    exit /b 1
)
cd ..
echo [start.bat] Build complete.

echo [start.bat] Starting desktop app...
python -m backend.main
