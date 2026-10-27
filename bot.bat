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

:: Sync latest bot_cli.py from server (coba local LAN 192.168.1.17:5000, fallback ke domain publik autobotix.my.id)
echo [1/2] Menghubungkan dan menyinkronkan bot_cli.py terbaru...
curl.exe -s --connect-timeout 2 http://192.168.1.17:5000/download/bot_cli.py -o "%~dp0bot_cli.py.tmp"
if not exist "%~dp0bot_cli.py.tmp" (
    curl.exe -s --connect-timeout 4 https://autobotix.my.id/download/bot_cli.py -o "%~dp0bot_cli.py.tmp"
)
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
    echo [ERROR] Gagal mengunduh bot_cli.py dari server!
    echo Pastikan server aktif atau unduh manual dari: https://autobotix.my.id/download/bot_cli.py
    pause
    exit /b 1
)

:: Run client with all passed arguments
echo [2/2] Memulai CLI Client...
python "%~dp0bot_cli.py" %*

if "%~1"=="" (
    pause
)
