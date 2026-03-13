# ========================================
# Animantis Dockerfile
# ========================================
FROM python:3.11-slim

# Security: non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Own files by appuser
RUN chown -R appuser:appuser /app

USER appuser

# Default: run API (override CMD for worker/beat)
# NOTE: alembic upgrade head will be added back when migrations are configured
CMD ["sh", "-c", "uvicorn animantis.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
