@echo off
REM ============================================================
REM  debug.bat — 開発環境起動スクリプト
REM ============================================================
REM  バックエンド (FastAPI) と フロントエンド (Vite dev server) を
REM  それぞれ別ウィンドウで起動します。
REM
REM  アクセス先:
REM    http://localhost:5173   ← Vite dev server (推奨)
REM    http://127.0.0.1:8765  ← FastAPI 直接
REM
REM  停止方法: 各ウィンドウで Ctrl+C を押してください。
REM ============================================================

echo [debug.bat] 開発サーバーを起動しています...

REM ── バックエンド (FastAPI + uvicorn --reload) ──────────────
REM   --reload: ファイル変更を検知して自動再起動
REM   --port 8765: Vue の vite.config.js プロキシ先に合わせる
start "FastAPI Backend" cmd /k "uvicorn backend.main:app --reload --port 8765"

REM 少し待ってからフロントエンドを起動（ポートバインド待ち）
timeout /t 2 /nobreak > nul

REM ── フロントエンド (Vite dev server) ──────────────────────
REM   Vite の /api プロキシが自動的に :8765 へ転送する
start "Vite Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo [debug.bat] 起動完了。
echo   バックエンド: http://127.0.0.1:8765
echo   フロントエンド: http://localhost:5173
echo.
echo 各ウィンドウで Ctrl+C を押すと停止します。
