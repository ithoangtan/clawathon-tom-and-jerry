# Recommendation — Build the ZaloPay Internal Knowledge Agent, as One LangGraph Runtime

## The decision

**Build:** a citation-grounded internal knowledge assistant for ZaloPay (~800 employees, ~20 departments). Confluence is the source of truth (GitLab + Drive/SharePoint later). The agent answers **only** when retrieval supports the answer, always cites page + section, adapts tone to the asker's role, fans out across departments when needed, and refuses rather than hallucinates.

**Build it as:** a single LangGraph application — supervisor/router node + per-department corrective-RAG subgraphs — packaged in one Docker image and deployed as **one Custom Agent runtime** on GreenNode AgentBase, driven end-to-end by the `greennode-agentbase-skills` lifecycle.

**Ship it as:** a 2-day MVP (router + Engineering + Product subgraphs, Confluence-only, FAISS in-container, public networking, `/chat` + Teams webhook) that is a strict structural subset of production (20 subgraphs, hybrid per-dept indexes in VPC, MCP Gateway + Policy Groups, Private Networking, full audit).

## Why this agent (and not something else)

1. **It's the only idea in the brainstorm with a fully specified problem.** `Requirement-first.md` contains real scope (20 depts, 500K–2M pages, doc types, sync cadence, NFRs). The 500-projects catalog offers inspiration (support bots, SQL agents, research agents) but no competing idea with this depth of organizational need.
2. **Platform fit is total.** Every requirement maps to a platform module with no gaps (see `01-PLATFORM-CAPABILITIES.md` §10 and the table in `../PATTERN-SYNTHESIS.md` §3): runtime ⇄ supervisor system, Memory ⇄ continuity + learning, MCP Governance ⇄ RBAC on sources, Private Networking ⇄ internal reach, MaaS ⇄ cheap Qwen/MiniMax serving, Usage & Budget ⇄ cost caps.
3. **Highest leverage per engineering hour.** A grounded knowledge agent compounds: every department onboarded reuses the same graph shape, sync pipeline, and citation contract. Catalog alternatives (e.g., a fraud-analysis or SQL agent) are deeper integrations with narrower audiences and heavier data-access risk for a first deployment.
4. **The defining constraint is testable.** "Grounded or refuse" gives crisp acceptance criteria (citation accuracy, refusal correctness) — rare for agent products, and exactly what a first production agent needs.

## Key architecture decisions (deltas and confirmations vs earlier notes)

| # | Decision | Rationale |
|---|---|---|
| D1 | **One runtime, not 21** | Platform scales replicas (1–10) within a runtime; departments are subgraphs + index partitions, not deployment units. 21 runtimes multiply cost, deploy time, and version skew with zero isolation benefit (isolation lives in the index + Policy Groups). Split into 2–3 runtimes later only if load profiles demand it |
| D2 | **LangGraph + corrective-RAG gate** | The grade-before-answer node is the mechanism enforcing "never hallucinate" (see `02-PATTERN-MATCHES.md`) |
| D3 | **AgentBase Memory for state; separate index for corpus** | STM checkpointer + LTMS (`USER_PREFERENCE`, `CUSTOM`) replace the bespoke Postgres/Redis learning stack from `agentbase architecture/ZALOPAY_ARCHITECTURE.md`. The 500K–2M-page corpus stays in a dedicated retrieval index (FAISS in-image at MVP → Weaviate/pgvector in ZaloPay VPC at prod) |
| D4 | **Source access via MCP Gateway + Policy Groups (prod)** | Department-level access control enforced by platform policy, not prompts. MVP may call Confluence API directly with an Identity-stored token |
| D5 | **Private Networking is a week-0 dependency** | VPC peering needs GreenNode support lead time; without it, prod cannot reach internal Confluence/GitLab. Kick off immediately, in parallel with the MVP |
| D6 | **MaaS models only (Qwen/MiniMax)** | OpenAI-compatible endpoint, unified billing, budget alerts; small model for routing/grading, larger for synthesis |
| D7 | **Teams via custom webhook route in the runtime; OpenClaw optional for Zalo** | OpenClaw cannot host custom logic or Teams; our container is free to expose any routes besides `/health` |
| D8 | **Sync = daily incremental batch with tombstones** | End-of-day Confluence delta sync (modified/deleted), doc-lifecycle metadata (`active`/`deprecated`/`sunset`) so the 5–10-year "source of truth" promise holds |

## What changed vs the earlier drafts in this folder

- `ZALOPAY_ARCHITECTURE.md` proposed Kubernetes on ZaloPay infra + ELK + Jaeger + Celery + Postgres + Redis + 3-node Weaviate. **Most of that stack is replaced by platform services** (Runtime autoscaling/versioning, Memory, Monitor, Usage & Budget). What remains self-managed is only the corpus index + sync job.
- The earlier draft's `--flavor gpu-small --region us-east-1` examples don't match the platform (flavors like `1x1-general`, HCM region); corrected in the spec.
- The 2-day MVP from `mvp/` survives almost intact, with two upgrades: scaffold via `/agentbase-wizard init --langgraph` (instead of hand-rolled FastAPI) so the SDK contract (port 8080, `/health`, `/invocations`, headers) is right from minute one, and use AgentBase Memory instead of SQLite for session state.

## Top risks (carried into the spec)

1. **Wrong/missing citations** → corrective-RAG gate + citation-verification node + citation accuracy as a release-blocking metric.
2. **VPC peering lead time** → request at project start; MVP designed to run Public meanwhile.
3. **Per-department leakage** → isolation enforced at index partition + Policy Group, tested adversarially.
4. **Sync drift (deletes/deprecation)** → tombstone handling + weekly full-reconcile pass.
5. **Cost at scale** → MaaS budget alerts per key; cache frequent queries; small-model routing.

## Next step

Implement against **`../../requirements-fable-5/`** — start with `05-DEPLOYMENT-PLAN.md` Phase 0 (credentials, VPC peering request) and the MVP build plan in **`../../requirements-fable-5-mvp/`**.

> **Second pass (2026-06-13):** goals and approach were re-reviewed and LOCKED in `04-FINAL-DECISION.md`, including live-docs verification of the platform claims above and several SDK-level corrections. That file supersedes wording here where they differ.
