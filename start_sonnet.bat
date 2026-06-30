@echo off
setlocal enabledelayedexpansion

set TARGET_PATH=
set "_TMPFILE=%TEMP%\sentinel_%RANDOM%.tmp"
(type "%~dp0target_path.txt" & echo.) > "%_TMPFILE%"
for /f "usebackq eol=# delims=" %%L in ("%_TMPFILE%") do (
    if not defined TARGET_PATH (
        set TARGET_PATH=%%L
    )
)
del "%_TMPFILE%" 2>nul

if not defined TARGET_PATH (
    echo target_path.txt に対象フォルダのパスが記載されていません
    pause
    exit /b
)

if not exist "!TARGET_PATH!" (
    echo 指定されたパスが見つかりません: !TARGET_PATH!
    pause
    exit /b
)

set SENTINEL_MODEL=claude-sonnet-4-6
echo Sonnet で実行します
echo.
python -m sentinel_api run "!TARGET_PATH!"

echo.
echo 完了しました。SECURITY_STATUS.md を確認してください
pause
