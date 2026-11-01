@echo off
REM ==========================================================================
REM  start_knowledgebase.bat - Start the Knowledge Base (RAG) container.
REM  Part of CyberQuest (Django) - YB_student_project_270889991. Double-click to run.
REM  Works with the Docker version (started by run.bat). Container names:
REM    cyberquest      = the web app        cyberquest-rag = the Knowledge Base
REM ==========================================================================
setlocal EnableExtensions
cd /d "%~dp0.."
echo.
echo  Starting the Knowledge Base (RAG) service...
where docker >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not installed. & goto end )
docker info >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not running. Start it and try again. & goto end )
if not exist ".env" ( echo  [ERROR] No .env file. Run run.bat once first. & goto end )
docker compose up -d rag
if errorlevel 1 ( echo  [ERROR] Could not start the Knowledge Base. See the message above. & goto end )
echo  [OK] The Knowledge Base is starting. The first start can take a few minutes.
echo  Check it with check_knowledgebase.bat

:end
echo.
pause
exit /b 0
