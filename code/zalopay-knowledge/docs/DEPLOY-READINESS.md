# Deploy Readiness — Zalopay Knowledge Agent (AgentBase)

Checklist for MVP deploy on GreenNode AgentBase. Skills live in `.claude/skills/` (symlink or copy from `greennode-agentbase-skills`).

## MVP Platform/Ops gates (checklist §3 🟢 MUST)

| Requirement | Implementation | Verify |
|---|---|---|
| Idempotent sync + tombstones | `SyncService` + `IndexBuilder.tombstone_removed_urls`; content-hash skip via `sync_sources` in `meta.db` | `pytest tests/unit/ingestion/test_orchestrator.py tests/unit/ingestion/test_sync_hash.py` |
| Atomic index swap | FAISS written to temp file then `os.replace` | `pytest tests/unit/ingestion/test_indexer_atomic.py` |
| Readiness = index + MaaS | `GET /health/ready` → 503 until both; liveness separate at `/health/live` | `pytest tests/unit/api/test_health_probes.py` |
| MaaS retry + timeout | `VngMaasLLM` tenacity retries; `LLM_REQUEST_TIMEOUT_S` default 60s | `pytest tests/unit/adapters/test_maas_llm.py` |
| Per-stage tracing | `build_stage_trace` → `audit.db.stage_trace_json` | `pytest tests/unit/common/test_stage_trace.py tests/unit/store/test_audit_trace.py` |
| Dept subgraph degradation | `_make_dept_branch` catches branch failures → `timeout` + `branch_error` | `pytest tests/unit/platform/test_ops_mvp.py` |

Combined platform suite: `pytest tests/unit/platform/test_ops_mvp.py tests/unit/ingestion/ tests/unit/api/test_health_probes.py`.

## Prerequisites

```bash
export GREENNODE_CLIENT_ID="..."
export GREENNODE_CLIENT_SECRET="..."
```

## Ordered steps

1. **LLM** — `/agentbase-llm`: create API key; enable SMALL + MAIN models; set runtime env `LLM_API_KEY` (or rely on platform `GREENNODE_API_KEY` fallback).
2. **Memory (STM)** — `/agentbase-memory create`; set `MEMORY_ID` on runtime.
3. **Validate** — `/agentbase-wizard test validate` → `test docker --platform linux/amd64` → `test preflight`.
4. **Build** — `make docker-build-amd64` from project root.
5. **Deploy** — `/agentbase-deploy` (PUBLIC MVP, flavor with enough RAM for embeddings + FAISS).
6. **Sync** — trigger Confluence + GDrive sync via Settings; confirm `GET /health/ready` → `ready: true` (index + MaaS).
7. **Monitor** — `/agentbase-monitor runtime-logs` and budget alert at 80%.
8. **Teardown playbook** — `/agentbase-teardown zalopay-knowledge --dry-run` before any real cleanup.

## Health probes

| Endpoint | Purpose | Success |
|---|---|---|
| `GET /health/live` | Liveness — process accepting HTTP | Always `200` |
| `GET /health/ready` | Readiness — FAISS loaded + MaaS ping | `200` when `ready: true`, else `503` |
| `GET /health` | Combined snapshot (liveness + readiness fields) | `200` with `index_ready`, `maas_ready`, `ready` |

AgentBase `@app.ping` maps to the same gate as `/health/ready` (index + MaaS).

Configure orchestrator **readiness** checks against `/health/ready`, not `/health/live`.

The Docker `HEALTHCHECK` uses `/health/live` so the container stays up during long first sync; route traffic only when `/health/ready` is 200.

## Sync operations (G4)

1. Trigger `POST /sync/confluence` and/or `POST /sync/gdrive` (202 Accepted).
2. Poll `GET /sync/status` until `state: idle` (or `error` with message).
3. Removed source URLs are tombstoned (`lifecycle_state=sunset`) before partition rebuild.
4. Unchanged page bodies skip re-chunking when `sync_sources.content_hash` matches (zero LLM tokens; local embed only on changed docs).
5. Each department partition is rebuilt offline then atomically swapped — never serve a half-written FAISS file.

## Runtime env (non-`GREENNODE_*` in env file)

See `.env.example`. On AgentBase, `APP_ENV=agentbase`. Platform injects `GREENNODE_API_KEY` when `LLM_API_KEY` is unset.

Key ops tunables: `INDEX_DIR`, `GRAPH_BUDGET_S`, `BRANCH_TIMEOUT_S`, `LLM_REQUEST_TIMEOUT_S`, `HEALTH_PING_TIMEOUT_S`, `AGENT_ENABLED`.

## Out of scope (Phase 2)

- `/agentbase-gateway`, `/agentbase-policy` (MCP + Policy Groups)
- `/agentbase-identity` for Confluence vault (MVP uses `.env`)
- LTMS full strategies, VPC, Teams channel
- Sync freshness SLA alerting, versioned index rollback, eval-as-CI-gate

## References

- `docs/API-CONTRACT.md`
- `2-requirements/05-DEPLOYMENT-PLAN.md`
- `2-requirements/08-KNOWLEDGE_AI_AGENT_CHECKLIST_AGAIN.md` §3
- `greennode-agentbase-skills/README.md`
