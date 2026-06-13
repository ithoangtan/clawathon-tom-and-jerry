# 04 — Required Skills, Tools, Integrations, Models, Credentials

## 1. greennode-agentbase-skills (install prerequisite)

```bash
git clone https://github.com/vngcloud/greennode-agentbase-skills.git
cp -r greennode-agentbase-skills/.claude/skills/* <project>/.claude/skills/   # or ~/.claude/skills
export GREENNODE_CLIENT_ID="<service-account-client-id>"
export GREENNODE_CLIENT_SECRET="<service-account-secret>"
```

Skills used (all ten): `agentbase-wizard` (lifecycle driver), `agentbase` (reference + helper scripts), `agentbase-llm`, `agentbase-memory`, `agentbase-identity`, `agentbase-deploy` (incl. CR + OpenClaw), `agentbase-gateway`, `agentbase-policy`, `agentbase-monitor`, `agentbase-teardown`.

## 2. Runtime dependencies (the agent image)

| Component | Choice | Notes |
|---|---|---|
| Language | Python 3.11 (≥3.10 required by wizard) | |
| Agent SDK | `greennode-agentbase` | `GreenNodeAgentBaseApp`, `RequestContext`, `@app.ping`/`PingStatus`, `@requires_api_key(provider_name="aip-key")`, `MemoryClient` |
| Memory bridge | `greennode-agent-bridge[langgraph]` | Provides the `AgentBaseMemoryEvents` LangGraph checkpointer (verified against live docs — it is NOT in the base SDK) |
| Orchestration | LangGraph (+ LangChain core) | Supervisor + subgraphs + conditional edges |
| LLM client | OpenAI-compatible client → MaaS | One client, two model tiers |
| Embeddings | Multilingual model (e.g. `multilingual-e5-small` class) — local in MVP; served in VPC at prod scale | Corpus is VI+EN |
| Index (MVP) | FAISS in-process | Pre-built from the 3 dept spaces (Risk, Grow Enablement, Bank Partnerships; ≈1,000 pages total), baked into image / loaded at boot |
| Index (Prod) | Weaviate **or** Postgres+pgvector in ZaloPay VPC | Hybrid dense+BM25; per-dept partitions/collections |
| HTTP | SDK app (FastAPI-compatible additional routes): Web UI portal (Chat + Dashboard), `/chat`, `/feedback`; `/webhooks/teams` in Phase 2 | Bind `0.0.0.0:8080` |
| Tests | pytest + contract tests from `/agentbase-wizard test` | |

## 3. Models (all via MaaS — verify `modelStatus = ENABLED` at build time)

| Role | Tier | Candidates |
|---|---|---|
| Routing, grading, citation verification | small/cheap | Qwen small / MiniMax small variants in the MaaS catalog |
| Answer synthesis, reconciliation | mid | Qwen 2.5/3-class chat model |
| Embeddings | — | Local multilingual sentence-transformer (MVP); revisit MaaS/OCR offerings for files in phase 2 |

Endpoint: `https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1` (`LLM_BASE_URL`), key via `/agentbase-llm api-keys create` (`LLM_API_KEY`; key names must match `^[a-z0-9\-]{5,50}$`), model name in `LLM_MODEL` (+ `LLM_MODEL_SMALL` project convention). The model catalog is discovered at build time via `aip.sh models list` — never hard-code model names; AI Platform pagination is 1-indexed (other services differ — always inspect responses).

## 4. External integrations

| System | Phase | Access path | Auth (stored in Agent Identity) |
|---|---|---|---|
| Confluence (source of truth) | 1 (3 personal spaces) / 2 (all) | MVP: REST v2 direct over the personal Confluence instance. Prod: via MCP Gateway route into VPC | Service-account bearer token (apikey credential) |
| Microsoft Teams | 2 (webhook + full bot) | Webhook route on the runtime; Bot Framework registration on ZaloPay tenant | Bot app ID + secret (apikey credential); webhook signature verification |
| GitLab | 2 | MCP Gateway route; index README/docs/comments via sync job | Project access token |
| SharePoint | 2 | MCP Gateway route; OAuth2 (2LO admin-granted); document text extraction in sync job | OAuth2 credential on identity |
| PDF stores | 1 (Google Drive, SharePoint simulation) / 2 (SharePoint, full) | Sync-job extraction (pypdf/OCR) → same chunk pipeline; citation = file name + page | Per-store credential on identity |
| Zalo (optional channel) | 2+ | OpenClaw instance (Telegram/Zalo template) calling the runtime endpoint | Bot token via OpenClaw pairing flow |

Integration rules: the request path never calls Confluence live (retrieval hits the index only — keeps latency and rate limits sane); the sync job is the only Confluence client; per FR-5.1 respect ~100 req/min, batch ≤50, exponential backoff ≤5 retries.

## 5. Environment variables

| Var | Source | Secret? |
|---|---|---|
| `GREENNODE_CLIENT_ID` / `GREENNODE_CLIENT_SECRET` / `GREENNODE_AGENT_IDENTITY` / `GREENNODE_ENDPOINT_URL` | auto-injected by runtime — never set | — |
| `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_MODEL_SMALL` | `/agentbase-llm` + `save_env_var.sh` | key: yes |
| `MEMORY_ID` | `/agentbase-memory create` | no |
| `CONFLUENCE_URL`, `CONFLUENCE_SPACES` | config | no |
| `CONFLUENCE_TOKEN` | MVP only (`save_env_var.sh --value-file`); prod → Agent Identity retrieval | yes |
| `TEAMS_APP_ID` / `TEAMS_APP_SECRET` | identity (prod) | yes |
| `INDEX_URL` (prod) | VPC index endpoint | no |
| `GRADE_THRESHOLD`, `TOPK`, `BRANCH_TIMEOUT_S` | tunables with defaults (0.5 / 8 / 20) | no |

Discipline: `/agentbase-wizard` Step 6 (`check_env.sh`) must pass with zero missing vars before any deploy; `.env` never committed.

## 6. Project skills/prompts internal to the agent

- Router prompt (intent classes ≅ doc types: technical/product/operational/business/compliance/organizational + department descriptors).
- Grading prompt (binary relevance + score, JSON-only output).
- Synthesis prompts per role profile (engineer/PM/ops/risk/business — seeded from the brainstorm's response profiles, then evolved via LTMS `CUSTOM` strategy).
- Verification prompt (claim ↔ chunk entailment check).
- Reconciliation prompt (merge vs conflict-flag, citation-preserving).
All prompts versioned in-repo under `prompts/` and covered by the eval set in `06-SUCCESS-CRITERIA.md`.
