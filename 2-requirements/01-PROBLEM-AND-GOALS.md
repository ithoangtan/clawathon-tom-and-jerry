# 01 — Problem Statement & Goals

## Problem

Zalopay (~800 employees, ~20 departments) holds its institutional knowledge in Confluence (100–1,000 pages per department; 2K–20K pages total across **PRD, Operation, Technical, Risk, Security, Org-structure, RCA, and Ops-guidance** doc types), SharePoint to save PDF files (contracts, evidence, policies). Finding an authoritative answer today means knowing which department owns it, which space to search, and which page is still current. The consequences:

- Repeated questions in chat channels interrupt subject-matter experts (estimated 5–10 minutes saved per query answered by the agent instead of a human).
- Answers from generic LLM tools are unverifiable and sometimes wrong — unacceptable in a regulated fintech where a wrong compliance or ops answer has real cost.
- Knowledge decays silently: deprecated features and sunset processes keep being cited because nothing marks them stale.

## Target users

| Role | Need | Response style |
|---|---|---|
| Engineers/DevOps | Implementation details, runbooks, code refs | Technical |
| PM/PO | Feature status, PRDs, dependencies | Business-focused, PRD-linked |
| Ops/Support | Step-by-step procedures, escalation paths | Numbered steps, runbook links |
| Risk/Compliance/Legal | Requirements, edge cases, regulatory implications | Cautious, risk-flagged |
| Business/Exec | Status, impact, timeline | Executive summary |

## Goals

1. **G1 — Grounded answers only, delivered in Teams, with high accuracy.** Users ask about Zalopay knowledge and receive the answer in AI portal(chat bot login with Microsoft 365) or Microsoft Teams. Every answer is backed by retrieved internal documentation and carries citations (Confluence URL + section). If retrieval does not support an answer, the agent says so explicitly. Hallucinated answers are treated as defects, not quality variance. **The agent never researches the internet — it has no web tools by construction; Confluence is the source of truth.**
2. **G2 — Agent Center front door for 20 departments(MVP have 3 departments).** One conversational entry point (the Agent Center) receives every question. It does **not** answer from its own knowledge: it routes to the right department agent(s), lets them answer, then **forwards** the department answer (with the owning department named) back to the user — reconciling when multiple departments are involved. Users can also address any department agent directly, bypassing the center.
3. **G3 — Role-aware responses.** The same fact is rendered appropriately for an engineer vs a compliance officer, improving with feedback over time.
4. **G4 — Fresh knowledge, token-frugally.** Daily incremental sync from Confluence (SharePoint - PDF stores), with correct handling of edits, deletions, and deprecation, sustainable over a 5–10 year horizon. The sync path uses **zero LLM tokens** (cursor → hash-skip → chunk-level diff → local embeddings); LLM spend is reserved for answering users. Design in `03-ARCHITECTURE.md` §5a.
5. **G5 — Enterprise-operable.** Deployed on GreenNode AgentBase with autoscaling, versioned rollback, logs/metrics, cost budgets, credentialed integrations, and department-level access control — operable by a small team. Take advantage of the tools that GreenNode AgentBase is providing - remember to check their limits and start small. Ref ai-stack/agent-base and ai-stack.
6. **G6 — Diverse document types.** Confluence pages of all types (PRD, Operation, Technical, Risk, Security, Org, RCA, Ops-guidance), SharePoint documents - PDFs are all first-class, with doc-type carried as chunk metadata for filtering, styling, and lifecycle handling.

## Non-goals (explicitly out)

- Generating new knowledge, opinions, or advice beyond what the docs state.
- Web search / internet research of any kind — the runtime image contains no web tools (enforced by construction, not by prompt).
- Acting on systems (creating tickets, changing configs, executing payments) — read-only assistant in all phases of this spec.
- Replacing Confluence as the authoring system; the agent never writes to sources.
- Fine-tuning models on Zalopay data (in-context learning + retrieval only).
- Customer-facing use. Internal employees only.

## Guiding principles

- **Refusal is success** when docs don't cover the question. Optimize for trust, not answer rate.
- **Platform over plumbing**: any capability AgentBase provides as a managed service (memory, scaling, versioning, credential storage, governance, monitoring, budgets) is consumed, not rebuilt.
- **MVP full but simple to demo**: Need ask the engineer when we build a MVP to detail what are we build?
- **Cheap by default**: MaaS models (Qwen/MiniMax class) with small-model routing/grading;

## Constraints inherited from the platform (summary — full list in `03-ARCHITECTURE.md` §6)

Container deploy with greennode-agentbase-skills
