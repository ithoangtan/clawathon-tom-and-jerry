# ZaloPay Knowledge Agent — multi-stage image (AgentBase-compatible)
#
# Stage 1: build the React SPA into frontend/dist
# Stage 2: Python 3.11 runtime with FAISS + local embeddings + FastAPI on :8080
#
# AgentBase hard requirements (runtime-contract.md):
#   - EXPOSE 8080
#   - GET /health → HTTP 200 when ready
#   - CMD ["python", "main.py"] binds 0.0.0.0:8080

# ── Stage 1: frontend ────────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python runtime ──────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Build headers for lxml; runtime libs for XML parsing.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        "greennode-agentbase>=1.0,<2" \
        "greennode-agent-bridge[langgraph]>=1.0,<2"

COPY . .
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# FAISS partitions, SQLite meta, HF model cache (mounted in docker-compose).
RUN mkdir -p /data/index/faiss /data/index/hf-cache /app/corpus/pdfs

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    INDEX_DIR=/data/index

EXPOSE 8080

CMD ["python", "main.py"]
