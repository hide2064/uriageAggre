@echo off
REM ============================================================
REM  commit.bat — git commit & push スクリプト
REM ============================================================
REM  使い方:
REM    commit.bat "コミットメッセージ"
REM
REM  引数なしで実行した場合は自動タイムスタンプのメッセージを使います。
REM ============================================================

REM メッセージが引数で渡された場合はそれを使用
set MSG=%~1
if "%MSG%"=="" (
    REM 引数なし → 現在日時をメッセージに使用
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATE=%%a-%%b-%%c
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TIME=%%a:%%b
    set MSG=chore: save progress %DATE% %TIME%
)

echo [commit.bat] コミット & プッシュを実行します...
echo メッセージ: %MSG%
echo.

REM ── ステージング ────────────────────────────────────────────
git add -A
if errorlevel 1 (
    echo [ERROR] git add に失敗しました。
    pause
    exit /b 1
)

REM ── コミット ────────────────────────────────────────────────
git commit -m "%MSG%"
if errorlevel 1 (
    echo [INFO] コミットするものがないか、コミットに失敗しました。
    pause
    exit /b 0
)

REM ── プッシュ ────────────────────────────────────────────────
git push
if errorlevel 1 (
    echo [ERROR] プッシュに失敗しました。リモートの設定を確認してください。
    pause
    exit /b 1
)

echo.
echo [commit.bat] 完了しました。
