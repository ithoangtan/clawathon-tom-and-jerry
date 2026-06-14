# Requirements — Zalopay Internal Knowledge Agent (Fable 5 spec)

Complete, implementation-ready specification for the agent selected in `../brainstrom-fable-5/synthesis-fable-5/03-RECOMMENDATION.md` and **locked in `../brainstrom-fable-5/synthesis-fable-5/04-FINAL-DECISION.md`**: a citation-grounded, supervisor-routed, corrective-RAG knowledge assistant for Zalopay — Web UI portal-first (Teams in Phase 2), Confluence-as-truth, no internet research — built with LangGraph and deployed on **GreenNode AgentBase** via `greennode-agentbase-skills`.

> Demo-ready MVP subset → **`../requirements-fable-5-mvp/`** (3 departments — Risk, Grow Enablement, Bank Partnerships — ≈1,000 pages total, full flow preserved).

## Documents

| Doc | Contents |
|---|---|
| `01-PROBLEM-AND-GOALS.md` | Problem statement, users, goals, non-goals, guiding principles |
| `02-SCOPE-AND-CAPABILITIES.md` | Capabilities in/out per phase (MVP → Production), functional requirements, behavioral contract |
| `03-ARCHITECTURE.md` | System design, LangGraph graph shape, data flow, and the explicit mapping to AgentBase modules and the skills framework |
| `04-SKILLS-TOOLS-INTEGRATIONS.md` | Required skills (greennode-agentbase-skills usage), tools, external integrations, models, credentials |
| `05-DEPLOYMENT-PLAN.md` | Phase-by-phase deployment on AgentBase: prerequisites, MVP, production, rollback, operations |
| `06-SUCCESS-CRITERIA.md` | Acceptance criteria, metrics, test plan, release gates |
| `07-USER-SCENARIOS.md` | Full-flow user scenarios — core Q&A, knowledge lifecycle, access/abuse, operations on the Web UI portal MVP; Teams-specific realities marked Phase 2 (★ subset = MVP demo set) |

## One-paragraph summary

Zalopay employees lose time hunting answers spread across Confluence, GitLab, SharePoint, and PDFs, and existing chat tools hallucinate. This agent answers questions **only** from internal documentation (Confluence as source of truth; it has no internet-research capability by construction), always cites the exact page and section, says "not in the docs" when retrieval doesn't support an answer, adapts responses to the asker's role, and consults multiple departments when a question spans them. Users ask through a **Web UI portal** (Microsoft 365 login; Microsoft Teams in Phase 2), via an **Agent Center** that never answers from its own knowledge — it routes to department agents and forwards their answers (department agents are also directly addressable). It runs as a single Custom Agent runtime on GreenNode AgentBase (port 8080, `/health`, stateless), uses the platform Memory service for conversation state and learned preferences, MaaS (Qwen/MiniMax) for inference, MCP Gateway + Policy Groups for governed source access, and Private Networking (VPC peering) to reach internal systems in production. The full lifecycle — scaffold, configure, test, deploy, monitor, teardown — is driven by the `greennode-agentbase-skills` Claude skills.

## Reading order for implementers

1. `01` then `02` for what to build.
2. `03` for how it's shaped and why.
3. `04` + `05` while building/deploying (keep `greennode-agentbase-skills/README.md` open alongside).
4. `07` for how real users will behave in the portal (Teams in Phase 2) — drives the eval sets.
5. `06` before calling anything done.
