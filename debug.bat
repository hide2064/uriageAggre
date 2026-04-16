@echo off
REM debug.bat - Development mode launcher
REM Opens two windows: FastAPI backend (reload) + Vite dev server
REM
REM Access:
REM   http://localhost:5173   <- Vite dev server (recommended)
REM   http://127.0.0.1:8765  <- FastAPI direct

echo [debug.bat] Starting development servers...

REM Backend: FastAPI with auto-reload on file changes
start "FastAPI Backend" cmd /k "uvicorn backend.main:app --reload --port 8765"

REM Wait for backend to bind the port
timeout /t 2 /nobreak > nul

REM Frontend: Vite dev server (proxies /api -> :8765)
start "Vite Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo [debug.bat] Servers started.
echo   Backend:  http://127.0.0.1:8765
echo   Frontend: http://localhost:5173
echo.
echo Press Ctrl+C in each window to stop.
