@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
cls

echo ==========================================
echo   UniMeet - Система організації подій
echo ==========================================
echo.

REM Перевірка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ПОМИЛКА] Python не встановлено!
    echo Завантажте Python з https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python встановлено

REM Перевірка віртуального середовища
if not exist "venv\" (
    echo.
    echo Створення віртуального середовища...
    python -m venv venv
    if errorlevel 1 (
        echo [ПОМИЛКА] Не вдалось створити віртуальне середовище!
        pause
        exit /b 1
    )
    echo [OK] Віртуальне середовище створено
)

REM Активація віртуального середовища
echo.
echo Активація віртуального середовища...
if not exist "venv\Scripts\python.exe" (
    echo [ПОМИЛКА] Віртуальне середовище пошкоджено!
    pause
    exit /b 1
)

REM Встановлення залежностей
echo.
echo Перевірка та встановлення залежностей...
call venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
    echo [ПОМИЛКА] Не вдалось оновити pip!
    pause
    exit /b 1
)

call venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ПОМИЛКА] Не вдалось встановити залежності!
    pause
    exit /b 1
)

REM Перевірка .env файлу
echo.
echo Перевірка конфігурації бази даних...
if not exist ".env" (
    echo [УВАГА] Файл .env не знайдено!
    echo.
    echo Будь ласка, налаштуйте параметри підключення до MySQL:
    echo.
    copy .env.example .env >nul
    echo [OK] Файл .env створено з шаблону
    echo.
    echo Відредагуйте файл .env та вкажіть:
    echo - MYSQL_HOST (адреса сервера БД, за замовчуванням localhost)
    echo - MYSQL_USER (користувач БД)
    echo - MYSQL_PASSWORD (пароль)
    echo - MYSQL_DB (назва бази даних)
    echo.
    pause
) else (
    echo [OK] Конфігурація знайдена
)

REM Запуск додатку
echo.
echo ==========================================
echo   Запуск веб-додатку...
echo ==========================================
echo.
call venv\Scripts\python.exe app.py

endlocal
pause
