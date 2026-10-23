@echo off
REM ==========================================================================
REM  run_local.bat - Start CyberQuest WITHOUT Docker (needs Python 3.10+).
REM  Owner: Anish Shrestha (task A-04). Finds a free port, makes a virtual
REM  environment, installs packages, prepares the database and starts waitress.
REM ==========================================================================
setlocal EnableExtensions EnableDelayedExpansion
title CyberQuest (Django) - local
cd /d "%~dp0"

where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo  [!] Python is not installed. Get it from https://www.python.org/downloads/ ^(tick "Add to PATH"^).
  pause & exit /b 1
)

set "PORT="
for /L %%P in (8000,1,8020) do (
  if not defined PORT (
    netstat -ano | findstr /C:":%%P " | findstr /C:"LISTENING" >nul
    if errorlevel 1 (set "PORT=%%P") else (echo  Port %%P is busy - trying the next one...)
  )
)
if not defined PORT ( echo  [!] Ports 8000-8020 are busy. & pause & exit /b 1 )

if not exist ".venv\Scripts\python.exe" (
  echo  Creating virtual environment...
  %PY% -m venv .venv || ( echo  [!] Could not create .venv & pause & exit /b 1 )
)
call ".venv\Scripts\activate.bat"
echo  Installing packages (first time only takes a minute)...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt || ( echo  [!] pip install failed & pause & exit /b 1 )

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  for /f "usebackq delims=" %%K in (`python -c "import secrets;print(secrets.token_urlsafe(48))"`) do set "SECRET=%%K"
  for /f "usebackq delims=" %%K in (`python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"`) do set "FKEY=%%K"
  powershell -NoProfile -Command "(Get-Content .env) -replace '^DJANGO_SECRET_KEY=.*','DJANGO_SECRET_KEY=!SECRET!' -replace '^FIELD_ENCRYPTION_KEY=.*','FIELD_ENCRYPTION_KEY=!FKEY!' | Set-Content .env"
)

set "DJANGO_SETTINGS_MODULE=cyberquest.settings.prod"
set "DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:!PORT!,http://localhost:!PORT!"
set "SITE_URL=http://127.0.0.1:!PORT!"
python manage.py migrate --noinput || ( echo  [!] Database setup failed & pause & exit /b 1 )
python manage.py collectstatic --noinput -v0
python manage.py seed_demo

echo.
echo  CyberQuest is running at  http://127.0.0.1:!PORT!/   (press CTRL+C to stop)
echo  Demo logins: http://127.0.0.1:!PORT!/accounts/demo-accounts/
start "" "http://127.0.0.1:!PORT!/"
waitress-serve --host=127.0.0.1 --port=!PORT! --threads=8 cyberquest.wsgi:application
pause
