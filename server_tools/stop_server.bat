@echo off
REM ==========================================================================
REM  stop_server.bat - Stop the CyberQuest web app (the Knowledge Base keeps running).
REM  Part of CyberQuest (Django) - YB_student_project_270889991. Double-click to run.
REM  Works with the Docker version (started by run.bat). Container names:
REM    cyberquest      = the web app        cyberquest-rag = the Knowledge Base
REM ==========================================================================
setlocal EnableExtensions
cd /d "%~dp0.."
echo.
echo  Stopping the CyberQuest web app...
where docker >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not installed. & goto end )
docker info >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not running. Start it and try again. & goto end )
docker compose stop web
if errorlevel 1 ( echo  [ERROR] Could not stop CyberQuest. See the message above. & goto end )
echo  [OK] CyberQuest is stopped. Your data is kept in Docker volumes.
echo  Start it again with run.bat or restart_server.bat.

:end
echo.
pause
exit /b 0
