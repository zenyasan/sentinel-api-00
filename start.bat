@echo off
chcp 65001 > nul
echo ===================================
echo  sentinel-api を起動します
echo ===================================
echo.

if "%~1"=="" (
    echo 使い方：対象のFastAPIプロジェクトフォルダを
    echo このファイルにドラッグ＆ドロップしてください。
    pause
    exit /b
)

echo 使用するモデルを選んでください
echo   1: Sonnet（標準・低コスト）
echo   2: Opus（高精度・高コスト）
echo.
set /p MODEL_CHOICE="番号を入力してEnter (1 or 2): "

if "%MODEL_CHOICE%"=="2" (
    set SENTINEL_MODEL=claude-opus-4-6
    echo Opus版で実行します
) else (
    set SENTINEL_MODEL=claude-sonnet-4-6
    echo Sonnet版で実行します
)

echo.
python -m sentinel_api run "%~1"

echo.
echo ===================================
echo  完了しました。SECURITY_STATUS.md を確認してください。
echo ===================================
pause
