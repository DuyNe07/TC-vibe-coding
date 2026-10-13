# Production image of the app (built and started by build.sh). Secrets come from .env at `docker run`, never baked in.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONUTF8=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN useradd --create-home app && mkdir -p data logs && chown -R app:app data logs
USER app

EXPOSE 8501
# migrations first (scripts/migrate.py), then the app; exec keeps Streamlit as PID 1 for docker stop
CMD ["sh", "-c", "python scripts/migrate.py && exec python -m streamlit run frontend/app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true --server.runOnSave=false --server.fileWatcherType=none"]
