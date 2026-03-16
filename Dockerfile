# ========================================
# Animantis Dockerfile — Multi-stage
# Stage 1: Build frontend (Vite + React)
# Stage 2: Run backend (FastAPI + Uvicorn)
# ========================================

# ── Stage 1: Frontend build ──────────────────────────────────
FROM node:20-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --production=false
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python backend ─────────────────────────────────
FROM python:3.11-slim

# Security: non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Copy built frontend from stage 1
COPY --from=frontend-build /frontend/dist /app/frontend/dist

# Make startup script executable
RUN chmod +x start.sh

# Own files by appuser
RUN chown -R appuser:appuser /app

USER appuser

# Default: run API (override CMD for worker/beat)
CMD ["sh", "start.sh"]
