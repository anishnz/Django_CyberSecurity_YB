@echo off
REM ==========================================================================
REM  check_knowledgebase.bat - Check the Knowledge Base (RAG) health and its AI model.
REM  Part of CyberQuest (Django) - YB_student_project_270889991. Double-click to run.
REM  Works with the Docker version (started by run.bat). Container names:
REM    cyberquest      = the web app        cyberquest-rag = the Knowledge Base
REM ==========================================================================
setlocal EnableExtensions
cd /d "%~dp0.."
echo.
echo  ===== CyberQuest Knowledge Base check =====
where docker >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not installed. & goto end )
docker info >nul 2>nul
if errorlevel 1 ( echo  [ERROR] Docker Desktop is not running. Start it and try again. & goto end )

echo.
echo  1. Container
set "STATE="
for /f "delims=" %%S in ('docker inspect -f "{{.State.Status}}" cyberquest-rag 2^>nul') do set "STATE=%%S"
if not defined STATE ( echo     [FAIL] The container is not there. Run start_knowledgebase.bat & goto end )
echo     Status: %STATE%
set "HEALTH="
for /f "delims=" %%S in ('docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" cyberquest-rag 2^>nul') do set "HEALTH=%%S"
echo     Docker health: %HEALTH%
if not "%STATE%"=="running" ( echo     [FAIL] Not running. Run start_knowledgebase.bat & goto end )

echo.
echo  2. Service answers (/health)
docker exec cyberquest-rag python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:9000/health').status==200 else 1)" >nul 2>nul
if errorlevel 1 ( echo     [FAIL] The service does not answer yet. The first start downloads a language model - wait and try again. & goto end )
echo     [OK] The service answers.

echo.
echo  3. AI model setting (/v1/model-info, uses the secret service key inside the container)
docker exec cyberquest-rag python -c "import os,urllib.request as u; r=u.Request('http://127.0.0.1:9000/v1/model-info',headers={'X-Service-Key':os.environ['RAG_SERVICE_KEY'],'X-User-Role':'super_admin'}); print('    ',u.urlopen(r,timeout=10).read().decode())"
if errorlevel 1 ( echo     [FAIL] Could not read the model setting. Check: docker compose logs rag & goto end )
echo     [OK] The service key and the model setting work.

echo.
echo  4. Test question to the AI model (optional - uses your AI key and may cost a little)
choice /c YN /n /m "     Ask a test question now? [Y/N] "
if errorlevel 2 goto web
docker exec cyberquest-rag python -c "import os,json,urllib.request as u; b=json.dumps({'question':'What is phishing?','top_k':3}).encode(); r=u.Request('http://127.0.0.1:9000/v1/ask',data=b,headers={'X-Service-Key':os.environ['RAG_SERVICE_KEY'],'X-User-Role':'student','Content-Type':'application/json'}); d=json.loads(u.urlopen(r,timeout=120).read().decode()); print('     Answer:',d['answer'][:300].replace(chr(10),' ')); print('     Sources found:',len(d['sources']))"
if errorlevel 1 ( echo     [FAIL] The question failed. The AI key may be missing or wrong - see docs\KNOWLEDGE_BASE.md & goto web )
echo     [OK] The AI model answered from the knowledge base.

:web
echo.
echo  5. CyberQuest web app can reach it
set "PORT="
for /f "tokens=2 delims=:" %%P in ('docker compose port web 8000 2^>nul') do set "PORT=%%P"
if not defined PORT ( echo     [NOTE] The web app is not running, so this step is skipped. & goto end )
for /f %%C in ('curl -s -o nul -w "%%{http_code}" http://127.0.0.1:%PORT%/health/ 2^>nul') do set "CODE=%%C"
echo     Web app /health/ answered: %CODE%  (200 = all good, 503 = see System status after you log in)

:end
echo.
pause
exit /b 0
