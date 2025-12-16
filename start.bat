@echo off
echo ==========================================
echo   Система організації студентських подій
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
    echo [OK] Віртуальне середовище створено
)

REM Активація віртуального середовища
echo.
echo Активація віртуального середовища...
call venv\Scripts\activate.bat

REM Встановлення залежностей
echo.
echo Перевірка та встановлення залежностей...
pip install -r requirements.txt

REM Перевірка .env файлу
if not exist ".env" (
    echo.
    echo [УВАГА] Файл .env не знайдено!
    echo Створіть файл .env на основі .env.example
    echo та налаштуйте параметри підключення до MySQL
    pause
)

REM Запуск додатку
echo.
echo ==========================================
echo   Запуск веб-додатку...
echo ==========================================
echo.
echo Додаток буде доступний за адресою:
echo http://localhost:5000
echo.
echo Для зупинки натисніть Ctrl+C
echo.

python app.py

pause
