#!/usr/bin/env bash
# run.sh - Start CyberQuest with Docker on macOS / Linux (same steps as run.bat).
set -euo pipefail
cd "$(dirname "$0")"
command -v docker >/dev/null || { echo "Docker is not installed."; exit 1; }
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
HOST_PORT=$PORT docker compose up -d --build
for i in $(seq 1 90); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/health/")" = "200" ] && break; sleep 2
done
echo "CyberQuest is running at http://127.0.0.1:$PORT/"
