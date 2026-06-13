# Synthesis (Fable 5 pass) — Which Agent to Build, and How

This folder is a fresh synthesis of everything in this workspace, produced after reading:

- `docs/` — GreenNode AgentBase platform documentation (VNG Cloud)
- `greennode-agentbase-skills/` — the Claude skill bundle that drives the AgentBase lifecycle
- `500-AI-Agents-Projects/` — the example-agent catalog
- The raw notes in this `brainstrom/` folder (`Requirement-first.md`, `mvp/`, `agentbase architecture/`)

## Files

| File | Contents |
|---|---|
| `01-PLATFORM-CAPABILITIES.md` | What AgentBase actually provides, its hard contracts and limits, and what that implies for the design |
| `02-PATTERN-MATCHES.md` | Cross-reference of the brainstorm idea against the 500-projects catalog — which patterns to borrow |
| `03-RECOMMENDATION.md` | The decision: which agent to build, why, the options rejected, and the build shape |
| `04-FINAL-DECISION.md` | **Second-pass lock (read this first):** locked goals (Teams-first, Confluence-as-truth, no internet, Agent Center forward semantics, token-efficient daily sync), live-docs platform verification, and the corrections folded into the specs |

## The recommendation in three sentences

Build the **ZaloPay Internal Knowledge Agent**: a citation-grounded, supervisor-routed, corrective-RAG assistant for ~800 employees across ~20 departments, answering **only** from internal documentation (Confluence as source of truth) and refusing when the answer is not in the docs.

Implement it as **one LangGraph application in one Custom Agent runtime** (router node + department subgraphs), not as 21 separate runtimes — AgentBase's runtime contract, memory service, MCP governance, and autoscaling all favor a modular monolith that can be split later.

Ship a **2-day MVP** (router + 2 departments, Confluence-only, public networking) that is a strict subset of the production system (20 departments, hybrid per-dept indexes, MCP Gateway + Policy Groups, Private Networking via VPC peering), so nothing is thrown away when scaling up.

## Where the full spec lives

Implementation-ready specification → **`../../requirements-fable-5/`** (problem, scope, architecture, skills/tools/integrations, deployment plan, success criteria, user scenarios).

Demo-ready MVP specification → **`../../requirements-fable-5-mvp/`** (2 departments, ≈100 + ≈5,000 pages, full flow on AgentBase, build plan + demo script).
