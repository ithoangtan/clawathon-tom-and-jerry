# 03 — Architecture & Mapping to AgentBase / greennode-agentbase-skills

## 1. Topology decision: one runtime, departments as subgraphs

The system is **one LangGraph application in one Custom Agent runtime**. Departments are subgraphs sharing the process and differing only in (a) which index partition they retrieve from and (b) their response-style profile.

**Agent Center semantics (G2):** the router/supervisor node is the Agent Center. It is contractually forbidden to synthesize an answer itself — its only outputs are (a) an acknowledgement, (b) a dispatch to 1..N department subgraphs, (c) the forwarded department answer(s) with the owning department named, or (d) one clarifying question when routing confidence is low. Users can also enter the graph with `target_departments` pre-pinned (direct department access via per-department Teams bot/tag or explicit mention), skipping classification entirely.

Rejected alternative — 21 runtimes (1 router + 20 departments): AgentBase scales **replicas within a runtime** (1–10), not fleets of runtimes; cross-runtime agent-to-agent calls add latency, auth, and version-skew problems; cost and deploy time multiply ×21; and isolation is achieved more strongly at the index partition + Policy Group level anyway. If a single department's load ever dominates, split that subgraph into its own runtime then — the graph shape doesn't change.

## 2. System diagram

```
        Web UI portal (MVP) / Teams (Phase 2) / OpenClaw-Zalo
                          │  HTTPS
                          ▼
          AgentBase Runtime endpoint (DEFAULT, versioned)
┌─────────────────────────────────────────────────────────────┐
│  Container (port 8080) — greennode-agentbase SDK app         │
│   GET /health   POST /invocations   POST /webhooks/teams (Phase 2) │
│                          │                                   │
│   ┌──────────────────────▼─────────────────────────────┐    │
│   │ LangGraph                                          │    │
│   │  ingest-context ─► router/supervisor               │    │
│   │        │   (classify intent, pick 1..N departments,│    │
│   │        │    check access allowlist)                │    │
│   │        ▼                                           │    │
│   │  dept subgraph ×N (parallel, per-branch timeout)   │    │
│   │   retrieve(hybrid, dept partition)                 │    │
│   │     ─► grade relevance ──低──► REFUSE("not in docs")│    │
│   │     ─► synthesize(answer + citations, role style)  │    │
│   │     ─► verify citations ──fail──► strip/REFUSE     │    │
│   │        ▼                                           │    │
│   │  reconcile (merge | flag conflict) ─► respond      │    │
│   └────────────────────────────────────────────────────┘    │
│        │                │                    │               │
│        ▼                ▼                    ▼               │
│  Memory svc        MaaS LLM            Retrieval index      │
│  (STM checkpointer  (OpenAI-compat,    MVP: FAISS in-proc   │
│   + LTM records)     Qwen/MiniMax)     Prod: Weaviate/pgvector in VPC │
└─────────────────────────────────────────────────────────────┘
         Prod source access:                Sync job (separate schedule):
         MCP Gateway (Private) + Policy     Confluence/GitLab/Drive →
         Groups → Confluence/GitLab/Drive   chunk → embed → upsert+tombstone
         inside ZaloPay VPC (VPC peering)   → index partitions
```

## 3. Graph state (carried across nodes, checkpointed)

`{session_id, user_id, role, home_department, allowed_departments, messages[], target_departments[], evidence{dept → chunks+scores}, citations[], confidence, refusals[], conflicts[], recalled_preferences[]}`

Checkpointer: `AgentBaseMemoryEvents` from **`greennode-agent-bridge[langgraph]`** (separate package from the `greennode-agentbase` SDK — verified against live docs) → `builder.compile(checkpointer=...)`, invoked with `config={"configurable": {"thread_id": context.session_id, "actor_id": context.user_id}}`. The MaaS key is injected into the handler via the SDK decorator `@requires_api_key(provider_name="aip-key")`; health via `@app.ping` → `PingStatus.HEALTHY`. No state in process memory between requests (platform requires stateless containers).

## 4. Node contracts

| Node | Input → Output | Model |
|---|---|---|
| ingest-context | headers + payload → validated state (reject if memory headers missing) | none |
| router | question + history → `{intent, target_departments[], confidence}` | small/cheap MaaS model |
| retrieve | question per dept → top-k chunks (k≈8 dense ∥ BM25, merged) from that dept's partition only | embedding model (multilingual) |
| grade | chunks → relevance scores; max < threshold (≈0.5 to start) → REFUSE branch | small model |
| synthesize | chunks + role profile + recalled preferences → answer with inline citation markers | main MaaS model |
| verify | (claim, cited chunk) pairs → supported? strip or refuse on failure | small model |
| reconcile | N dept answers → merged answer or conflict report; preserves all citations | main model |
| respond | state → API/Teams formatting, feedback_id issued, audit log emitted | none |

## 5. Data layer

- **Corpus index** (not the Memory service): partitioned per department. MVP: FAISS index pre-built by the sync job from the 3 department spaces (Risk, Grow Enablement, Bank Partnerships; ≈1,000 pages total) and baked into the image / loaded at boot — never built per-request. Prod: Weaviate or Postgres+pgvector deployed in ZaloPay's VPC, reached privately; hybrid search (dense + BM25); chunk metadata per FR-5.3.
- **Memory service** (`https://agentbase.api.vngcloud.vn/memory/...`): one Memory store; `eventExpiryDuration` 30 days; LTMS: `USER_PREFERENCE` (auto) + `CUSTOM` (response-style extraction prompt). Namespace `/strategies/{memoryStrategyId}/actors/{actorId}`; `actorId` = employee user ID.
- **Audit/feedback**: append-only log via runtime logs (MVP); prod adds a small Postgres in VPC for feedback rows + audit queries (the only bespoke datastore besides the index).

## 5a. Token-efficient daily sync pipeline (G4 / FR-5.6)

The sync job spends **zero LLM tokens** on a normal day. Ordered stages, each existing to avoid paying for the next:

| Stage | Mechanism | Cost on a quiet day |
|---|---|---|
| 1. Detect | Confluence CQL `lastModified >= cursor` per space; page-id reconcile pass for deletions | API calls only |
| 2. Skip | Stored `version.number` + SHA-256 of storage-format body vs current → unchanged pages skipped | none |
| 3. Chunk diff | Re-chunk changed pages; hash each chunk; reuse vectors for unchanged chunks | none |
| 4. Embed | Local multilingual sentence-transformer embeds only changed chunks | CPU only, no MaaS tokens |
| 5. Classify | Doc-type from space/label/path rules; small-model LLM fallback ONLY for new unclassifiable pages (≈1 call/new page, capped) | ~0 |
| 6. Upsert | Index partition upsert + tombstones; cursor advanced only on success | none |
| Weekly | Full reconcile (source page-id set vs index) catches drift | API calls only |

PDF/SharePoint (phase 2) enter at stage 3 after extraction (OCR where needed), carrying `{file_name, page}` citation metadata instead of `{url, anchor}`.

## 6. Mapping to AgentBase modules (the platform contract)

| Concern | AgentBase module | Specifics |
|---|---|---|
| Compute, scaling, rollback | **Agent Runtime** | Image from vCR; port 8080; `GET /health`; flavor `1x1-general` → resize on OOM; autoscale min 2 / max 10 @ CPU 50% (prod); every PATCH = immutable version; DEFAULT endpoint tracks latest; rollback = pin endpoint to older version; canary = second endpoint pinned to new version |
| Identity & secrets | **Access Control / Agent Identity** | Auto-injected `GREENNODE_CLIENT_ID/SECRET`, `GREENNODE_AGENT_IDENTITY`; Confluence/GitLab/Teams credentials stored on the identity (API key / OAuth2), retrieved via SDK — never in image or `.env` in prod |
| Conversation + learning | **Memory** | STM events (checkpointer) + LTM records (semantic search 5–200 results, scoreThreshold 0–1) |
| LLM serving | **MaaS / AgentBase LLM** | `LLM_BASE_URL=https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1`; key via `/agentbase-llm api-keys create`; chosen models must be `modelStatus = ENABLED` |
| Governed source access | **MCP Governance** | MCP Gateway (Private mode) fronting Confluence/GitLab/Drive MCP servers in VPC; inbound auth IAM/JWT; outbound APIKEY/OAuth2; **Policy Groups** with exact-action ALLOW/DENY statements per department resource |
| Network reach | **Private Networking** | VPC peering (pre-arranged with GreenNode support); Runtime + Gateway in Private mode; Route CIDRs for additional subnets |
| Images | **Container Registry (vCR)** | `vcr.vngcloud.vn/<repo>/zalopay-knowledge:<semver>`; robot account in `imageAuth` |
| Observability | **Monitor** | runtime logs, endpoint logs, CPU/RAM metrics, dashboard |
| Cost | **Usage & Budget** | per-key usage; budget alert at 80% |
| Org access | **Team & Permissions** | deploy rights restricted to Admin; viewers get Monitor |

## 7. Mapping to greennode-agentbase-skills (the delivery contract)

| Lifecycle stage | Skill | Use in this project |
|---|---|---|
| Scaffold | `/agentbase-wizard init zalopay-knowledge --langgraph` | Generates SDK-correct `main.py` (LangGraph + memory variant), Dockerfile, requirements; Python ≥3.10; files in CWD |
| LLM | `/agentbase-llm` | Create API key (auto-saves `LLM_API_KEY`), set `LLM_BASE_URL`, pick ENABLED Qwen/MiniMax models, set rate limits |
| Memory | `/agentbase-memory` | Create store + LTMS strategies; `MEMORY_ID` to env via `save_env_var.sh` |
| Identity/auth | `/agentbase-identity` | Create identity; store Confluence token (apikey), Teams secret; OAuth2 for Drive later |
| Test | `/agentbase-wizard test validate → local → docker → preflight` | Static contract checks, local server + contract tests, containerized test (`--platform linux/amd64` on Apple Silicon) |
| Deploy | `/agentbase-deploy` | build → push (vCR robot creds) → create/PATCH runtime → poll `ACTIVE` |
| Govern | `/agentbase-gateway`, `/agentbase-policy` | Create Private gateway, routes to VPC MCP servers, bind Policy Group with per-dept statements |
| Operate | `/agentbase-monitor` | runtime-logs / endpoint-logs / metrics / dashboard |
| Cleanup | `/agentbase-teardown zalopay-knowledge --dry-run` first, always | |

Conventions the project adopts from the skills: state in `.agentbase-state.json` (resumable, never hand-edited); `.greennode.json` is SDK-owned; secrets only via `save_env_var.sh --value-file`; never construct platform URLs from memory — invoke the owning skill; inspect API responses before parsing (pagination is inconsistent across services); explicit confirmation before mutating actions.

## 8. Security architecture

- Inbound (prod): JWT/IAM at the gateway; runtime not exposed publicly once Private.
- Per-department isolation: index partition filter is set by the router from a server-side allowlist (never from user input), and source access is policy-gated at the MCP Gateway. Prompt-level instructions are NOT a security boundary.
- PII: mask in logs (regex pass for emails/phones/card patterns) — corpus content itself stays in VPC in prod.
- Secrets: IAM service account via auto-injected env; external creds via Agent Identity (Vault-backed); reset path: `PATCH .../reset-service-account` if leaked.

## 9. Failure modes & handling

| Failure | Behavior |
|---|---|
| Dept branch timeout | Reconcile proceeds with completed branches; response notes the missing department |
| Index unavailable | Refuse with "knowledge base temporarily unavailable" — never answer un-grounded |
| MaaS 429/5xx | Retry with backoff; degrade to single-department answer; surface error after budget exhausted |
| Memory svc down | Answer statelessly (no history/preferences), log warning |
| Sync job failure | Previous index keeps serving; alert; freshness metric flags > 24h staleness |
| Bad deploy | Health check fails → version never receives traffic; rollback via endpoint pin |
