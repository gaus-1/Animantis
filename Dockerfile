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

# Make startup script executable
RUN chmod +x start.sh

# Own files by appuser
RUN chown -R appuser:appuser /app

USER appuser

# Default: run API (override CMD for worker/beat)
CMD ["sh", "start.sh"]
