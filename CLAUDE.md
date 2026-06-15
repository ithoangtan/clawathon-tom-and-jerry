# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Zalopay Internal Knowledge Agent** — a citation-grounded, corrective-RAG assistant that answers internal Q&A exclusively from Zalopay's Confluence + Google Drive docs. Never uses the internet; always cites sources.

The repo layout:
- `code/zalopay-knowledge/` — main application (FastAPI backend + React SPA)
- `2-requirements/` — 9-doc implementation spec (problem statement, architecture, deployment, etc.)
- `greennode-agentbase-skills/` — GreenNode AgentBase deployment skills (`.claude/skills` is symlinked here)

## Commands

All commands run from `code/zalopay-knowledge/` unless noted.

### Backend
```bash
make up              # Start full stack via docker compose (builds image first)
make down            # Stop stack (preserves volumes)
make build           # Build Docker image only

make test            # All pytest tests
make test-unit       # Unit tests only
make test-contract   # Contract/round-trip tests

python -m ruff check .    # Lint
```

### Frontend
```bash
make fe-dev          # Start Vite dev server (localhost:5173, proxies /api to backend)
make fe-build        # Build frontend to frontend/dist/

# Or directly from frontend/:
npm run dev
npm run build
npm test             # Vitest
npm run typecheck    # tsc --noEmit
```

### Sync & Health (requires running container)
```bash
make sync-confluence
make sync-gdrive
make sync-status
make health
```

### Deployment
```bash
make docker-build-amd64      # Build linux/amd64 image for AgentBase
make validate-runtime-env    # Check required AgentBase env vars
```

## Architecture

### Backend: FastAPI + LangGraph

The core is a **LangGraph supervisor state machine** in `app/graph/`:

```
Supervisor → routes question to relevant departments
  → 3 subgraphs in parallel: risk / grow_enablement / bank_partnerships
      each: [retrieve] → [grade] → [synthesize] → [verify]
  → [reconcile conflicts] → [respond]
```

- **Ports** (`app/ports/`): protocol interfaces — `LLMPort`, `RetrieverPort`, `CheckpointerPort`
- **Adapters** (`app/adapters/`): concrete implementations (OpenSearch, FAISS fallback, MaaS LLM, SQLite, AgentBase Memory)
- **Ingestion** (`app/ingestion/`): Confluence Cloud v2 API + Google Drive PDF sync
- **Config** (`app/config.py`): all settings via Pydantic + `.env`
- **Prompts** (`app/prompts/`): versioned YAML templates — edit here, not inline in code

### Frontend: React + Vite SPA

- Pages: Chat, Settings, Dashboard, Admin (`frontend/src/pages/`)
- State: Zustand (`frontend/src/store/`)
- Markdown rendering: `react-markdown` + `remark-gfm`
- Layout: resizable panels via `react-resizable-panels`

### RAG Design Principles

1. **Corrective-RAG**: grades retrieved chunks; re-queries if confidence is low
2. **Citation-grounded**: every answer must cite a source document
3. **Refuse gracefully**: "not in the docs" is a valid and expected answer
4. **Bilingual VI + EN**: detects language, maintains context per thread

### Key Infrastructure

| Concern | Local Dev | Production (AgentBase) |
|---|---|---|
| State/checkpointing | SQLite (`index/`) | AgentBase Memory service |
| Vector index | OpenSearch (GreenNode VDB) | OpenSearch (GreenNode VDB) |
| Audit / Feedback DB | MySQL `49.213.71.45` | MySQL `49.213.71.45` (same) |
| LLM | VNG MaaS (Qwen) | Same |
| Port | 8080 | 8080 |
| Health | `GET /health/ready`, `GET /health/live` | Same |

Set `VECTOR_STORE=faiss` in `.env` to fall back to local FAISS for offline dev.
Runtime env for AgentBase deploy lives in `deploy/.runtime.env` (gitignored — copy from `.env`).

### LLM

OpenAI-compatible endpoint: `https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1`
Embeddings: `baai/bge-m3` (multilingual, OpenSearch k-NN index).

## Testing Layout

```
tests/
  unit/        # Pure unit tests, no external deps
  contract/    # Round-trip tests (API shapes, graph edges)
  integration/ # Requires running services
  eval/        # RAG evaluation harness
  golden/      # Golden output snapshots
```

Run a single test: `pytest tests/unit/test_foo.py::test_bar`
