@echo off
REM ==========================================================================
REM  restart_knowledgebase.bat - Restart the Knowledge Base (RAG) container, then check its health.
REM  Part of CyberQuest (Django) - YB_student_project_270889991. Double-click to run.
REM  Works with the Docker version (started by run.bat). Container names:
REM    cyberquest      = the web app        cyberquest-rag = the Knowledge Base
REM ==========================================================================
setlocal EnableExtensions
cd /d "%~dp0.."
echo.
echo  Restarting the Knowledge Base (RAG) service...
where docker >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not installed. & goto end )
docker info >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not running. Start it and try again. & goto end )
if not exist ".env" ( echo  [ERROR] No .env file. Run run.bat once first. & goto end )
docker compose up -d rag
docker compose restart rag
if errorlevel 1 ( echo  [ERROR] Could not restart the Knowledge Base. See the message above. & goto end )
echo  Waiting for the Knowledge Base to answer (up to 5 minutes)...
set /a TRIES=0
:wait
set /a TRIES+=1
docker exec cyberquest-rag python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:9000/health').status==200 else 1)" >nul 2>nul
if not errorlevel 1 goto ready
if %TRIES% GEQ 60 ( echo  [ERROR] The Knowledge Base did not answer. Check: docker compose logs rag & goto end )
timeout /t 5 /nobreak >nul
goto wait
:ready
echo  [OK] The Knowledge Base is healthy. Run check_knowledgebase.bat for a full check.

:end
echo.
pause
exit /b 0
