#!/usr/bin/env bash
# run.sh - Start CyberQuest with Docker on macOS / Linux (same steps as run.bat).
set -euo pipefail
cd "$(dirname "$0")"
command -v docker >/dev/null || { echo "Docker is not installed."; exit 1; }
docker compose down >/dev/null 2>&1 || true   # free the port of an older CyberQuest container (data stays in volumes)
PORT=""
for p in $(seq 8000 8020); do
  if ! (echo > /dev/tcp/127.0.0.1/$p) 2>/dev/null; then PORT=$p; break; else echo "Port $p is busy - trying the next one..."; fi
done
[ -n "$PORT" ] || { echo "Ports 8000-8020 are busy."; exit 1; }
if [ ! -f .env ]; then
  cp .env.example .env
  SECRET=$(python3 -c "import secrets;print(secrets.token_urlsafe(48))")
  FKEY=$(python3 -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())")
  sed -i.bak "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$SECRET|; s|^FIELD_ENCRYPTION_KEY=.*|FIELD_ENCRYPTION_KEY=$FKEY|" .env && rm -f .env.bak
fi
# Knowledge Base (RAG) service key: add a random one if .env has none yet (older .env files)
if ! grep -q '^RAG_SERVICE_KEY=' .env; then echo 'RAG_SERVICE_KEY=change-me' >> .env; fi
if grep -qE '^RAG_SERVICE_KEY=(change-me)?$' .env; then
  RKEY=$(python3 -c "import secrets;print(secrets.token_urlsafe(32))")
  sed -i.bak "s|^RAG_SERVICE_KEY=.*|RAG_SERVICE_KEY=$RKEY|" .env && rm -f .env.bak
fi
echo "Building and starting CyberQuest and its Knowledge Base service (the first time takes 10-20 minutes)..."
HOST_PORT=$PORT docker compose up -d --build
READY=""
for i in $(seq 1 90); do
  CODE="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/health/" || true)"
  if [ "$CODE" = "200" ] || [ "$CODE" = "503" ]; then READY=$CODE; break; fi
  sleep 2
done
if [ -z "$READY" ]; then echo "CyberQuest did not answer. Check: docker compose logs web"; exit 1; fi
[ "$READY" = "503" ] && echo "CyberQuest is running, but a health check needs attention (see System status)."
echo "CyberQuest is running at http://127.0.0.1:$PORT/"
echo "Demo logins: http://127.0.0.1:$PORT/accounts/demo-accounts/"
echo "Stop it with: docker compose down"
if command -v open >/dev/null; then open "http://127.0.0.1:$PORT/"; elif command -v xdg-open >/dev/null; then xdg-open "http://127.0.0.1:$PORT/" >/dev/null 2>&1 || true; fi
