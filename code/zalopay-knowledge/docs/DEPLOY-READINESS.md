# Deploy Readiness — ZaloPay Knowledge Agent (AgentBase)

Checklist for MVP deploy on GreenNode AgentBase. Skills live in `.claude/skills/` (symlink or copy from `greennode-agentbase-skills`).

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
6. **Sync** — trigger Confluence + GDrive sync via Settings; confirm `GET /health` → `index_ready: true`.
7. **Monitor** — `/agentbase-monitor runtime-logs` and budget alert at 80%.
8. **Teardown playbook** — `/agentbase-teardown zalopay-knowledge --dry-run` before any real cleanup.

## Runtime env (non-`GREENNODE_*` in env file)

See `.env.example`. On AgentBase, `APP_ENV=agentbase`. Platform injects `GREENNODE_API_KEY` when `LLM_API_KEY` is unset.

## Out of scope (Phase 2)

- `/agentbase-gateway`, `/agentbase-policy` (MCP + Policy Groups)
- `/agentbase-identity` for Confluence vault (MVP uses `.env`)
- LTMS full strategies, VPC, Teams channel

## References

- `docs/API-CONTRACT.md`
- `2-requirements/05-DEPLOYMENT-PLAN.md`
- `greennode-agentbase-skills/README.md`
