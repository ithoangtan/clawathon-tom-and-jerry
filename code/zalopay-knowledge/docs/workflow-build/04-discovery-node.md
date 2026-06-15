# Phase 4 — Workflow Discovery node

## Goal

Given a user request, find the right workflow definition page. Two paths (SOLUTION §Tầng 2):
- **A. Explicit name** — "Chạy workflow *Campaign Risk Review* cho ticket ZP-12345" → load that
  workflow directly.
- **B. Semantic** — "Review campaign Lucky Wheel mới, quà vé máy bay" → semantic search over the
  `workflow` index filtered to `zalopay-workflow` + `status:active`, return top matches with score.

Output: the chosen workflow's `name` + `page_id` (and any parsed ticket key), written to state
for the executor (Phase 5). Depends on Phase 1 (filtered search + full-page fetch).

## Background (verified in repo)

- Node pattern: `make_x_node(ports..., *, settings=None) -> Callable[[State], dict]`
  (`app/graph/nodes/router.py`, `retrieve.py`).
- After Phase 1, `retriever.search(department="workflow", query=..., filters={...})` returns
  scored `RetrievedChunk`s; each chunk has `source` (=page_id), `title`, `score`, `labels`.
- Prompt loader + `parse_json_response` as in Phase 3.

## What to build

### 1. Prompt (`app/prompts/workflow_discovery.v1.yaml`)

- `required_inputs`: `question`.
- Extract, as JSON: `explicit_name` (workflow name if the user named one, else null),
  `jira_key` (a ticket key like `ZP-12345` if present, else null), and a cleaned
  `search_query` for semantic matching.

### 2. Node (`app/graph/nodes/workflow_discovery.py`)

```python
def make_discover_workflow_node(retriever, llm, *, settings=None) -> Callable[[GraphState], dict]:
    def discover_workflow(state):
        # 1. LLM extracts explicit_name / jira_key / search_query
        # 2a. explicit_name → search filtered by title-ish query + labels, pick best title match
        # 2b. else semantic: retriever.search(department="workflow",
        #        query=search_query, filters={"labels": ["zalopay-workflow", "status:active"]}, k=5)
        # 3. Group chunk hits by `source` (page_id); rank pages by best chunk score
        # 4. Write top candidate + alternatives to state
        ...
    return discover_workflow
```

State writes (new fields, finalised in Phase 5's state extension):
- `workflow_page_id`: best match page_id (or None if nothing found)
- `workflow_name`: its title
- `workflow_candidates`: list of `{name, page_id, score}` (top ~3, for transparency/logging)
- `jira_parent_key`: extracted ticket key if any

Behaviour notes:
- Filter must include `status:active` so only ACTIVE workflows are discoverable by default
  (matches the definition-lifecycle gate). `ARCHIVED`/`DRAFT` pages won't carry `status:active`.
- If no candidate clears a minimal score threshold, write `workflow_page_id=None` and a short
  `workflow_discovery_note` explaining nothing matched (executor turns this into a graceful reply).
- For the demo, single best candidate is enough; do **not** block on a confirmation round-trip
  (keep it one-pass). Surfacing alternatives in the answer text is sufficient.

## Acceptance criteria

- Explicit-name request resolves to the correct page_id.
- Semantic request returns the best ACTIVE workflow page by score, plus alternatives.
- A no-match request yields `workflow_page_id=None` + a note, no crash.
- Jira key in the prompt is captured into `jira_parent_key`.

## Tests

- `tests/unit/test_workflow_discovery.py`: mock `LLMPort` (canned extraction JSON) and
  `RetrieverPort.search` (canned scored chunks across 2–3 page_ids). Assert correct top
  candidate, grouping by `source`, the `status:active` filter is passed, jira_key extraction,
  and the no-match path.

## Verify

`python -m ruff check .` and `make test-unit`.

---

## Copy-paste Agent Prompt

> You are working in `code/zalopay-knowledge/`. Implement **Phase 4**: a Workflow Discovery
> graph node. Assumes Phase 1 (filtered `search` + `get_page_chunks`) is merged.
>
> 1. Read `app/graph/nodes/router.py` and `retrieve.py` (node factory pattern, prompt usage,
>    `parse_json_response`), and `app/ports/retriever.py` (now with `filters`). Read SOLUTION
>    §Tầng 2 for the two discovery paths.
> 2. Create `app/prompts/workflow_discovery.v1.yaml` (required_inputs: question) that extracts
>    JSON `{explicit_name, jira_key, search_query}`.
> 3. Create `app/graph/nodes/workflow_discovery.py` with
>    `make_discover_workflow_node(retriever, llm, *, settings=None)`. It: calls the LLM to extract
>    name/jira_key/query; if a name is given resolves to that workflow, else runs
>    `retriever.search(department="workflow", query=search_query,
>    filters={"labels":["zalopay-workflow","status:active"]}, k=5)`; groups hits by `source`
>    (page_id); ranks pages by best chunk score; writes `workflow_page_id`, `workflow_name`,
>    `workflow_candidates` (top 3 `{name,page_id,score}`), `jira_parent_key`. If nothing clears a
>    minimal threshold, write `workflow_page_id=None` + `workflow_discovery_note`. Keep it one-pass
>    (no confirmation round-trip).
> 4. Add `tests/unit/test_workflow_discovery.py` mocking the LLM and retriever: assert top
>    candidate selection, grouping by `source`, that the `status:active` filter is applied,
>    jira_key extraction, and the no-match path.
>
> Run `python -m ruff check .` and `make test-unit`. Report changes + test output.
