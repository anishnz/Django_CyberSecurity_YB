@echo off
REM ==========================================================================
REM  run_local.bat - Start CyberQuest WITHOUT Docker (needs Python 3.10+).
REM  Owner: Anish Shrestha (task A-04).
REM  1. Checks Python 3.10+   2. Finds a free port (8000-8020)
REM  3. Makes .venv and installs packages (only when requirements.txt changes,
REM     so it also starts with no internet)   4. Makes .env with random secrets
REM  5. Prepares the database   6. Sets up and starts the Knowledge Base (RAG)
REM     service in its own small window (optional: CyberQuest runs without it)
REM  7. Starts waitress and opens the browser only when CyberQuest answers.
REM ==========================================================================
setlocal EnableExtensions EnableDelayedExpansion
title CyberQuest (Django) - local
cd /d "%~dp0"
set "HERE=%CD%"

echo.
echo  ===========================================================
echo   CyberQuest - Learn. Play. Decide. Stay Cyber Safe.
echo   Mount Everest Digital Limited
echo  ===========================================================
echo.

REM ---- 1. Python 3.10 or newer ------------------------------------------
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo  [ERROR] Python is not installed. Get it from https://www.python.org/downloads/ ^(tick "Add Python to PATH"^).
  pause & exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
  echo  [ERROR] CyberQuest needs Python 3.10 or newer. Install it from https://www.python.org/downloads/
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
  echo  [ERROR] Ports 8000-8020 are all busy. Close another program and try again.
  pause & exit /b 1
)
echo  Using port !PORT!

REM ---- 3. virtual environment and packages ---------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo  Creating virtual environment...
  %PY% -m venv .venv || ( echo  [ERROR] Could not create .venv & pause & exit /b 1 )
)
call ".venv\Scripts\activate.bat"
set "NEED_INSTALL=1"
if exist ".venv\requirements.installed" (
  fc /b "requirements.txt" ".venv\requirements.installed" >nul 2>nul && set "NEED_INSTALL=0"
)
if "!NEED_INSTALL!"=="1" (
  echo  Installing packages - the first time takes a few minutes and needs internet...
  python -m pip install -q --upgrade pip >nul 2>nul
  python -m pip install -q -r requirements.txt || ( echo  [ERROR] pip install failed. Check your internet and run this again. & pause & exit /b 1 )
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

REM ---- Knowledge Base (RAG) service key: add a random one if .env has none yet ---------
powershell -NoProfile -Command "$p='.env'; if(-not ((Get-Content $p) -match '^RAG_SERVICE_KEY=')){Add-Content $p 'RAG_SERVICE_KEY=change-me'}; if((Get-Content $p) -match '^RAG_SERVICE_KEY=(change-me)?$'){$b=New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); $k=[Convert]::ToBase64String($b).Replace('+','-').Replace('/','_').TrimEnd('='); (Get-Content $p) -replace '^RAG_SERVICE_KEY=.*',('RAG_SERVICE_KEY='+$k) | Set-Content $p; Write-Host '  Created a key for the Knowledge Base service.'}"

REM ---- 5. database, static files, demo data ---------------------------------
set "DJANGO_SETTINGS_MODULE=cyberquest.settings.prod"
set "DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:!PORT!,http://localhost:!PORT!"
set "SITE_URL=http://127.0.0.1:!PORT!"
echo  Preparing the database...
python manage.py migrate --noinput || ( echo  [ERROR] Database setup failed & pause & exit /b 1 )
python manage.py collectstatic --noinput -v0
python manage.py seed_demo

REM ---- 6. Knowledge Base (RAG) service - optional ---------------------------------
set "RAG_READY=0"
set "RAGPORT="
for /L %%P in (9000,1,9020) do (
  if not defined RAGPORT (
    netstat -ano | findstr /C:":%%P " | findstr /C:"LISTENING" >nul
    if errorlevel 1 set "RAGPORT=%%P"
  )
)
if defined RAGPORT (call :start_rag) else (echo  [NOTE] Ports 9000-9020 are busy - CyberQuest starts without the Knowledge Base.)

REM ---- 7. open the browser when the server answers, then start the server ----
REM A small hidden PowerShell job asks /health/ every half second (up to 60 s).
REM Any answer means the server is up (503 = up, but a health check needs attention).
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "$u='http://127.0.0.1:!PORT!/'; for($i=0; $i -lt 120; $i++){ try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 ($u + 'health/') | Out-Null; break } catch { if($_.Exception.Response){ break } }; Start-Sleep -Milliseconds 500 }; Start-Process $u"

echo.
echo  ===========================================================
echo   CyberQuest is starting at  http://127.0.0.1:!PORT!/
echo   Demo logins: http://127.0.0.1:!PORT!/accounts/demo-accounts/
echo   Your browser opens by itself when CyberQuest is ready.
echo   Keep this window open. Press CTRL+C to stop CyberQuest.
echo   The Knowledge Base runs in the small "CyberQuest Knowledge Base" window.
echo  ===========================================================
echo.
waitress-serve --host=127.0.0.1 --port=!PORT! --threads=8 cyberquest.wsgi:application
echo.
echo  CyberQuest has stopped.
if "!RAG_READY!"=="1" taskkill /fi "WINDOWTITLE eq CyberQuest Knowledge Base*" /f >nul 2>nul
pause
exit /b 0

REM ===========================================================================
REM  :start_rag - make the Knowledge Base environment (first time only) and start
REM  it in a small window. Any problem only switches the Knowledge Base off.
REM ===========================================================================
:start_rag
set "RPY=!HERE!\cyberquest-rag\.venv\Scripts\python.exe"
if not exist "!RPY!" (
  echo  Creating the Knowledge Base environment...
  %PY% -m venv "!HERE!\cyberquest-rag\.venv" || goto rag_fail
)
set "RAG_NEED=1"
if exist "cyberquest-rag\.venv\requirements.installed" (
  fc /b "cyberquest-rag\requirements.txt" "cyberquest-rag\.venv\requirements.installed" >nul 2>nul && set "RAG_NEED=0"
)
if "!RAG_NEED!"=="1" (
  echo  Installing Knowledge Base packages - the first time downloads about 1 GB and takes 10-20 minutes...
  "!RPY!" -m pip install -q --upgrade pip >nul 2>nul
  "!RPY!" -m pip install -q torch --index-url https://download.pytorch.org/whl/cpu || goto rag_fail
  "!RPY!" -m pip install -q -r "cyberquest-rag\requirements.txt" || goto rag_fail
  copy /Y "cyberquest-rag\requirements.txt" "cyberquest-rag\.venv\requirements.installed" >nul
)
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if "%%A"=="RAG_SERVICE_KEY" set "RAG_SERVICE_KEY=%%B"
  if "%%A"=="RAG_LLM_API_KEY" set "RAG_LLM_API_KEY=%%B"
)
set "RAG_DATA_DIR=!HERE!\cyberquest-rag\data"
set "HF_HOME=!HERE!\cyberquest-rag\data\hf"
set "RAG_BASE_URL=http://127.0.0.1:!RAGPORT!"
start "CyberQuest Knowledge Base" /min /d "!HERE!\cyberquest-rag" "!RPY!" -m uvicorn app.main:app --host 127.0.0.1 --port !RAGPORT!
set "RAG_READY=1"
echo  Knowledge Base service starting on port !RAGPORT! in its own window (the first start downloads a language model).
exit /b 0

:rag_fail
echo  [NOTE] The Knowledge Base service could not be set up (check the internet). CyberQuest runs without it.
exit /b 0
