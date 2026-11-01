@echo off
REM ==========================================================================
REM  pause_server.bat - Pause the CyberQuest web app. Run it again to resume.
REM  Part of CyberQuest (Django) - YB_student_project_270889991. Double-click to run.
REM  Works with the Docker version (started by run.bat). Container names:
REM    cyberquest      = the web app        cyberquest-rag = the Knowledge Base
REM ==========================================================================
setlocal EnableExtensions
cd /d "%~dp0.."
echo.
where docker >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not installed. & goto end )
docker info >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not running. Start it and try again. & goto end )
set "STATE="
for /f "delims=" %%S in ('docker inspect -f "{{.State.Status}}" cyberquest 2^>nul') do set "STATE=%%S"
if not defined STATE ( echo  [ERROR] The CyberQuest container is not there. Run run.bat first. & goto end )
if "%STATE%"=="paused" (
  docker unpause cyberquest >nul
  echo  [OK] CyberQuest is RESUMED. Run this file again to pause it.
  goto end
)
if "%STATE%"=="running" (
  docker pause cyberquest >nul
  echo  [OK] CyberQuest is PAUSED - the page will not answer. Run this file again to resume.
  goto end
)
echo  [NOTE] CyberQuest is "%STATE%", not running. Use run.bat or restart_server.bat.

:end
echo.
pause
exit /b 0
