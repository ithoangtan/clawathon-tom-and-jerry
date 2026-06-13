# Zalopay Internal Knowledge Agent

A **citation-grounded, corrective-RAG assistant** for Zalopay's internal teams.  Every answer carries at least one verifiable citation from your Confluence/Drive corpus; the agent refuses when the retrieved documents don't support an answer.  It never touches the internet.

---

## What it is / isn't

| It IS | It is NOT |
|---|---|
| An internal Q&A assistant grounded 100% in your Confluence + Drive documents | A general-purpose chatbot |
| A citation machine — every claim cites a source | A document management system |
| Cross-department (Risk / Grow Enablement / Bank Partnerships fan-out) | A compliance/legal tool (answers are informational only) |
| Deployed as a single Docker container | A multi-tenant SaaS |
| Bilingual VI + EN | A translation service |

---

## Architecture at a glance

```
React SPA ──HTTP──► FastAPI (port 8080)
                     │
                     ▼
              LangGraph supervisor
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   Risk subgraph  Grow subgraph  Bank subgraph   (parallel, per-branch timeout)
   retrieve→grade→synthesize→verify
        │            │            │
        └────────────┴────────────┘
                     ▼
               reconcile → respond

Ports (swappable):  LLMPort → VNG MaaS (Qwen/MiniMax)
                    RetrieverPort → FAISS (local)
                    CheckpointerPort → SQLite (local) / AgentBase STM (deploy)

Ingestion (triggered by Sync button):
  Confluence Cloud v2 ──► extract ──► chunk ──► embed (local) ──► FAISS partition
  Google Drive PDFs   ──► pypdf  ──► chunk ──► embed (local) ──► FAISS partition
```

---

## Prerequisites

- Docker + Docker Compose v2
- 4 GB RAM free (embedding model + FAISS)
- VNG MaaS API key with at least one Qwen/MiniMax model enabled
- Confluence Cloud API token (for the spaces you want to index)
- Google Drive service-account JSON **or** API key (for PDF sync)

---

## Quick-start demo loop

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd code/zalopay-knowledge

# 2. Copy and fill environment variables
cp .env.example .env
#    Edit .env — fill LLM_API_KEY, SMALL_MODEL, MAIN_MODEL,
#    CONFLUENCE_* and GDRIVE_* values at minimum.

# 3. Build and start
docker compose up --build
#    First build takes ~3–5 min (downloads embedding model).
#    Subsequent starts are fast.

# 4. Open the portal
open http://localhost:8080

# 5. Demo loop
#    a. Settings page → pick a user/role/department identity
#    b. Settings → Sync → click "Sync from Confluence"
#       (watch the Dashboard → Sync Status panel turn green)
#    c. Settings → Sync → click "Sync PDFs from Drive"
#    d. Chat → ask an in-corpus question (grounded answer + citations)
#    e. Chat → ask an out-of-corpus question (clean refusal)
#    f. Chat → ask a cross-department question (ConflictPanel if sources disagree)
```

---

## Frontend dev loop (hot-reload)

```bash
# Terminal 1 — backend container
docker compose up

# Terminal 2 — Vite dev server (proxies /api → :8080)
make fe-dev
# open http://localhost:5173
```

---

## Project layout

```
zalopay-knowledge/
├── app/
│   ├── api/          routes, schemas (API contract), context header parsing
│   ├── ports/        Protocols only — LLMPort, RetrieverPort, CheckpointerPort
│   ├── adapters/     Concrete implementations (MaaS LLM, FAISS retriever, SQLite checkpointer)
│   ├── graph/        LangGraph state, node implementations, subgraph factory
│   ├── ingestion/    Confluence + Drive sync pipeline
│   ├── store/        SQLite audit log + feedback store
│   ├── common/       PII masking, language detection, citation helpers, logging
│   └── prompts/      Versioned YAML prompt files
├── frontend/         React + Vite + TypeScript + Tailwind
├── corpus/pdfs/      Drive-sourced PDFs (gitignored; Docker named volume)
├── index/            FAISS partitions + SQLite metadata (gitignored; Docker named volume)
├── tests/            unit/ contract/ evals/
└── docs/             API-CONTRACT.md DEPLOY-READINESS.md PHASE-2-PLACEHOLDERS.md RUNBOOK.md
```

---

## Testing

```bash
# Backend
make test            # all tests
make test-unit       # unit tests only
make test-contract   # contract / round-trip tests only

# Frontend
cd frontend && npm test
```

---

## Deploy to GreenNode AgentBase

See `docs/DEPLOY-READINESS.md` for the exact swap checklist.  In short:

1. Set `APP_ENV=agentbase` in the AgentBase environment config.
2. The platform auto-injects `GREENNODE_*` vars (MaaS key override, identity URL, memory URL).
3. `deps.py` picks `checkpointer_agentbase.py` and the AgentBase entrypoint in `main.py`.
4. No changes to graph nodes, prompts, or ingestion code.

---

## Phase 2 (not built — documented stubs only)

Teams webhook, MCP server endpoint, VPC/Private mode, Policy Groups, long-term memory (LTMS), GitLab source, SharePoint source.  See `docs/PHASE-2-PLACEHOLDERS.md`.
