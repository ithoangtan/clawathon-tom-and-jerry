# 02 — Capabilities & Scope

## Phasing

| | **Phase 1 — MVP (≈2-5 days)** | **Phase 2 — Production (≈4 months)** |
|---|---|---|
| Departments | 3 (Risk, Grow Enablement, Bank Partnerships) — **≈1,000 pages total across 3 departments** | 20 |
| Sources | Confluence (3 personal spaces) + PDF files on Google Drive (simulating SharePoint) | Confluence (all spaces) + GitLab + SharePoint (PDF store) |
| Index | FAISS, **pre-built by the sync job and baked into the image / loaded at boot** (≤1,000 pages ⇒ build offline, not per-request) | Hybrid (dense + BM25) per-department index in Zalopay VPC (Weaviate or pgvector) |
| Sync | Manual trigger; pipeline **architected** for scheduled incremental runs (Phase 2 activation only) | Daily incremental batch + tombstones + weekly reconcile |
| Networking | Personal Confluence space; networking per ai-stack/agent-base platform defaults (no custom VPC) | Private runtime + private MCP Gateway (VPC peering) |
| Channels | **Web UI portal** (Chat + Dashboard) + `POST /chat` (test alias) | Teams (mention/DM) + Web UI portal (Chat + Dashboard) + MCP server |
| Memory | STM checkpointer (AgentBase Memory) | STM + LTMS `USER_PREFERENCE` + `CUSTOM` feedback strategy |
| Access control | Follow ai-stack/agent-base production auth standards; personal Confluence connection uses same pattern as production | IAM/JWT inbound on gateway; Policy Groups per department; audit trail |
| Scale | Deploy as Custom Agent on Agent Runtime (per ai-stack/agent-base Custom Agents spec) | min 2 / max 10 replicas, autoscale CPU 50% |

## Functional requirements

### FR-1 Query handling
- FR-1.1 Accept a natural-language question with user context (`X-GreenNode-AgentBase-User-Id`, `X-GreenNode-AgentBase-Session-Id`, role + department via `X-GreenNode-AgentBase-Custom-*` headers). Requests using memory without these headers are **rejected with a clear error** (no silent defaults).
- FR-1.2 Classify intent and select 1–N target departments (router/supervisor).
- FR-1.3 Support follow-up questions using conversation history (STM).
- FR-1.4 Vietnamese and English queries (corpus is mixed-language; embedding model must be multilingual).
- FR-1.5 **Agent Center contract:** the router node never synthesizes an answer from its own knowledge — it only acknowledges, dispatches to department subgraph(s), and **forwards** their answers, always naming the owning department(s). If routing confidence is low, it asks ONE clarifying question (with department suggestions) instead of guessing.
- FR-1.6 **Direct department access:** a user may target a department explicitly (per-department Teams bot/tag, or `@bot <dept>: question`); the request enters the same graph with `target_departments` pre-pinned, skipping classification.

### FR-2 Grounded answering (the defining contract)
- FR-2.1 Retrieve top-k chunks from the target department index (hybrid dense+keyword in prod).
- FR-2.2 **Grade relevance before answering** (corrective-RAG gate). Below threshold → respond "Không có thông tin trong tài liệu" / "Not covered in the docs", optionally suggesting related pages and the owning department channel.
- FR-2.3 Every answer includes ≥1 citation: `{title, url, section/anchor, last_modified}` pointing at Confluence (or GitLab path / Drive file in phase 2).
- FR-2.4 A post-generation verification step checks each cited chunk actually supports the corresponding claim; failed verification downgrades to refusal or strips the unsupported claim.
- FR-2.5 Documents marked `deprecated` may be cited only with an explicit staleness warning; `sunset` documents are excluded from answering and may only be referenced historically ("in 2024 this was X").
- FR-2.6 **No internet research, by construction:** the runtime image ships no web-search/browse tool; retrieval can only hit the internal index. Confluence is the source of truth; SharePoint/PDF content is ingested through the same pipeline with equivalent citation metadata (file name + page/section).

### FR-3 Multi-department
- FR-3.1 Questions spanning departments fan out to the relevant subgraphs in parallel (per-branch timeout; phase 1: 30s overall budget).
- FR-3.2 A reconciliation node merges agreeing answers; conflicting answers are surfaced as a flagged conflict with both citations — never silently merged.

### FR-4 Personalization & learning
- FR-4.1 Responses are styled by role profile (risk / growth / partnerships / ops / business).
- FR-4.2 Users can rate responses (👍/👎 + optional comment) via a feedback endpoint.
- FR-4.3 (Phase 2) Feedback and behavioral signals are distilled into long-term memory via LTMS (`USER_PREFERENCE` auto-extraction + a `CUSTOM` strategy prompt for response-style patterns), and recalled per-user/per-role at answer time. `actorId` = end-user ID.

### FR-5 Knowledge sync (pipeline exists from MVP; daily schedule is Phase 2)
- FR-5.1 Daily end-of-day incremental sync per Confluence space (CQL `lastModified` cursor; batch ≤50 pages/request with backoff).
- FR-5.2 Deletions and permission changes produce index tombstones within one sync cycle.
- FR-5.3 Chunking ~300–800 tokens, semantic-boundary splits, with metadata: department, doc type (PRD/Operation/Technical/Risk/Security/Org/RCA/Ops), source URL + anchor (or file name + page for PDF/SharePoint), modified_at, lifecycle state.
- FR-5.4 Weekly full reconcile detects drift between source and index.
- FR-5.5 Sync runs as a separate scheduled job (not inside the request path); failures alert operators and leave the previous index serving.
- FR-5.6 **Token efficiency (G4):** sync uses zero LLM calls — change detection via version number + content hash; chunk-level diff so only changed chunks are re-embedded; embeddings computed locally (no MaaS tokens); doc-type classification by space/label/path rules, with a one-time small-model fallback only for new unclassifiable pages.
- FR-5.7 PDF ingestion: MVP reads PDFs from Google Drive (SharePoint simulation); production reads from SharePoint. Both feed the same text-extraction (OCR where needed) → chunk/metadata pipeline. Non-extractable files are indexed by title/metadata only and flagged.

### FR-6 Channels
- FR-6.1 `POST /invocations` (SDK convention) as the canonical API; `POST /chat` thin alias for manual testing.
- FR-6.2 Web UI portal (MVP + Production): Chat interface with citation rendering and a dashboard for usage/sync monitoring; served from the same deployment.
- FR-6.3 (Phase 2) Teams integration: webhook receiver route; replies in markdown with citation links; mention + DM; channel-thread replies stay in-thread; long answers are summarized with an expandable citation list (Teams message-size limits respected).
- FR-6.4 (Phase 2) MCP server: exposes the agent as an MCP-compatible tool endpoint for consumption by other agents or developer tooling.

### FR-7 Administration & operations
- FR-7.1 All queries/answers/refusals logged with user, departments consulted, citations, confidence, latency (PII-masked).
- FR-7.2 Department-level access control: who may query which department's knowledge — enforced via MCP Gateway Policy Groups (source side) and an allowlist in graph state (response side).
- FR-7.3 Cost: MaaS usage tracked per API key; budget alert configured before production traffic.

## Non-functional requirements

| NFR | Target (MVP) | Target (Prod) |
|---|---|---|
| Latency, single-dept answer | ≤ 30 s | p95 ≤ 15 s, p50 ≤ 6 s |
| Throughput | 1 rps | 10 rps sustained (autoscale to max 10 replicas) |
| Availability | best effort | 99.9% (min 2 replicas, health-gated deploys) |
| Citation accuracy (sampled audit) | ≥ 90% | ≥ 95% |
| False-answer rate (answered when docs don't support) | < 5% | < 1% |
| Refusal correctness (refused when docs DO cover it) | < 20% | < 10% |
| Sync freshness | n/a | ≤ 24 h from page edit to index |
| Cost | < $5 total | Budget-capped; alert at 80% of monthly budget |

## Out of scope (all phases of this spec)

Write actions on any source system; customer-facing deployment; model fine-tuning; non-Zalopay tenants; real-time (sub-minute) sync; voice channels; automated escalation ticket creation (phase-3 candidate).
