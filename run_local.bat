@echo off
REM ==========================================================================
REM  run_local.bat - Start CyberQuest WITHOUT Docker (needs Python 3.10+).
REM  Owner: Anish Shrestha (task A-04).
REM  1. Checks Python 3.10+   2. Finds a free port (8000-8020)
REM  3. Makes .venv and installs packages (only when requirements.txt changes,
REM     so it also starts with no internet)   4. Makes .env with random secrets
REM  5. Prepares the database   6. Starts waitress and opens the browser only
REM     when CyberQuest answers on /health/.
REM ==========================================================================
setlocal EnableExtensions EnableDelayedExpansion
title CyberQuest (Django) - local
cd /d "%~dp0"

echo.
echo  ===========================================================
echo   CyberQuest - Learn. Play. Decide. Stay Cyber Safe.
echo   Mount Everest Digital Limited ^| YB_student_project_270889991
echo  ===========================================================
echo.

REM ---- 1. Python 3.10 or newer ------------------------------------------
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo  [!] Python is not installed. Get it from https://www.python.org/downloads/ ^(tick "Add Python to PATH"^).
  pause & exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
  echo  [!] CyberQuest needs Python 3.10 or newer. Install it from https://www.python.org/downloads/
  pause & exit /b 1
)

REM ---- 2. find a free port -------------------------------------------------
set "PORT="
for /L %%P in (8000,1,8020) do (
  if not defined PORT (
    netstat -ano | findstr /C:":%%P " | findstr /C:"LISTENING" >nul
    if errorlevel 1 (set "PORT=%%P") else (echo  Port %%P is busy - trying the next one...)
  )
)
if not defined PORT (
  echo  [!] Ports 8000-8020 are all busy. Close another program and try again.
  pause & exit /b 1
)
echo  Using port !PORT!

REM ---- 3. virtual environment and packages ---------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo  Creating virtual environment...
  %PY% -m venv .venv || ( echo  [!] Could not create .venv & pause & exit /b 1 )
)
call ".venv\Scripts\activate.bat"
set "NEED_INSTALL=1"
if exist ".venv\requirements.installed" (
  fc /b "requirements.txt" ".venv\requirements.installed" >nul 2>nul && set "NEED_INSTALL=0"
)
if "!NEED_INSTALL!"=="1" (
  echo  Installing packages - the first time takes a few minutes and needs internet...
  python -m pip install -q --upgrade pip >nul 2>nul
  python -m pip install -q -r requirements.txt || ( echo  [!] pip install failed. Check your internet and run this again. & pause & exit /b 1 )
  copy /Y "requirements.txt" ".venv\requirements.installed" >nul
) else (
  echo  Packages are already installed.
)

REM ---- 4. first run: .env with random secrets --------------------------------
if not exist ".env" (
  echo  Creating .env with new random secrets...
  copy /Y ".env.example" ".env" >nul
  for /f "usebackq delims=" %%K in (`python -c "import secrets;print(secrets.token_urlsafe(48))"`) do set "SECRET=%%K"
  for /f "usebackq delims=" %%K in (`python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"`) do set "FKEY=%%K"
  powershell -NoProfile -Command "(Get-Content .env) -replace '^DJANGO_SECRET_KEY=.*','DJANGO_SECRET_KEY=!SECRET!' -replace '^FIELD_ENCRYPTION_KEY=.*','FIELD_ENCRYPTION_KEY=!FKEY!' | Set-Content .env"
)

REM ---- 5. database, static files, demo data ---------------------------------
set "DJANGO_SETTINGS_MODULE=cyberquest.settings.prod"
set "DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:!PORT!,http://localhost:!PORT!"
set "SITE_URL=http://127.0.0.1:!PORT!"
echo  Preparing the database...
python manage.py migrate --noinput || ( echo  [!] Database setup failed & pause & exit /b 1 )
python manage.py collectstatic --noinput -v0
python manage.py seed_demo

REM ---- 6. open the browser when the server answers, then start the server ----
REM A small hidden PowerShell job asks /health/ every half second (up to 60 s).
REM Any answer means the server is up (503 = up, but a health check needs attention).
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "$u='http://127.0.0.1:!PORT!/'; for($i=0; $i -lt 120; $i++){ try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 ($u + 'health/') | Out-Null; break } catch { if($_.Exception.Response){ break } }; Start-Sleep -Milliseconds 500 }; Start-Process $u"

echo.
echo  ===========================================================
echo   CyberQuest is starting at  http://127.0.0.1:!PORT!/
echo   Demo logins: http://127.0.0.1:!PORT!/accounts/demo-accounts/
echo   Your browser opens by itself when CyberQuest is ready.
echo   Keep this window open. Press CTRL+C to stop CyberQuest.
echo  ===========================================================
echo.
waitress-serve --host=127.0.0.1 --port=!PORT! --threads=8 cyberquest.wsgi:application
echo.
echo  CyberQuest has stopped.
pause
