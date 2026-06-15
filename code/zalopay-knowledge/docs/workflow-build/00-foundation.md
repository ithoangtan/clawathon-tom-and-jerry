# Phase 0 — Foundation: register the `workflow` department & sync the space

> **STATUS: ✅ DONE (code) — 2026-06-15.** Live-sync verification pending (needs services up
> + ≥1 page in the `Workflow` space). See "Result" at the bottom.

## Goal

Make the Confluence space `Workflow` flow through the existing ingestion pipeline into its
own OpenSearch index (`zalopay_workflow`), with Confluence labels preserved. Pure config +
one registry entry — no new logic.

## Background (verified in repo)

- The ingestion pipeline already syncs any configured space and **preserves Confluence
  labels** end-to-end: `app/ingestion/confluence.py` (fetch + `_extract_labels`) →
  `app/ingestion/chunker.py` (`chunk_text(... labels=...)`) → `app/ingestion/opensearch_indexer.py`
  (index mapping has `space`, `source`=page_id, `labels` keyword fields).
- Spaces are configured by `CONFLUENCE_SPACES` (JSON map `department_key → space_key`) in
  `app/config.py` (field `confluence_spaces`, computed `confluence_space_map`).
- Departments are registered in `app/common/departments.py`.
- Index name is `{OPENSEARCH_INDEX_PREFIX}_{department}` → `zalopay_workflow`.
- Sync is triggered by `POST /api/admin/sync` (`app/api/admin_routes.py`) / `make sync-confluence`.

## Files to change

- `app/common/departments.py` — add a `workflow` department entry (key, display name,
  description). Keep it minimal; mirror an existing entry like `risk`. This department is a
  **container for workflow definitions**, not a Q&A domain — note that in its description.
- `.env` and `.env.example` — add `workflow` to `CONFLUENCE_SPACES`, e.g.
  `CONFLUENCE_SPACES={"risk":"RISK","grow_enablement":"GROW","bank_partnerships":"BANK","workflow":"Workflow"}`
  (use the real space key for the `Workflow` space).
- If the router/allowed-departments logic auto-includes all registered departments, ensure
  `workflow` does **not** get treated as a normal answerable department in everyday Q&A. If
  there's an allow-list or routable-departments set, exclude `workflow` from normal routing
  (it's only entered via the workflow-execution intent added in Phase 5). Check
  `app/common/departments.py` and `app/graph/nodes/router.py` for how `allowed_departments`
  is derived.

## Acceptance criteria

- `make sync-confluence` (or `POST /api/admin/sync {"source":"confluence","department":"workflow"}`)
  creates/populates the `zalopay_workflow` index.
- Indexed chunks carry the page's labels (`zalopay-workflow`, `status:active`, `domain:*`) in
  the `labels` field and the page_id in `source`.
- Existing Q&A behaviour is unchanged — `workflow` is not surfaced as a normal answer source.

## Tests

- Unit test in `tests/unit/` confirming `Settings.confluence_space_map` includes `workflow`
  when `CONFLUENCE_SPACES` contains it (follow `tests/unit/test_config.py` pattern with
  `monkeypatch`).
- Unit test confirming the `workflow` department is registered and (if applicable) excluded
  from the default routable set.

## Verify

`python -m ruff check .` and `make test-unit`. Then with services up, run the sync and query
OpenSearch for the `zalopay_workflow` index to confirm chunks + labels exist.

---

## Copy-paste Agent Prompt

> You are working in `code/zalopay-knowledge/` (FastAPI + LangGraph RAG agent). Implement
> **Phase 0** of the Workflow Platform: register a new Confluence-backed department named
> `workflow` so the `Workflow` space syncs into its own OpenSearch index.
>
> Do this:
> 1. Read `app/common/departments.py` and add a `workflow` department entry, mirroring the
>    structure of an existing one (e.g. `risk`). Its description must state it is a container
>    for **workflow definitions**, not a normal Q&A domain.
> 2. Add `workflow` to the `CONFLUENCE_SPACES` JSON map in both `.env` and `.env.example`
>    (department key `workflow` → the real `Workflow` space key).
> 3. Read `app/graph/nodes/router.py` and how `allowed_departments` is derived. If all
>    registered departments are auto-routable, exclude `workflow` from normal Q&A routing
>    (it will be entered only via a dedicated intent in a later phase). Make the smallest
>    change that achieves this; leave a `# workflow: entered via workflow-execution intent`
>    style comment.
> 4. Add unit tests under `tests/unit/` (follow `tests/unit/test_config.py`): one asserting
>    `confluence_space_map` includes `workflow`, one asserting the department is registered
>    and excluded from default routing.
>
> Do NOT change the ingestion pipeline — it already preserves labels and indexes
> `space`/`source`/`labels`. Run `python -m ruff check .` and `make test-unit`. Report what
> you changed and the test output.

---

## Result (2026-06-15)

**Design refinement vs original plan:** instead of a one-off exclusion hack, added a
first-class `routable: bool = True` flag on the `Department` dataclass. `workflow` is
registered with `routable=False` — so it **is** synced + indexed (ingestion/retriever use
`iter_keys()`/`all_departments()` = full registry) but is **excluded** from the Q&A surface
(router catalog, role-access defaults, escalation/scope copy, frontend department list, which
now use new `routable_departments()` / `routable_keys()` helpers).

**Files changed:**
- `app/common/departments.py` — `WORKFLOW` enum value; `routable` field; `workflow` registry
  entry (`space_env_var=CONFLUENCE_SPACE_WORKFLOW`, `routable=False`); new
  `routable_departments()` + `routable_keys()`; `department_catalog_text`,
  `format_department_keys_for_prompt`, `export_frontend_catalog` switched to routable-only.
- `app/graph/nodes/router.py` — `_VALID_DEPARTMENTS`, allowed-fallback, clarify options → routable.
- `app/graph/nodes/ingest_context.py` — role-access default → routable.
- `app/graph/nodes/respond.py` — capability_query department listing → routable.
- `app/common/product_copy.py` — scope/escalation/owner copy → routable.
- `.env` + `.env.example` — added `"workflow":"Workflow"` to `CONFLUENCE_SPACES`.
- Tests: `tests/department_fixtures.py` (`ALL_KEYS`/`ALL_DEPARTMENT_KEYS` now routable-only;
  added `WORKFLOW`, `REGISTERED_KEYS`); `tests/unit/common/test_departments.py` (registry vs
  routable assertions + new `test_workflow_is_registered_but_not_routable`);
  `tests/unit/graph/test_ingest_context.py` (allowed = routable).

**Verification:** full unit suite — clean tree baseline `7 failed, 417 passed, 124 errors` →
after Phase 0 `7 failed, 418 passed, 124 errors`. **Zero regressions** (the 7 failures + 124
collection errors are pre-existing and unrelated — broken `embeddings`/`helpers` imports and
test-env LLM/Jira config). `ruff --select F` on changed files: clean.

**⚠️ Open item — space key:** other spaces use the `Clawathon*` prefix (`ClawathonRisk`...) but
the workflow space was configured as `"Workflow"` (per confirmed config). If the real Confluence
space key differs (e.g. `ClawathonWorkflow`), update `CONFLUENCE_SPACES` in `.env`.

**Next to demo live:** needs ≥1 page in the `Workflow` space, then
`POST /api/admin/sync {"source":"confluence","department":"workflow"}` to populate the
`zalopay_workflow` index — deferred to the Phase 5 demo step (workflow page content is the known
blocker).
