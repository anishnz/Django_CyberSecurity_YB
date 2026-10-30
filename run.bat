@echo off
REM ==========================================================================
REM  run.bat - Start CyberQuest (Django) with Docker. Double-click to run.
REM  Owner: Anish Shrestha (task A-04)
REM  1. Checks Docker   2. Finds a free port (8000-8020)   3. Makes .env with
REM  random secrets (first run)   4. Starts Docker   5. Waits for /health/
REM  6. Opens the browser.
REM ==========================================================================
setlocal EnableExtensions EnableDelayedExpansion
title CyberQuest (Django)
cd /d "%~dp0"

echo.
echo  ===========================================================
echo   CyberQuest - Learn. Play. Decide. Stay Cyber Safe.
echo   Mount Everest Digital Limited
echo  ===========================================================
echo.

where docker >nul 2>nul
if errorlevel 1 (
  echo  [!] Docker Desktop is not installed.
  echo      Install it from https://www.docker.com/products/docker-desktop
  echo      or double-click run_local.bat to run without Docker.
  pause & exit /b 1
)
docker info >nul 2>nul
if errorlevel 1 (
  echo  [!] Docker Desktop is not running. Start Docker Desktop, wait until it is ready, then run this again.
  pause & exit /b 1
)

REM ---- stop an older CyberQuest container, so its port is free again ------
REM (your data is kept: it lives in Docker volumes, not in the container)
docker compose down >nul 2>nul

REM ---- find a free port -------------------------------------------------
set "PORT="
for /L %%P in (8000,1,8020) do (
  if not defined PORT (
    netstat -ano | findstr /C:":%%P " | findstr /C:"LISTENING" >nul
    if errorlevel 1 (
      set "PORT=%%P"
    ) else (
      echo  Port %%P is busy - trying the next one...
    )
  )
)
if not defined PORT (
  echo  [!] Ports 8000-8020 are all busy. Close another program and try again.
  pause & exit /b 1
)
echo  Using port !PORT!

REM ---- first run: create .env with random secrets -----------------------
if not exist ".env" (
  echo  Creating .env with new random secrets...
  copy /Y ".env.example" ".env" >nul
  for /f "usebackq delims=" %%K in (`powershell -NoProfile -Command "$b=New-Object byte[] 48;[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b);[Convert]::ToBase64String($b)"`) do set "SECRET=%%K"
  for /f "usebackq delims=" %%K in (`powershell -NoProfile -Command "$b=New-Object byte[] 32;[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b);[Convert]::ToBase64String($b).Replace('+','-').Replace('/','_')"`) do set "FKEY=%%K"
  powershell -NoProfile -Command "(Get-Content .env) -replace '^DJANGO_SECRET_KEY=.*','DJANGO_SECRET_KEY=!SECRET!' -replace '^FIELD_ENCRYPTION_KEY=.*','FIELD_ENCRYPTION_KEY=!FKEY!' | Set-Content .env"
)

REM ---- start --------------------------------------------------------------
set "HOST_PORT=!PORT!"
echo  Building and starting CyberQuest (the first time takes a few minutes)...
docker compose up -d --build
if errorlevel 1 (
  echo  [!] Docker could not start CyberQuest. See the messages above.
  pause & exit /b 1
)

echo  Waiting for CyberQuest to be ready...
set /a TRIES=0
:wait
set /a TRIES+=1
for /f %%C in ('curl -s -o nul -w "%%{http_code}" http://127.0.0.1:!PORT!/health/ 2^>nul') do set "CODE=%%C"
if "!CODE!"=="200" goto ready
if "!CODE!"=="503" (
  echo  [!] CyberQuest is running, but a health check needs attention. See System status after you log in.
  goto ready
)
if !TRIES! GEQ 90 (
  echo  [!] CyberQuest did not answer. Check: docker compose logs web
  pause & exit /b 1
)
timeout /t 2 /nobreak >nul
goto wait

:ready
echo.
echo  CyberQuest is running at  http://127.0.0.1:!PORT!/
echo  Demo logins: http://127.0.0.1:!PORT!/accounts/demo-accounts/
echo  Stop it with:  docker compose down
echo.
start "" "http://127.0.0.1:!PORT!/"
pause
