@echo off
setlocal

rem Quick launcher for UniMeet (dev mode)
if not exist venv\Scripts\python.exe (
    echo [INFO] Creating virtual environment...
    python -m venv venv || goto :error
)

call venv\Scripts\activate || goto :error
python -m pip install -r requirements.txt || goto :error

set FLASK_APP=app.py
set FLASK_ENV=development
python app.py
goto :eof

:error
echo [ERROR] Startup failed. Check the messages above.
exit /b 1
