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
    echo target_path.txt �ɑΏۃt�H���_�̃p�X���L�ڂ��Ă�������
    pause
    exit /b
)

if not exist "!TARGET_PATH!" (
    echo �w�肳�ꂽ�p�X��������܂���: !TARGET_PATH!
    pause
    exit /b
)

set SENTINEL_MODEL=claude-sonnet-4-6
echo Sonnet�łŎ��s���܂�
echo.
python -m sentinel_api run "!TARGET_PATH!"

echo.
echo �������܂����BSECURITY_STATUS.md ���m�F���Ă�������
pause
