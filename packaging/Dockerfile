# Production image of the app (packaging/build.sh builds it, packaging/deploy.sh runs it). Secrets come from .env at
# `docker run`, never baked in. Build context = the repository root (.dockerignore there).
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONUTF8=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 MIGRATE=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN useradd --create-home app && mkdir -p data logs && chown -R app:app data logs
USER app

EXPOSE 8501
# MIGRATE=1: migrations first (scripts/migrate.py); deploy.sh migrates once and starts the replicas with MIGRATE=0.
# exec keeps Streamlit as PID 1 for docker stop.
CMD ["sh", "-c", "[ \"$MIGRATE\" = 0 ] || python scripts/migrate.py || exit 1; exec python -m streamlit run frontend/app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true --server.runOnSave=false --server.fileWatcherType=none"]
