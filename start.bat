@echo off
REM ============================================================
REM  start.bat — 本番モード起動スクリプト（pywebview デスクトップ）
REM ============================================================
REM  Vue フロントエンドをビルドし、pywebview でデスクトップアプリとして起動します。
REM  インターネット接続不要。すべてローカルで動作します。
REM
REM  前提条件:
REM    pip install -r requirements.txt
REM    npm install (frontend/ ディレクトリ内)
REM ============================================================

echo [start.bat] 本番モードで起動しています...

REM ── フロントエンドビルド ────────────────────────────────────
echo [1/2] Vue フロントエンドをビルド中...
cd frontend
npm run build
if errorlevel 1 (
    echo [ERROR] フロントエンドのビルドに失敗しました。
    pause
    exit /b 1
)
cd ..
echo [1/2] ビルド完了。

REM ── デスクトップアプリ起動 ──────────────────────────────────
echo [2/2] デスクトップアプリを起動中...
python backend\main.py
