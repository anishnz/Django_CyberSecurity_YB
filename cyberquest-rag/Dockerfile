# CyberQuest Knowledge Base (RAG) service - Docker image
# Started by docker-compose next to the CyberQuest web app. Only the web app can reach it
# (no port is published to the computer). The embedding model is downloaded on the first
# start and kept in the volume (HF_HOME), so later starts are fast and work offline.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RAG_DATA_DIR=/data \
    HF_HOME=/data/hf

WORKDIR /srv
COPY requirements.txt .
# CPU-only PyTorch first: a much smaller download than the default GPU build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY cybersecurity_knowledge_base_L0-L6_English.md .
RUN useradd --create-home rag && mkdir -p /data && chown -R rag:rag /data /srv
USER rag

EXPOSE 9000
HEALTHCHECK --interval=30s --timeout=5s --start-period=300s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:9000/health').status==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
