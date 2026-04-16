@echo off
REM commit.bat - Git add, commit, and push
REM Usage: commit.bat "commit message"
REM        (no argument = auto timestamp message)

set MSG=%~1
if "%MSG%"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DSTR=%%a-%%b-%%c
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TSTR=%%a:%%b
    set MSG=chore: save progress %DSTR% %TSTR%
)

echo [commit.bat] Committing: %MSG%

git add -A
if errorlevel 1 ( echo [ERROR] git add failed. & pause & exit /b 1 )

git commit -m "%MSG%"
if errorlevel 1 ( echo [INFO] Nothing to commit or commit failed. & pause & exit /b 0 )

git push
if errorlevel 1 ( echo [ERROR] Push failed. & pause & exit /b 1 )

echo [commit.bat] Done.
