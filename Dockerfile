# ── Imagen: pipeline HireSignal ───────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates wget curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --default-timeout=300 --no-cache-dir -r requirements.txt

# Scrapling (StealthyFetcher) usa patchright (Chromium) para el fallback de
# Getonbrd cuando el endpoint HTML bloquea requests. Mismo patrón que
# AfterDrive_Intelligence: browser en /ms-playwright para usuario no-root.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN python -m patchright install --with-deps chromium && \
    python -c "from scrapling.cli import install; install([], standalone_mode=False)"

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

COPY hire_signal/ ./hire_signal/
COPY run.py .
COPY scripts/ ./scripts/

RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "hire_signal.scheduler"]