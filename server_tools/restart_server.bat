@echo off
REM ==========================================================================
REM  restart_server.bat - Restart the CyberQuest web app (data is kept).
REM  Part of CyberQuest (Django) - YB_student_project_270889991. Double-click to run.
REM  Works with the Docker version (started by run.bat). Container names:
REM    cyberquest      = the web app        cyberquest-rag = the Knowledge Base
REM ==========================================================================
setlocal EnableExtensions
cd /d "%~dp0.."
echo.
echo  Restarting the CyberQuest web app...
where docker >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not installed. & goto end )
docker info >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not running. Start it and try again. & goto end )
docker compose restart web
if errorlevel 1 ( echo  [ERROR] Could not restart. Try run.bat to build and start everything. & goto end )
echo  Waiting for CyberQuest to answer...
set /a TRIES=0
:wait
set /a TRIES+=1
for /f "tokens=2 delims=:" %%P in ('docker compose port web 8000 2^>nul') do set "PORT=%%P"
if not defined PORT set "PORT=8000"
set "CODE="
for /f %%C in ('curl -s -o nul -w "%%{http_code}" http://127.0.0.1:%PORT%/health/ 2^>nul') do set "CODE=%%C"
if "%CODE%"=="200" goto ready
if "%CODE%"=="503" ( echo  [NOTE] CyberQuest is running, but a health check needs attention. & goto ready )
if %TRIES% GEQ 60 ( echo  [ERROR] CyberQuest did not answer. Check: docker compose logs web & goto end )
timeout /t 2 /nobreak >nul
goto wait
:ready
echo  [OK] CyberQuest is running at  http://127.0.0.1:%PORT%/

:end
echo.
pause
exit /b 0
