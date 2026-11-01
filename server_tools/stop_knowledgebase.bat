@echo off
REM ==========================================================================
REM  stop_knowledgebase.bat - Stop the Knowledge Base (RAG) container. CyberQuest keeps working without it.
REM  Part of CyberQuest (Django) - YB_student_project_270889991. Double-click to run.
REM  Works with the Docker version (started by run.bat). Container names:
REM    cyberquest      = the web app        cyberquest-rag = the Knowledge Base
REM ==========================================================================
setlocal EnableExtensions
cd /d "%~dp0.."
echo.
echo  Stopping the Knowledge Base (RAG) service...
where docker >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not installed. & goto end )
docker info >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not running. Start it and try again. & goto end )
docker compose stop rag
if errorlevel 1 ( echo  [ERROR] Could not stop the Knowledge Base. See the message above. & goto end )
echo  [OK] The Knowledge Base is stopped. Its documents are kept in a Docker volume.
echo  (If you started CyberQuest with run_local.bat, close the small "CyberQuest Knowledge Base" window instead.)

:end
echo.
pause
exit /b 0
