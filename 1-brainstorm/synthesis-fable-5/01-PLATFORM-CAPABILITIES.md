# GreenNode AgentBase — Capabilities, Contracts, and Constraints That Shape the Design

Everything below is sourced from `docs/English/ai-stack/agent-base/` and `greennode-agentbase-skills/`. This is the platform reality the agent must be designed around.

## 1. The two deployment paths

| Path | What it is | Verdict for this project |
|---|---|---|
| **Custom Agent (Agent Runtime)** | You ship a Docker image; platform runs, scales, versions, and routes to it | **Primary path.** The knowledge agent is custom Python (LangGraph) — this is the only path that fits |
| **OpenClaw (1-click)** | Pre-built Telegram/Zalo chat bot template, deployed in 40–60s, BYOK or MaaS | **Complementary only.** No custom logic, no Teams, no custom domain, no team/shared instance, no backup. Useful later as a Zalo channel front-end, not as the agent itself |

## 2. Runtime service contract (HARD — only two requirements)

1. Container **listens on port 8080** (not configurable).
2. **`GET /health` returns HTTP 200** when ready → runtime marked `ACTIVE`.

Everything else is convention. The `greennode-agentbase` SDK adds:

- `POST /invocations` as the entrypoint (SDK convention, not platform-enforced)
- Header extraction: `X-GreenNode-AgentBase-Session-Id` (→ `context.session_id`, required for short-term memory/checkpointer), `X-GreenNode-AgentBase-User-Id` (→ `context.user_id`, required for memory and delegated/OAuth2-3LO auth; maps to `actor_id`), `X-GreenNode-AgentBase-Request-Id`, `X-GreenNode-AgentBase-Custom-*`
- **Docs warning:** if the agent uses memory, *reject* requests missing these headers — silent defaults cause data mixing between users

Auto-injected env vars (never set manually): `GREENNODE_CLIENT_ID`, `GREENNODE_CLIENT_SECRET`, `GREENNODE_AGENT_IDENTITY`, `GREENNODE_ENDPOINT_URL`.

**Design implication:** the agent must be **stateless in-process** — all conversation state goes to the Memory service. The corpus index must either fit in the container (MVP: FAISS baked into image / loaded at boot) or live in the VPC (prod: self-hosted vector store reached privately).

## 3. Runtime lifecycle facts

- Runtime states: `CREATING → ACTIVE | ERROR`, plus `UPDATING`, `DELETING`.
- Every `PATCH /agent-runtimes/{id}` creates a new **immutable Version**; the `DEFAULT` endpoint auto-tracks latest; extra endpoints can be pinned to versions → **canary and instant rollback are free** (point endpoint back to older version).
- Autoscaling: `minReplicas`/`maxReplicas` **1–10**, CPU/RAM thresholds **25–75%**. Replicas cap at 10 per runtime.
- Compute flavors like `1x1-general` (1 CPU / 1 GB). OOMKilled → pick larger flavor.
- API base: `https://agentbase.api.vngcloud.vn` (`/runtime/agent-runtimes`, `/memory/memories`, …). Console: `https://aiplatform.console.vngcloud.vn`.
- Region: HCM (primary).

**Design implication:** a 21-runtime topology (1 router + 20 departments) buys nothing — the platform scales replicas, not agent fleets, and each runtime carries its own cost/ops overhead. One runtime, many subgraphs.

## 4. Memory service (managed — do not build our own for conversation state)

- **Short-term:** ordered role/content events, scoped by session ID, survives container restarts, `eventExpiryDuration` 1–365 days. LangGraph integration via the SDK's `AgentBaseMemoryEvents` checkpointer (`builder.compile(checkpointer=...)`).
- **Long-term:** semantic records, namespace-partitioned (default `/strategies/{memoryStrategyId}/actors/{actorId}`), retrieved via similarity search (5–200 results, scoreThreshold 0–1). Extraction via LTMS strategies: `SEMANTIC`, `USER_PREFERENCE`, `CUSTOM` (own prompt).
- `actorId` = the end user, never the agent.

**Design implication:** use Memory for (a) conversation continuity, (b) role/response-style preferences (`USER_PREFERENCE`), (c) feedback-derived learning (`CUSTOM` strategy). The **document corpus is NOT memory** — it's a separate retrieval index. The earlier brainstorm's instinct to run Weaviate-for-everything is half-right: Weaviate (or FAISS at MVP) for the corpus only.

## 5. LLM access — MaaS / AgentBase LLM

- OpenAI-compatible endpoint: `https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1`.
- API keys managed via `/agentbase-llm api-keys create` (saved to `.env` as `LLM_API_KEY`); model must have `modelStatus = ENABLED`.
- Cheap models (Qwen, MiniMax family) available — matches the brainstorm's cost target.
- Usage & Budget module: per-agent/model cost tracking + budget alerts.

**Design implication:** zero external LLM dependency. Router classification can use a small/cheap model; answer synthesis a larger one — both behind one OpenAI-compatible client.

## 6. MCP Governance (Resource Gateway + Policy Groups)

- MCP Gateway proxies agent tool calls to MCP servers; inbound auth `NONE`/`IAM`/`JWT`; per-target outbound auth `APIKEY` / OAuth2 2LO / 3LO.
- Policy Groups attach to the gateway: statements with effect (ALLOW/DENY), principal, **exact action patterns**, resources, conditions.

**Design implication:** Confluence/GitLab/Drive access should go **through the gateway** in production so per-department access is enforced by policy, not by prompt. This is the platform-native answer to the brainstorm's RBAC questions.

## 7. Identity & outbound auth

- Agent Identity + credential store (HashiCorp Vault-backed): static API key, delegated key, OAuth2 (2LO/3LO). Credentials injected at runtime via SDK decorators — never hardcoded.
- Runtime auto-provisions an identity if none configured; explicit identity needed only when using outbound auth features.

**Design implication:** Confluence service-account token, GitLab token, Teams bot secret all live in Identity, not in `.env`/image.

## 8. Private Networking

- VPC Peering connects your VPC to AgentBase; **Private** mode on Runtime and MCP Gateway keeps all traffic off the public internet.
- Must be provisioned by GreenNode support **beforehand**; only peered VPCs appear in the dropdown.

**Design implication:** ZaloPay's Confluence/GitLab are internal — **production requires Private mode**, so VPC peering is a week-0 dependency, not an afterthought. MVP can run Public against a test Confluence space.

## 9. Container Registry (vCR)

- Private registry `vcr.vngcloud.vn`, auto-provisioned per org; robot accounts for push/pull; `imageAuth {enabled, username: <robot backendName>, password}` on runtime creation.

## 10. The skills bundle = the delivery pipeline

`greennode-agentbase-skills` gives the whole lifecycle as Claude skills. The build should be driven through them, in this order:

```
/agentbase-wizard init <name> --langgraph     # scaffold (CWD, Python ≥3.10)
/agentbase-llm api-keys create                 # MaaS key + LLM_BASE_URL + model
/agentbase-memory create                       # STM + LTMS strategies
/agentbase-identity                            # Confluence/GitLab/Teams credentials
/agentbase-wizard test validate|local|docker   # contract tests before deploy
/agentbase-deploy                              # build → push (vCR) → deploy → ACTIVE
/agentbase-gateway + /agentbase-policy         # governed tool access (prod)
/agentbase-monitor                             # logs, metrics, dashboard
/agentbase-teardown <project> --dry-run        # cleanup
```

Operational notes baked into the skills: prerequisites `GREENNODE_CLIENT_ID`/`GREENNODE_CLIENT_SECRET` (IAM service account); state in `.agentbase-state.json` (resumable); secrets never pasted in chat (helper scripts `save_env_var.sh --value-file`); always inspect API responses before parsing; hard confirmation gates before mutating actions.

## 11. Hard constraints checklist (carry into the spec)

- Port 8080 + `/health` 200 — non-negotiable.
- Stateless containers; replicas 1–10; thresholds 25–75%.
- Memory event expiry 1–365 days; search results 5–200.
- Names: lowercase/hyphens (runtime), `^[a-zA-Z0-9._-]*$` ≤50 chars (memory).
- Private mode requires pre-arranged VPC peering (support ticket lead time).
- OpenClaw: Telegram/Zalo only, no custom domain, no backups, deletion permanent.
- Pagination is inconsistent across services (0- vs 1-indexed) — never assume, always inspect.
- Apple Silicon builds need `--platform linux/amd64`.
