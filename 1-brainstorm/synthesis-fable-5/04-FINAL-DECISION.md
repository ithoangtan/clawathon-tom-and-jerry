# 04 — Final Decision (Locked Goals & Approach)

> Second-pass review (2026-06-13) of everything in `brainstrom-fable-5/` against the `greennode-agentbase-skills` bundle and the **live GreenNode AgentBase documentation** (docs.vngcloud.vn, verified online this pass). This file LOCKS the goals and the build approach. `../../requirements-fable-5/` is the full spec; `../../requirements-fable-5-mvp/` is the demo-ready subset.

---

## 1. Locked goals (non-negotiable, carried into every spec)

| # | Goal | Implication |
|---|---|---|
| LG-1 | **Users ask about ZaloPay knowledge and get answers in Microsoft Teams, with high accuracy** | Teams is the primary channel in ALL phases including MVP. Accuracy (grounded + cited) outranks latency and coverage |
| LG-2 | **Confluence is the source of truth. No invented knowledge. No internet research — ever** | The agent has zero web-search capability by design. Retrieval hits the internal index only. If the docs don't cover it → explicit refusal |
| LG-3 | **Knowledge is refreshed daily** with the most token-efficient sync that still searches well | Incremental sync: CQL `lastModified` cursor → content-hash skip → chunk-level diff → re-embed only changed chunks. **Zero LLM calls in the sync path** (embeddings only). See §3 |
| LG-4 | **One Agent Center routes for all departments.** It is the shared front door: it does NOT answer by itself — it calls the right department agent(s) to answer, and forwards the result (and the conversation) to the user. Users can ALSO query any department agent directly | Supervisor pattern with a strict "router never synthesizes from its own knowledge" contract + per-department addressable entry points |
| LG-5 | **Document types are diverse**: Confluence (PRD, Operation, Technical, Risk, Security, Org-structure, RCA, Ops-guidance, …), SharePoint, PDF | Doc-type taxonomy is metadata on every chunk; PDF/SharePoint need extraction in the sync pipeline (phase 2 of full spec; MVP = Confluence + a PDF sample set) |
| LG-6 | **MVP cuts only breadth, never the flow**: 20 departments → 2; corpus per department: one ~100 pages, one ~5,000 pages. Everything else (full flow, Teams, agent center, citations, refusal, sync) stays real | The MVP is a strict structural subset — same graph, same contracts. The 5,000-page department exists precisely to prove the design at realistic single-department scale |
| LG-7 | **Full flow + realistic user scenarios** for the Teams AI bot must be enumerated and tested | Scenario catalog is now a first-class deliverable: `requirements-fable-5/07-USER-SCENARIOS.md` and the MVP demo script |
| LG-8 | Role-aware responses, cross-department reconciliation, feedback learning, 5–10-year knowledge lifecycle (deprecation/sunset), enterprise security/audit/cost-caps | Carried over unchanged from the first pass (`03-RECOMMENDATION.md`) — these were in the original requirements and are kept (additive review: nothing removed) |

## 2. Locked approach (what we build)

Unchanged in shape from `03-RECOMMENDATION.md`, sharpened in three places:

1. **One LangGraph application in one Custom Agent runtime** on AgentBase (port 8080, `GET /health`, stateless). Departments = corrective-RAG subgraphs + per-department index partitions. NOT 21 runtimes.
2. **Agent Center semantics clarified (LG-4):** the router node (a) acknowledges in Teams, (b) classifies + dispatches to 1..N department subgraphs, (c) forwards the departments' answers verbatim-with-citations (reconciled if multiple), and (d) names which department answered — so the user always knows the knowledge owner. The center itself is forbidden to generate content that didn't come from a department branch. Direct department access = the same graph entered with a pre-pinned `target_department` (per-department Teams bot/tag or explicit mention like `@kb engineering: …`).
3. **Grounded-or-refuse remains the defining contract:** retrieve → grade → synthesize-with-citations → verify, refusal on low relevance. No internet tools exist in the image (LG-2 is enforced by construction, not by prompt).

**Delivery is driven end-to-end by `greennode-agentbase-skills`:** `/agentbase-wizard init --langgraph` → `/agentbase-llm` → `/agentbase-memory` → `/agentbase-identity` → `/agentbase-wizard test` → `/agentbase-deploy` → `/agentbase-gateway` + `/agentbase-policy` (prod) → `/agentbase-monitor` → `/agentbase-teardown`.

## 3. Token-efficient daily sync (LG-3, the design)

The cheapest sync that still searches well, in order of what it avoids paying for:

1. **Detect** — Confluence CQL `lastModified >= <cursor>` per space (and a deletions pass via page-id reconcile). Cost: API calls only.
2. **Skip** — compare page `version.number` + SHA-256 of storage-format body against the stored value; unchanged → skip. Cost: nothing.
3. **Diff at chunk level** — re-chunk the changed page, hash each chunk; only chunks whose hash changed are re-embedded; unchanged chunk vectors are reused. Cost: embedding tokens ∝ actual edits, not page size.
4. **Embed locally** — multilingual sentence-transformer runs in the sync job (no MaaS tokens for embeddings at all).
5. **No LLM anywhere in sync** — doc-type classification comes from space/label/path rules first; an LLM classifier is used once per NEW page only if rules fail (small model, ~1 call/new page, capped).
6. **Tombstones + weekly full reconcile** — deletes/permission changes remove chunks within one cycle; weekly pass catches drift.

Net effect: a quiet day across 20 departments costs API calls + a handful of embeddings; a heavy editing day costs ∝ edited chunks. LLM tokens are reserved for answering users, not for ingestion.

## 4. Platform verification (done online this pass)

Checked against live docs at `docs.vngcloud.vn/vng-cloud-document/ai-stack/agent-base/` (2026-06-13):

- ✅ Module list confirmed: Agent Runtime, Marketplace (OpenClaw), Access Control (Identity), MCP Governance (Gateway + Policy Groups), Protect & Govern (rate limiting), Memory (STM events + LTM records, LTMS `SEMANTIC`/`USER_PREFERENCE`/`CUSTOM`), Container Registry (vCR), Team & Permissions, Usage & Budget.
- ✅ Runtime contract confirmed: port **8080** non-configurable, `GET /health` → 200, auto-injected `GREENNODE_CLIENT_ID/SECRET/AGENT_IDENTITY`, headers `X-GreenNode-AgentBase-User-Id`/`Session-Id` (reject-if-missing rule confirmed verbatim), replicas 1–10, CPU/RAM thresholds 25–75%, flavors like `1x1-general`, immutable versions + endpoint pinning for canary/rollback, Private VPC selected at runtime creation.
- ✅ Memory service limits confirmed: `eventExpiryDuration` 1–365 days, name ≤50 chars `^[a-zA-Z0-9._-]*$`, search limit 5–200, scoreThreshold 0–1, event pagination max `from` 5000.
- ✅ MaaS endpoint confirmed: `https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1`, OpenAI-compatible; model catalog is discovered at build time (`models list`, must be `ENABLED`) — model names are NOT hard-coded in the spec.
- 🆕 **Corrections discovered and folded into the specs:**
  - The LangGraph checkpointer `AgentBaseMemoryEvents` ships in **`greennode-agent-bridge[langgraph]`** (a separate package from the `greennode-agentbase` SDK).
  - MaaS key injection in the handler uses the **`@requires_api_key(provider_name="aip-key")`** decorator (key arrives as a function argument, not env-read).
  - Health can be implemented via the SDK's `@app.ping` returning `PingStatus.HEALTHY`.
  - Runtimes support **STOP/START** (states `STOPPED`, `STARTING`): a stopped runtime costs no compute and keeps config + endpoints — use this between MVP demo sessions.
  - AIP API-key names: `^[a-z0-9\-]{5,50}$`; AI Platform pagination is 1-indexed (runtime/memory services differ — always inspect responses).
- ✅ Skills repo confirmed public: `github.com/vngcloud/greennode-agentbase-skills` (10 skills; the live docs themselves recommend it as the deploy path).

**Conclusion unchanged: there is no capability gap.** Every locked goal has a platform home.

## 5. What the second pass changed in the documents

| Where | Change (additive) |
|---|---|
| `requirements-fable-5/01..06` | Doc-type taxonomy expanded (PRD, Operation, Technical, Risk, Security + Org/RCA/Ops); Agent Center forward-don't-answer contract; no-internet-by-construction; token-efficient sync design; SDK package corrections; Teams elevated to primary channel in MVP |
| `requirements-fable-5/07-USER-SCENARIOS.md` | NEW — realistic Teams usage scenario catalog (LG-7) |
| `requirements-fable-5-mvp/` | NEW folder — demo-ready MVP spec: 2 departments (≈100 + ≈5,000 pages), full flow, AgentBase-verified resources, build plan, demo script |

## 6. Decision in one sentence

Build the ZaloPay Internal Knowledge Agent as **one LangGraph supervisor-routed, corrective-RAG, citation-grounded runtime on GreenNode AgentBase** — Teams-first, Confluence-as-truth, refuse-rather-than-hallucinate, token-frugal daily sync — shipped as a 2-department MVP (100 + 5,000 pages) that is a strict subset of the 20-department production system.
