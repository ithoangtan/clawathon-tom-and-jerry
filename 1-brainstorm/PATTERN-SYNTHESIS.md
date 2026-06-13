# Pattern Synthesis & Build Decision — Zalopay Enterprise Knowledge Agent

> This document extracts the recurring patterns from `500-AI-Agents-Projects/`, maps them onto the GreenNode AgentBase platform (`docs/`), and lands on a concrete recommendation for **how best to build the agent described in this brainstrom folder**. It is the bridge between the raw idea (`Requirement-first.md`, `mvp/`, `agentbase architecture/`) and the implementation-ready spec in `../requirements-fable-5/` (MVP subset: `../requirements-fable-5-mvp/`).

---

## 1. The Idea, Restated in One Line

A single source-of-truth knowledge assistant for ~800 Zalopay employees across ~20 departments, answering only from internal documentation (Confluence as source of truth, plus GitLab and Drive/SharePoint), with mandatory citations, role-aware responses, cross-department escalation, and continuous learning — deployed on GreenNode AgentBase and surfaced through Teams/Zalo plus a web dashboard.

The defining constraint is **grounded answering**: if the answer is not in the docs, the bot must say so and never hallucinate. Everything else (multi-agent, personalization, sync) serves that constraint.

---

## 2. What the 500 Projects Actually Converge On

Scanning the 20 local example agents and the framework catalog in `500-AI-Agents-Projects/README.md`, the same handful of patterns recur for any "answer questions over a private corpus" product:

| Pattern (from the catalog) | Where it shows up | What we borrow |
|---|---|---|
| **RAG over a private knowledge base** | `13-customer-support-agent` (LangGraph + FAISS), `03-pdf-qa-agent` (LlamaIndex) | Retrieve-then-generate with citations is the backbone of every doc-Q&A agent |
| **Corrective / Self / Agentic RAG** | LangGraph tutorials (`langgraph_crag`, `langgraph_self_rag`, `langgraph_agentic_rag`) | Grade retrieved chunks *before* answering; if relevance is low, refuse or re-query. This is exactly the "don't hallucinate" requirement. |
| **Supervisor / Router** | LangGraph `agent_supervisor` | A central agent classifies the query and routes to a specialist — our Central Router → Department agents |
| **Hierarchical agent teams** | LangGraph `hierarchical_agent_teams` | A top supervisor delegates to sub-supervisors/specialists — the model for 1 router + 20 department agents |
| **Multi-agent collaboration + judge/consensus** | `20-multi-agent-debate`, AutoGen group chat | When two departments disagree, a coordinator reconciles answers — our cross-department verification |
| **Escalation to human** | `13-customer-support-agent` | When confidence is low or the topic is sensitive, hand off instead of guessing |
| **Conversation + semantic memory** | AutoGen RetrieveChat, the catalog's "Memory" theme | Short-term history + long-term facts so the bot improves and stays consistent |

**Conclusion from the corpus:** the highest-value, lowest-risk shape for this product is a **supervisor-routed, citation-grounded, corrective-RAG system** — not a free-form chat agent and not a single monolithic RAG. Every comparable production example in the catalog that answers over private docs uses some combination of these, and **LangGraph is the framework that natively expresses all of them** (stateful graph, supervisor, hierarchical teams, the full RAG-grading family).

---

## 3. Mapping the Pattern onto AgentBase

The patterns above are framework concepts. AgentBase supplies the production substrate. The mapping is clean and is the reason this project is a good fit for the platform:

| Need (from the idea) | 500-projects pattern | AgentBase module that provides it |
|---|---|---|
| Run the router + department agents 24/7, scale with load | Supervisor + sub-agents | **Agent Runtime** — Custom Agent containers, versioning, autoscaling (`minReplicas`/`maxReplicas` 1–10, CPU/RAM thresholds 25–75%), `GET /health` |
| Reach Confluence / GitLab / Drive that live inside Zalopay's network | Tool calls in RAG nodes | **MCP Governance** (MCP Gateway + Policy Group) for governed tool access + **Private Networking** (VPC Peering) so the runtime/gateway call internal systems without traversing the public internet |
| Store Confluence/Slack/Teams tokens safely, inject at runtime | — | **Access Control** — Agent Identity + credential store (API Key / OAuth2), auto-injected |
| Conversation history + role/learning facts | Memory pattern | **Memory** — Short-Term (events per session) + Long-Term (semantic records via LTMS: `SEMANTIC`, `USER_PREFERENCE`, `CUSTOM`) |
| Cheap LLM serving (Qwen / MiniMax) via OpenAI-compatible endpoint | — | **AgentBase LLM / MaaS** — OpenAI-compatible endpoint, API keys, rate limits |
| Teams / Zalo chat surface fast | Chat front-end | **OpenClaw** (Marketplace) for Telegram/Zalo, or a Custom Agent webhook for Teams |
| Cost ceilings per department/model, alerts | Observability theme | **Usage & Budget** — per-agent/model cost tracking + budget alerts |
| Who can query which department | RBAC | **Policy Groups** on the Gateway + **Team & Permissions** (Root/Admin/Member/Viewer) |
| Drive the whole lifecycle from Claude | — | **greennode-agentbase-skills**: `/agentbase-wizard` → `-identity` → `-llm` → `-memory` → `-deploy` → `-gateway` → `-policy` → `-monitor` |

There is no capability gap. Every requirement in `Requirement-first.md` has a home on the platform.

---

## 4. The Build Decision

### 4.1 Framework: **LangGraph** (primary)

LangGraph wins because the product is fundamentally a **stateful, multi-node graph with conditional routing and self-correction**, and that is precisely what LangGraph models. Concretely:

- The **Central Router** is a LangGraph supervisor node that classifies intent and routes to a department subgraph.
- Each **Department agent** is a subgraph implementing **corrective RAG**: retrieve → grade relevance → (answer with citation | refuse "not in docs" | escalate cross-department).
- **Cross-department** queries fan out to multiple subgraphs and a **reconciliation node** merges/flags conflicts (the debate→judge pattern).
- Graph state carries the session, retrieved evidence, citations, and confidence — and persists via AgentBase Memory.

CrewAI/AutoGen were considered. CrewAI is excellent for role-play business automation but weaker at the deterministic retrieve-grade-cite control flow we need; AutoGen shines for code-gen/self-healing, which is not this product. They remain options for isolated sub-tasks (e.g., a CrewAI "report writer" crew), but the spine is LangGraph. The sibling strategy folder's `../brainstorm/framework-selection.md` reaches the same conclusion for stateful RAG.

### 4.2 Retrieval: hybrid, per-department, grounded

- **Hybrid search** (dense embeddings + keyword/BM25) per-department index, with citation metadata (Confluence page ID + section anchor) attached to every chunk.
- **Corrective RAG gate** is non-negotiable: a relevance grade decides answer-vs-refuse. This is the mechanism that satisfies "only answer if it's in the docs."
- **Chunking** ~300–800 tokens with doc-type classification (Org / PRD / Tech / RCA / Ops) carried as metadata for filtering and lifecycle ("deprecated but referenceable").

### 4.3 Memory: AgentBase Memory, not a bespoke store

Use Short-Term events for conversation continuity and Long-Term `USER_PREFERENCE` + `CUSTOM` strategies for role-aware response patterns and feedback-driven learning. This removes the need to operate our own vector store *for memory* (the document corpus index is separate and may be self-hosted Weaviate/FAISS in VPC).

### 4.4 Topology: phased, not big-bang

- **MVP:** 1 router + 2 department agents (Engineering, Product), Confluence-only, in-memory/FAISS index, one Custom Agent runtime, Teams or `/chat` endpoint. Proves the end-to-end grounded-RAG loop. Spec in `../requirements-fable-5-mvp/`.
- **Production (≈4 weeks):** 1 router + 20 department agents, hybrid per-dept indexes, daily incremental Confluence/GitLab/Drive sync, Private Networking, full RBAC/audit, autoscaling, DR. Spec in `../requirements-fable-5/`.

The MVP is a strict subset of production — same graph shape, same citation contract — so nothing is thrown away when scaling up.

### 4.5 Deployment path (Claude-driven, via skills)

```
/agentbase-wizard init zalopay-knowledge --langgraph
/agentbase-llm api-keys create   → Qwen/MiniMax via OpenAI-compatible endpoint
/agentbase-identity              → store Confluence / GitLab / Teams credentials
/agentbase-memory create         → short-term + LTMS strategies
/agentbase-gateway + /agentbase-policy → governed tool access, per-dept policy
/agentbase-wizard test local|docker
/agentbase-deploy                → build → push → deploy (Private mode for prod)
/agentbase-monitor               → logs, metrics, dashboard
```

---

## 5. Top Risks the Pattern Forces Us to Address Early

1. **Hallucination / wrong citation** — mitigated by the corrective-RAG grade + citation verification step; tracked as a first-class metric (citation accuracy).
2. **Network reach to internal sources** — requires Private Networking (VPC Peering) provisioned before prod; do not assume public API access to Confluence/GitLab.
3. **Per-department data isolation** — enforce at the Gateway (Policy Groups) *and* the index level, not just in prompts.
4. **Sync correctness over 5–10 years** — incremental sync must handle deletes/deprecation, or the "single source of truth" promise breaks.
5. **Cost at 20 agents** — cheap models (Qwen/MiniMax) + Usage & Budget caps per department.

---

## 6. Where to Go Next

- Full, build-ready specification → **`../requirements-fable-5/`**
- Fastest end-to-end proof → **`../requirements-fable-5-mvp/`**
- Locked goals & second-pass verification → **`synthesis-fable-5/04-FINAL-DECISION.md`**
- Framework deep-dive and trade-offs → `../brainstorm/framework-selection.md`, `../brainstorm/best-practices.md` (sibling strategy folder)
- Original requirements interview → `Requirement-first.md`
- Earlier architecture drafts → `agentbase architecture/ZALOPAY_ARCHITECTURE.md`, `agentbase architecture/IMPLEMENTATION_ROADMAP.md`

**Decision in one sentence:** build a LangGraph supervisor-routed, corrective-RAG, citation-grounded multi-agent system, backed by AgentBase Runtime + Memory + MCP Governance + Private Networking, shipped MVP-first then scaled to 20 departments.
