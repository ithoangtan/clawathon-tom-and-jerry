# Phase 5 — Executor node + state + router intent + graph wiring

## Goal

The integrating phase. Add a `workflow_execution` intent, run discovery → parse → execute the
steps in one pass → take real Jira actions → return a cited step-by-step markdown answer.
Depends on Phases 1, 2, 3, 4.

## Background (verified in repo)

- State: `GraphState` TypedDict in `app/graph/state.py` (context, routing, evidence,
  `answer`/`citations`/`status` outputs).
- Graph build: `app/graph/build.py` — `build_graph(deps)` wires
  `START → ingest_context → router → [dept subgraphs via Send] → reconcile → respond → suggest`.
  Conditional routing helpers: `_route_after_ingest`, `_make_route_after_router`. `respond`
  shapes final state; `service.state_to_response` maps `GraphState → ChatResponse`.
- Router: `make_router_node` (`app/graph/nodes/router.py`) classifies intent; it already has
  `SHORT_CIRCUIT_INTENTS` and an `action_request` intent — extend this machinery.
- Ports available on `deps`: `deps.llm`, `deps.retriever`, and (Phase 2) `deps.jira`.
- Citation shape: `chunk_to_citation` / `CitationModel` (see `synthesize.py`, `schemas.py`).

## What to build

### 1. State fields (`app/graph/state.py`)

Add to `GraphState` (all optional): `workflow_mode: bool`, `workflow_name: str | None`,
`workflow_page_id: str | None`, `workflow_candidates: list[dict]`, `jira_source: str | None`,
`jira_parent_key: str | None`, `workflow_discovery_note: str | None`. (The parsed
`WorkflowDefinition` can live in a transient local — no need to store the whole object in state
unless useful for streaming.)

### 2. Router intent (`app/graph/nodes/router.py` + `router.v1.yaml`)

- Add a `workflow_execution` intent. The router sets `intent="workflow_execution"` and
  `target_departments=[]` when the user asks to **run/execute a workflow** (verbs like "chạy
  workflow", "run workflow", "execute", or naming a known workflow + a ticket). Update
  `router.v1.yaml` examples accordingly. Treat it like the other short-circuit intents so it
  does **not** fan out to department subgraphs.

### 3. Executor node (`app/graph/nodes/workflow_executor.py`)

```python
def make_execute_workflow_node(llm, retriever, jira, *, settings=None) -> Callable[[GraphState], dict]:
    def execute_workflow(state):
        # 1. Discovery already ran (Phase 4) → workflow_page_id. If None → graceful "no workflow found".
        # 2. Load full page: retriever.get_page_chunks(department="workflow", page_id=...)
        #    → join chunk text in order = full workflow page text.
        # 3. parse_workflow(page_text, llm=llm)  → WorkflowDefinition
        # 4. Gate: is_executable(defn). If not ACTIVE → return a clear, cited refusal/warning
        #    (DEPRECATED: warn there is a newer version; do NOT execute in one-pass demo).
        # 5. Iterate defn.steps in order, dispatch by step.type, accumulate a step log + citations:
        ...
    return execute_workflow
```

Step dispatch (keep each branch small; the LLM does the heavy lifting per step):

| `type` | What the executor does |
|---|---|
| `fetch` | If a Jira key is in scope → `jira.get_issue(key)`; else `retriever.search` for the named source. Summarise into the step log. |
| `rag` | `retriever.search(department=<domain from responsible/labels>, query=step.action/input)` → cite top chunks (`chunk_to_citation`), include grounded findings. |
| `synthesize` | `llm.complete(tier=MAIN)` over accumulated context → drafted text for the step output. |
| `checklist` | Render the checklist items in the answer. Demo behaviour: ask the LLM to evaluate each item against gathered context and mark ✅ / ⚠️ needs-human-confirm — do not block. |
| `gate` | `llm.complete` (or simple rule) evaluates `step.condition` against context → record decision (skip step / escalate note). |
| `action` | Jira write per `defn.jira_source`: `existing-ticket` → attach to `jira_parent_key` (e.g. `jira.add_comment` or `create_issue(parent=key, ...)`); `auto-create` → `create_issue` an epic/parent (project=`jira_default_project`) then sub-tasks per step `Responsible`. Honour `jira_dry_run`. Record created keys/urls in the log + as a citation-like reference. |

- Build the final **markdown answer**: a heading with the workflow name + version, then each
  step as a numbered section (Responsible, what was done, findings/citations, any Jira
  action + resulting key/url). Write `answer`, `citations` (global list), `status="answered"`
  (or `"partial"` if a step degraded), and `source_departments` appropriately.
- Budget/deadline: respect `state["deadline_ts"]` like other nodes (`budget_exceeded`); if the
  budget is hit mid-run, finish with a partial answer rather than crashing.
- Errors: `WorkflowParseError`, `JiraUnavailable`, `RetrieverUnavailable` → graceful, cited
  explanation in the answer; never raise out of the node.

### 4. Graph wiring (`app/graph/build.py`)

- Register `discover_workflow` and `execute_workflow` nodes.
- Routing: when `intent == "workflow_execution"`, go `router → discover_workflow →
  execute_workflow → respond` (bypass dept subgraphs + `reconcile`). Add the conditional edge
  in the router-routing helper (`_make_route_after_router`) and `add_edge("execute_workflow",
  "respond")`. Discovery feeds the executor via state.
- Ensure `respond` / `state_to_response` pass the executor's `answer`/`citations`/`status`
  through unchanged (they already key off those fields — verify no special-casing needed).

## Acceptance criteria

- "Chạy workflow Campaign Risk Review cho ticket ZP-12345" → router picks
  `workflow_execution`; discovery finds the page; executor parses it, runs each step, performs
  the Jira action (or dry-run), and returns a numbered step-by-step answer citing the workflow
  page + policy refs + created Jira key.
- A `DEPRECATED`/non-`ACTIVE` workflow → clear warning, no execution.
- No-match discovery → graceful "no matching active workflow" reply.
- Normal (non-workflow) questions are unaffected — they still flow through dept subgraphs.

## Tests

- `tests/integration/` (or `tests/contract/`): drive `graph.invoke` with mocked `deps`
  (LLM returns canned routing JSON → `workflow_execution`; retriever returns the fixture page
  chunks for `get_page_chunks` + canned parse JSON; jira mocked). Assert the final state has a
  step-by-step `answer`, citations, `status="answered"`, and that `jira.add_comment`/`create_issue`
  was called with expected args (and skipped under `jira_dry_run`).
- A unit test for the non-ACTIVE gate path and the no-match path.

## Verify

`python -m ruff check .`, `make test-unit`, `make test-contract`. Then end-to-end:
`make up && make sync-confluence`, run the demo script from the README, and confirm a real
Jira sub-task/comment (or dry-run draft) plus a cited answer.

---

## Copy-paste Agent Prompt

> You are working in `code/zalopay-knowledge/`. Implement **Phase 5**, the integrating phase
> for the Workflow Platform. Phases 1 (retriever `filters` + `get_page_chunks`), 2
> (`deps.jira`), 3 (`parse_workflow`/`is_executable` in `app/workflow/`), and 4
> (`make_discover_workflow_node`) are merged.
>
> 1. Read `app/graph/state.py`, `app/graph/build.py` (`build_graph`, `_route_after_ingest`,
>    `_make_route_after_router`), `app/graph/nodes/router.py` (+ `router.v1.yaml`, intents,
>    `SHORT_CIRCUIT_INTENTS`), `app/graph/nodes/synthesize.py` (citations via
>    `chunk_to_citation`), `app/api/service.py` (`state_to_response`), and the Phase 3/4 modules.
> 2. Extend `GraphState` with optional fields: `workflow_mode`, `workflow_name`,
>    `workflow_page_id`, `workflow_candidates`, `jira_source`, `jira_parent_key`,
>    `workflow_discovery_note`.
> 3. Add a `workflow_execution` intent to the router (+ `router.v1.yaml` examples): set when the
>    user asks to run/execute a named workflow; `target_departments=[]`; treat as a non-fan-out
>    short-circuit intent.
> 4. Create `app/graph/nodes/workflow_executor.py` with
>    `make_execute_workflow_node(llm, retriever, jira, *, settings=None)`. It: reads
>    `workflow_page_id` (graceful reply if None); loads full page via
>    `retriever.get_page_chunks(department="workflow", page_id=...)`; calls `parse_workflow`;
>    enforces `is_executable` (only ACTIVE runs; DEPRECATED → warn, don't run); iterates steps
>    dispatching by `type` (fetch→jira.get_issue/retriever; rag→retriever.search + cite;
>    synthesize→llm MAIN; checklist→render+LLM-evaluate items, non-blocking; gate→evaluate
>    condition; action→Jira write per `jira_source`, honouring `jira_dry_run`). Accumulate a
>    numbered markdown step log + global citations; write `answer`/`citations`/`status`/
>    `source_departments`. Respect `deadline_ts` (`budget_exceeded`) and catch
>    `WorkflowParseError`/`JiraUnavailable`/`RetrieverUnavailable` into graceful cited text —
>    never raise out of the node.
> 5. Wire in `app/graph/build.py`: register `discover_workflow` + `execute_workflow`; when
>    `intent == "workflow_execution"` route `router → discover_workflow → execute_workflow →
>    respond` (bypass dept subgraphs + reconcile); `add_edge("execute_workflow","respond")`.
>    Verify `state_to_response` passes the answer/citations through.
> 6. Tests: an integration/contract test driving `graph.invoke` with mocked deps (routing →
>    workflow_execution; `get_page_chunks` returns a fixture page; canned parse JSON; jira
>    mocked) asserting a step-by-step answer, citations, `status`, and the Jira call args (and
>    dry-run skip). Unit tests for the non-ACTIVE gate and no-match paths.
>
> Do NOT alter normal Q&A routing for non-workflow questions. Run `python -m ruff check .`,
> `make test-unit`, `make test-contract`. Report changes + test output.
