@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

set TARGET_PATH=
for /f "usebackq eol=# delims=" %%L in ("%~dp0target_path.txt") do (
    if not defined TARGET_PATH (
        set TARGET_PATH=%%L
    )
)

if not defined TARGET_PATH (
    echo target_path.txt に対象フォルダのパスを記載してください
    pause
    exit /b
)

if not exist "!TARGET_PATH!" (
    echo 指定されたパスが見つかりません: !TARGET_PATH!
    pause
    exit /b
)

set SENTINEL_MODEL=claude-sonnet-4-6
echo Sonnet版で実行します
echo.
python -m sentinel_api run "!TARGET_PATH!"

echo.
echo 完了しました。SECURITY_STATUS.md を確認してください
pause
