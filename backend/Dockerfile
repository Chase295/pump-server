# ML Prediction Service Dockerfile
# Python 3.11-slim mit FastAPI
FROM python:3.11-slim

# Coolify Build Arguments (werden automatisch von Coolify übergeben)
ARG COOLIFY_URL
ARG COOLIFY_FQDN
ARG DB_DSN
ARG N8N_WEBHOOK_URL
ARG TRAINING_SERVICE_API_URL
ARG COOLIFY_BUILD_SECRETS_HASH

WORKDIR /app

# System-Dependencies installieren
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl wget supervisor && \
    rm -rf /var/lib/apt/lists/*

# Installiere Build-Dependencies für ML-Pakete
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies installieren
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY app/ ./app/

# Models-Verzeichnis erstellen (wird als Volume gemappt)
RUN mkdir -p /app/models

# Modell-Storage-Verzeichnis erstellen (für /tmp/models)
RUN mkdir -p /tmp/models && chmod 777 /tmp/models

# Log-Verzeichnis erstellen
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Config-Verzeichnis erstellen (für persistente UI-Konfiguration)
RUN mkdir -p /app/config && chmod 777 /app/config

# Supervisor Config für FastAPI + Streamlit
RUN printf '[supervisord]\n\
nodaemon=true\n\
\n\
[program:fastapi]\n\
command=uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
directory=/app\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/app/logs/fastapi.log\n\
stderr_logfile_maxbytes=50MB\n\
stderr_logfile_backups=5\n\
stdout_logfile=/app/logs/fastapi.log\n\
stdout_logfile_maxbytes=50MB\n\
stdout_logfile_backups=5\n\
\n\
[program:event-handler]\n\
command=/bin/bash -c "cd /app && PYTHONPATH=/app python app/prediction/event_handler.py"\n\
directory=/app\n\
autostart=true\n\
autorestart=true\n\
startretries=999999\n\
startsecs=5\n\
stopwaitsecs=10\n\
stderr_logfile=/app/logs/event_handler.log\n\
stderr_logfile_maxbytes=50MB\n\
stderr_logfile_backups=5\n\
stdout_logfile=/app/logs/event_handler.log\n\
stdout_logfile_maxbytes=50MB\n\
stdout_logfile_backups=5\n\
\n\
[program:streamlit]\n\
command=streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless=true\n\
directory=/app\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/app/logs/streamlit.log\n\
stderr_logfile_maxbytes=50MB\n\
stderr_logfile_backups=5\n\
stdout_logfile=/app/logs/streamlit.log\n\
stdout_logfile_maxbytes=50MB\n\
stdout_logfile_backups=5\n\
' > /etc/supervisor/conf.d/supervisord.conf

# Ports freigeben
EXPOSE 8000 8501

# Health Check (wget als Fallback für curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/api/health || curl -f http://localhost:8000/api/health || exit 1

# Graceful Shutdown
STOPSIGNAL SIGTERM

# Start Supervisor (startet FastAPI)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

