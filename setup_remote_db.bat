@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo ==========================================
echo   Налаштування Remote MySQL Database
echo ==========================================
echo.

REM Перевірка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ПОМИЛКА] Python не встановлено!
    pause
    exit /b 1
)

REM Створення віртуального середовища якщо його немає
if not exist "venv\" (
    echo Створення віртуального середовища...
    python -m venv venv
)

REM Встановлення залежностей
echo.
echo Встановлення залежностей...
call venv\Scripts\python.exe -m pip install --quiet mysql-connector-python python-dotenv colorama

REM Запуск утиліти
echo.
call venv\Scripts\python.exe setup_remote_db.py

pause
