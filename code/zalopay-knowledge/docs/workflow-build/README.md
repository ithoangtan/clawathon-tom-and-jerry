# Workflow Platform — Build Handoff

Implementation breakdown for the **Multi-Workflow Agent Platform** described in
[`use-case/SOLUTION-workflow-platform.md`](../../../../use-case/SOLUTION-workflow-platform.md).

Goal: the agent reads any workflow defined as a Confluence page (space `Workflow`),
discovers the right one, parses it, executes it step-by-step, and takes real Jira
actions — all without code changes per new workflow.

## Scope of this round

**Demo-first but full end-to-end flow.** Simplest implementation that still shows every
feature: discover → load full page → parse → execute steps → take a Jira action → return a
cited step-by-step answer. The executor runs in **one pass** (no multi-turn pause); steps
render as markdown, which the existing chat UI displays as-is — so **no frontend work is
required for the demo**. Parsing is **LLM-based**.

## Files & build order

Each file is self-contained: a coding agent can execute it with only that file + repo access.
Each ends with a **copy-paste Agent Prompt**.

| # | File | What it builds | Depends on |
|---|------|----------------|------------|
| 0 | [`00-foundation.md`](00-foundation.md) ✅ | Register `workflow` department + space + sync config | — |
| 1 | [`01-retriever-extensions.md`](01-retriever-extensions.md) ✅ | Label filtering + full-page fetch on `RetrieverPort` | 0 |
| 2 | [`02-jira-adapter.md`](02-jira-adapter.md) ✅ | `JiraPort` + `JiraClient` (reuses Confluence creds) | — |
| 3 | [`03-workflow-parser.md`](03-workflow-parser.md) ✅ | LLM parser: page → structured steps | 1 |
| 4 | [`04-discovery-node.md`](04-discovery-node.md) ✅ | Find the right workflow (name / semantic) | 1 |
| 5 | [`05-executor-and-wiring.md`](05-executor-and-wiring.md) ✅ | Executor node + state + router intent + graph edge | 1,2,3,4 |
| 6 | [`06-frontend-interactive.md`](06-frontend-interactive.md) | *(optional, post-demo)* interactive checklist/gate UI | 5 |

**Recommended order:** 0 → (1 ∥ 2) → 3 → 4 → 5. Phase 6 is a stretch.

**Status (2026-06-15):** Phases 0–5 complete. Code path is fully wired and unit/
integration tested (parser, discovery, executor, graph routing). The live demo is
**blocked**: the Confluence `Workflow` space has no `ACTIVE` workflow definition
page yet (only the space homepage + 2 default templates) — see "Demo script" below.

## Demo script (after Phase 5)

1. Publish one **`ACTIVE`** workflow page in space `Workflow`, e.g.
   *"Risk: Campaign Review — Lucky Wheel"* with `Jira Source: existing-ticket`,
   labels `zalopay-workflow`, `status:active`, `domain:risk`.
2. `make up && make sync-confluence`.
3. Ask in chat: **"Chạy workflow Campaign Risk Review cho ticket ZP-12345"**.
4. Expect: agent discovers the workflow, parses it, runs the steps, posts a Jira
   comment / creates a sub-task, and returns a step-by-step answer citing the workflow
   page + policy refs.

## Conventions every phase must follow

- **Node factory:** `make_x_node(ports..., *, settings: Settings | None = None) -> Callable[[State], dict]`
  (see `app/graph/nodes/router.py`, `synthesize.py`).
- **Prompts:** versioned YAML in `app/prompts/`, loaded via `load_prompt("name")`
  (`app/prompts/__init__.py`); declare `required_inputs`, `system`, `user`.
- **Config:** Pydantic `Settings` fields with `Field(default=..., description=...)`
  (`app/config.py`); secrets default to `""`. Mirror into `.env.example`.
- **Credentials:** resolve via `fetch_api_key_for_agent(settings, provider)`
  (`app/adapters/identity_client.py`) — works for both local env and AgentBase.
- **Ports/adapters:** protocol in `app/ports/`, concrete impl in `app/adapters/`,
  wired in `app/adapters/deps.py`.
- **Tests:** `tests/unit/` (logic, `monkeypatch` + port mocks) and `tests/contract/`
  (HTTP shape). Run `make test-unit`, `make test-contract`, `python -m ruff check .`.

## Definition-lifecycle gate (important)

Per the SOLUTION doc, a workflow page's `Definition Status` is one of
`DRAFT → IN_REVIEW → ACTIVE → DEPRECATED → ARCHIVED`. **Only `ACTIVE` is executable.**
`DEPRECATED` runs only after explicit user confirmation; all others are search/display only.
The parser (Phase 3) surfaces this; the executor (Phase 5) enforces it.
