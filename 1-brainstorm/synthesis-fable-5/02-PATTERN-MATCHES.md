# Cross-Reference — Brainstorm Idea vs the 500-AI-Agents-Projects Catalog

The catalog (`500-AI-Agents-Projects/`) contains ~20 fully working local agents (each with `agent.py`, `requirements.txt`, `metadata.yaml`) plus 500+ referenced external projects, organized by framework (LangChain ×8, LangGraph ×6, CrewAI ×5, LlamaIndex ×1) and by industry. For an "answer questions over a private corpus, never hallucinate" product, the catalog converges on a small set of patterns.

## Patterns to borrow (mapped to our requirements)

| Requirement from the brainstorm | Catalog pattern | Source | What we take |
|---|---|---|---|
| Answer from internal docs with citations | RAG over private KB | `13-customer-support-agent` (LangGraph + FAISS), `03-pdf-qa-agent` | Retrieve → generate with mandatory citation metadata on every chunk |
| "Only answer if it's in the docs" | **Corrective / Self-RAG** | LangGraph CRAG/Self-RAG tutorials referenced in catalog | Grade retrieved chunks *before* answering; low relevance → refuse ("not in docs") or re-query. This single pattern is what enforces the defining constraint |
| 1 router + 20 department agents | **Supervisor / hierarchical teams** | LangGraph `agent_supervisor`, `hierarchical_agent_teams` | Central router node classifies + routes to department subgraph; subgraphs share one process |
| Cross-department verification | Multi-agent debate → judge | `20-multi-agent-debate`, AutoGen group chat | Fan out to 2+ subgraphs, reconciliation node merges or flags conflict |
| Escalate when unsure | Human escalation | `13-customer-support-agent` | Confidence gate → hand off with context instead of guessing |
| Role-aware answers, learning from feedback | Conversation + semantic memory | AutoGen RetrieveChat; catalog "Memory" theme | Maps directly onto AgentBase STM events + LTMS `USER_PREFERENCE`/`CUSTOM` |
| Merchant/transaction analytics (future) | NL-to-SQL | SQL Query Agent | Out of scope now; viable phase-2 department tool |

## Framework verdict (consistent with `../PATTERN-SYNTHESIS.md` and `../../brainstorm/framework-selection.md`)

**LangGraph** is the spine:

- The product is a stateful graph with conditional routing and self-correction — LangGraph's native model.
- Router = supervisor node; each department = a corrective-RAG subgraph (retrieve → grade → answer-with-citation | refuse | escalate).
- Graph state carries session, evidence, citations, confidence — persisted via AgentBase Memory checkpointer (`AgentBaseMemoryEvents`).
- The skills bundle scaffolds it directly: `/agentbase-wizard init --langgraph` ships `langgraph_memory_main.py` with the SDK wiring already done.

CrewAI (role-play business automation) and AutoGen (code-gen/self-healing) were considered and rejected for the spine: both are weaker at deterministic retrieve-grade-cite control flow. CrewAI remains an option for isolated sub-tasks later.

## Standout reference implementations (ranked for this build)

1. **Customer Support Agent** (`13-customer-support-agent`) — LangGraph + FAISS + escalation. Closest working skeleton to our MVP; the MVP is essentially this, plus a supervisor and a citation contract.
2. **Multi-Agent Debate** (`20-multi-agent-debate`) — reconciliation pattern for cross-department conflicts.
3. **PDF Q&A Agent** (`03-pdf-qa-agent`) — document ingestion/chunking reference for Drive/SharePoint files (phase 2).
4. **SQL Query Agent** — phase-2 candidate for merchant/transaction analytics departments.
5. **Hierarchical agent teams** (LangGraph reference) — the topology for scaling 2 → 20 departments without changing graph shape.

## What the catalog does NOT solve (platform/spec must)

- Citation **verification** (link + section actually support the answer) — needs an explicit verify node + metric; no catalog project does this.
- Per-department **data isolation** — catalog agents are single-tenant; we enforce isolation at index level + MCP Policy Groups.
- Incremental sync over years (deletes, deprecation, "outdated but referenceable") — catalog agents ingest once; we need a sync pipeline with tombstones and doc-lifecycle metadata.
- Enterprise auth, audit, budget — all platform concerns (Identity, Gateway, Usage & Budget), not framework concerns.
