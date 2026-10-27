@echo off
setlocal enabledelayedexpansion
title AutoBotix Review Automation - Windows CLI
color 0B

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 tidak ditemukan di sistem Windows ini!
    echo Silakan install Python 3 dari https://www.python.org/downloads/
    echo Pastikan centang "Add Python to PATH" saat menginstall.
    pause
    exit /b 1
)

:: Sync latest bot_cli.py from server (192.168.1.17)
echo [1/2] Menghubungkan ke server AutoBotix (192.168.1.17)...
curl.exe -s --connect-timeout 2 http://192.168.1.17:5000/download/bot_cli.py -o "%~dp0bot_cli.py.tmp"
if exist "%~dp0bot_cli.py.tmp" (
    for %%A in ("%~dp0bot_cli.py.tmp") do (
        if %%~zA gtr 1000 (
            move /y "%~dp0bot_cli.py.tmp" "%~dp0bot_cli.py" >nul 2>&1
        ) else (
            del "%~dp0bot_cli.py.tmp" >nul 2>&1
        )
    )
)

if not exist "%~dp0bot_cli.py" (
    echo [ERROR] Gagal mengunduh bot_cli.py dari server! Pastikan IP 192.168.1.17 aktif.
    pause
    exit /b 1
)

:: Run client with all passed arguments
echo [2/2] Memulai CLI Client...
python "%~dp0bot_cli.py" %*

if "%~1"=="" (
    pause
)
