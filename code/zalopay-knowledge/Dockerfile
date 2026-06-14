# Zalopay Knowledge Agent — multi-stage image (AgentBase-compatible)
#
# Stage 1: build the React SPA into frontend/dist
# Stage 2: Python 3.11 runtime with FAISS + local embeddings + FastAPI on :8080
#
# AgentBase hard requirements (runtime-contract.md):
#   - EXPOSE 8080
#   - GET /health → HTTP 200 when ready
#   - CMD ["python", "main.py"] binds 0.0.0.0:8080
#
# Security (MVP checklist §5–6):
#   - No secrets in image: .env / credentials excluded via .dockerignore
#   - Platform injects GREENNODE_* at runtime (AgentBase Identity)
#   - Egress deny-all + allowlist: configure at AgentBase VPC / network policy
#     (see deploy/network-policy.md)
#   - TLS in transit: all outbound URLs must use https:// (enforced in Settings)

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
        "greennode-agent-bridge[langgraph]>=1.0,<2" \
    # Re-pin langgraph after bridge install: the bridge's [langgraph] extra may
    # silently upgrade langgraph to 0.3+ which drops JsonPlusSerializer.dumps().
    # AgentBaseMemoryEvents was written against 0.2.x and needs that method.
    && pip install --no-cache-dir "langgraph==0.2.76" "langgraph-checkpoint-sqlite==2.0.11"

COPY . .
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# FAISS partitions, SQLite meta, HF model cache (mounted in docker-compose).
RUN mkdir -p /data/index/faiss /data/index/hf-cache /app/corpus/pdfs

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    INDEX_DIR=/data/index

EXPOSE 8080

# Readiness gate for container orchestrators (index + MaaS). Liveness stays at /health/live.
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8080/health/ready', timeout=4); exit(0 if r.status==200 else 1)"

CMD ["python", "main.py"]
