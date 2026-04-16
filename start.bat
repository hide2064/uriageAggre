@echo off
REM start.bat - Production mode launcher (pywebview desktop)
REM Builds Vue frontend, kills any existing instance on :8765, then launches.

REM ---------------------------------------------------------------
REM  Step 1: Kill any process already using port 8765 (graceful restart)
REM ---------------------------------------------------------------
echo [start.bat] Checking port 8765...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R "\b8765\b" 2^>nul') do (
    echo [start.bat] Killing PID %%a (was using port 8765)
    taskkill /PID %%a /F >nul 2>&1
)

REM ---------------------------------------------------------------
REM  Step 2: Build Vue frontend
REM ---------------------------------------------------------------
echo [start.bat] Building Vue frontend...
pushd frontend
npm run build
if errorlevel 1 (
    echo [ERROR] Frontend build failed.
    popd
    pause
    exit /b 1
)
popd
echo [start.bat] Frontend build complete.

REM ---------------------------------------------------------------
REM  Step 3: Launch desktop app (uvicorn + pywebview in one process)
REM          uvicorn serves both API and static Vue files on :8765
REM          pywebview opens a desktop window pointing to :8765
REM ---------------------------------------------------------------
echo [start.bat] Starting app (backend + frontend on port 8765)...
python -m backend.main
if errorlevel 1 (
    echo [ERROR] App exited with an error. See above for details.
    pause
)
