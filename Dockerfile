# CyberQuest (Django) - Docker image
# Owner: Anish Shrestha (task A-03). Python 3.12 slim, non-root user, waitress server.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=cyberquest.settings.prod \
    SQLITE_PATH=/data/db/cyberquest.sqlite3 \
    MEDIA_ROOT=/data/media \
    LOG_DIR=/data/logs

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --create-home cyberquest \
    && mkdir -p /data/db /data/media /data/logs /app/backups /app/staticfiles \
    && chown -R cyberquest:cyberquest /data /app \
    && chmod +x docker/entrypoint.sh

USER cyberquest
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/').status==200 else 1)"

ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8000", "--threads=8", "cyberquest.wsgi:application"]
