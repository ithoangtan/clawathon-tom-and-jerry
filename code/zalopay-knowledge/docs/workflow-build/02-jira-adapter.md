# Phase 2 — Jira adapter: `JiraPort` + `JiraClient`

> **⚠️ UPDATED 2026-06-15 — minimize env vars / reuse Confluence creds.** Jira is the **same
> Atlassian instance + account** as Confluence (`ithoangtan-clawathon.atlassian.net`,
> `ithoangtan@gmail.com`). So **do NOT add `JIRA_*` env vars.** Instead:
> - Jira base URL = `settings.confluence_base_url` with a trailing `/wiki` stripped
>   (`https://ithoangtan-clawathon.atlassian.net`).
> - Auth = reuse `settings.confluence_email` + the Confluence API token (same resolution path
>   as Confluence, incl. `confluence_api_key_provider` on AgentBase).
> - Default project key = hardcode `"KAN"` (a module constant, not an env var).
> - Keep `jira_dry_run` as a simple bool (can be a hardcoded module constant defaulting False,
>   or a single optional setting — your call, but don't add the full `jira_*` block).
>
> The original env-var-heavy design below is superseded — follow this note where they conflict.

## Goal

Add the ability to perform Jira actions: read an issue, create an issue/sub-task, and post a
comment. This is brand-new (no Jira code exists today). Mirror the existing Confluence client
patterns so it fits the codebase.

## Background (verified in repo)

- **No Jira code exists.** Only a refused-query example in `tests/golden/golden_set.yaml`.
- `httpx` is already the HTTP library: `app/ingestion/confluence.py` uses `httpx.Client` with
  Basic auth (`ConfluenceClient._auth()`), timeouts, error handling, logging. **Copy this shape.**
- Credentials resolve via `fetch_api_key_for_agent(settings, provider_name)` in
  `app/adapters/identity_client.py` — works for local env vars and AgentBase Identity.
- Config is Pydantic `Settings` in `app/config.py`; secrets default to `""`.
- Ports live in `app/ports/`, adapters in `app/adapters/`, wired in `app/adapters/deps.py`.

## What to build

### 1. Config (`app/config.py` + `.env.example`)

Add a `# ── Jira ──` section:
```python
jira_base_url: str = Field(default="", description="Jira Cloud base URL, e.g. https://zalopay.atlassian.net")
jira_email: str = Field(default="", description="Email for Jira Basic auth")
jira_api_token: str = Field(default="", description="Jira API token (local dev)")
jira_api_key_provider: str = Field(default="identity-jira-zalopay", description="AgentBase Identity provider for the Jira token")
jira_default_project: str = Field(default="", description="Default Jira project key for auto-create workflows")
jira_dry_run: bool = Field(default=False, description="If true, Jira write actions are drafted/logged, not posted")
```
Mirror all of these (blank) into `.env.example` with comments.

### 2. Port (`app/ports/jira.py`)

```python
@runtime_checkable
class JiraPort(Protocol):
    def get_issue(self, key: str) -> dict: ...
    def create_issue(self, *, project: str, summary: str, description: str,
                     issuetype: str = "Task", parent: str | None = None,
                     assignee: str | None = None) -> dict: ...
    def add_comment(self, *, key: str, body: str) -> dict: ...
    def is_ready(self) -> bool: ...
```
Return dicts include at least the created/fetched issue `key` and `url`.

### 3. Adapter (`app/adapters/jira_client.py`)

- `JiraClient` using `httpx.Client`, Basic auth (`jira_email` + token), base `jira_base_url`.
- Resolve the token: prefer `settings.jira_api_token`; if empty, call
  `fetch_api_key_for_agent(settings, settings.jira_api_key_provider)`.
- Jira Cloud REST v3 endpoints:
  - `GET /rest/api/3/issue/{key}` → `get_issue`
  - `POST /rest/api/3/issue` (fields: project.key, summary, description, issuetype.name,
    `parent.key` for sub-tasks, `assignee.accountId`/`emailAddress` when given) → `create_issue`
  - `POST /rest/api/3/issue/{key}/comment` → `add_comment`
  - Description/comment body: accept plain text; wrap into Atlassian Document Format (ADF)
    with a small helper `_to_adf(text)` (a single paragraph is enough for the demo).
- **`jira_dry_run`**: when true, `create_issue`/`add_comment` must NOT call the API — instead
  log and return a synthetic dict (`{"key": "DRY-RUN", "url": "", "dry_run": True, ...}`) so the
  executor can still produce a coherent answer in a demo without write access.
- `is_ready()`: cheap reachability/credentials check (e.g. `/rest/api/3/myself`), tolerant of
  being unconfigured (return False, never raise).
- Graceful failure: raise a typed `JiraUnavailable` (define alongside the port or in the
  adapter) on transport/auth errors, mirroring how the retriever raises `RetrieverUnavailable`.

### 4. Wiring (`app/adapters/deps.py`)

- Construct a `JiraClient` (or a no-op stub when `jira_base_url` is empty) and expose it on the
  deps object as `.jira`, so graph nodes can receive it like `deps.jira`.

## Acceptance criteria

- With Jira configured, `create_issue` / `add_comment` / `get_issue` hit the right endpoints
  and return `{key, url, ...}`.
- With `jira_dry_run=True`, no network write happens; methods return a synthetic dry-run dict.
- With Jira unconfigured, the app still starts; `is_ready()` returns False and nodes can detect
  this without crashing.

## Tests

- `tests/unit/` mocking `httpx` (or the client transport): assert request URL/method/payload
  for each method; assert ADF wrapping; assert dry-run short-circuits the network.
- `tests/contract/` (optional): a graceful-degradation check that an unconfigured Jira yields
  `is_ready() == False` and a controlled error, not a 500.

## Verify

`python -m ruff check .` and `make test-unit`.

---

## Copy-paste Agent Prompt

> You are working in `code/zalopay-knowledge/`. Implement **Phase 2**: a Jira integration.
> There is no Jira code today; model it on the existing Confluence client.
>
> 1. Read `app/ingestion/confluence.py` (httpx + Basic auth pattern), `app/adapters/identity_client.py`
>    (`fetch_api_key_for_agent`), `app/config.py` (Settings conventions), `app/ports/retriever.py`
>    + `app/adapters/opensearch_retriever.py` (port/adapter + typed-unavailable-error pattern),
>    and `app/adapters/deps.py` (wiring).
> 2. Add Jira config fields to `app/config.py` and `.env.example`: `jira_base_url`, `jira_email`,
>    `jira_api_token`, `jira_api_key_provider` (default `"identity-jira-zalopay"`),
>    `jira_default_project`, `jira_dry_run` (bool, default False). Secrets default to `""`.
> 3. Create `app/ports/jira.py` with a `JiraPort` Protocol: `get_issue(key)`,
>    `create_issue(*, project, summary, description, issuetype="Task", parent=None, assignee=None)`,
>    `add_comment(*, key, body)`, `is_ready()`. Define a `JiraUnavailable` exception.
> 4. Create `app/adapters/jira_client.py` with `JiraClient` (httpx.Client, Basic auth, token from
>    `settings.jira_api_token` or `fetch_api_key_for_agent`). Use Jira Cloud REST v3 endpoints; wrap
>    text into ADF with a small `_to_adf` helper. Honour `jira_dry_run` (no network writes; return a
>    synthetic dry-run dict). `is_ready()` must be tolerant when unconfigured (return False, no raise).
> 5. Wire a `JiraClient` (or no-op stub when `jira_base_url` is empty) onto the deps object in
>    `app/adapters/deps.py` as `.jira`.
> 6. Add unit tests under `tests/unit/` mocking httpx: assert endpoints/payloads, ADF wrapping, and
>    dry-run short-circuit. Optionally a contract test for graceful unconfigured behaviour.
>
> Run `python -m ruff check .` and `make test-unit`. Report changes + test output.

---

## Result (2026-06-15) — ✅ DONE (code) + live-verified

**Implemented (no new env vars — reuses Confluence Atlassian creds):**
- `app/ports/jira.py` — `JiraPort` Protocol: `get_issue`, `create_issue`
  (`project` defaults to client's, `parent` → sub-task, optional `assignee`), `add_comment`,
  `is_ready`.
- `app/adapters/jira_client.py` — `JiraClient` (httpx, Jira Cloud REST v3). Base URL derived
  from `settings.confluence_base_url` (strips trailing `/wiki`); auth via
  `settings.confluence_email` + `resolve_confluence_api_token(settings)` (same path as
  Confluence, incl. AgentBase identity). `DEFAULT_PROJECT_KEY = "KAN"` hardcoded module
  constant. `_to_adf()` wraps plain text → Atlassian Document Format. `dry_run` ctor flag
  short-circuits writes (returns synthetic `{"key":"DRY-RUN","dry_run":True,...}`). Plus
  `NullJiraClient` (raises `JiraUnavailable` on actions, `is_ready()=False`).
- `app/ports/errors.py` — new `JiraUnavailable`.
- `app/graph/build.py` — `GraphDeps.jira: Optional[JiraPort]`.
- `app/adapters/deps.py` — wires `JiraClient` when configured, else `NullJiraClient`.

**Tests:** `tests/unit/adapters/test_jira_client.py` (19): `_to_adf`, base-URL derivation,
configured(), get_issue/create_issue/sub-task/add_comment request shaping (asserts endpoints +
payload incl. default project `KAN` + ADF), dry-run (no network), HTTP-error → `JiraUnavailable`,
unconfigured → raise, is_ready true/false, NullJiraClient.

**Live verification (read-only, against the real instance):**
`JiraClient(get_settings())` → `configured=True`, `base=https://ithoangtan-clawathon.atlassian.net`,
`is_ready()=True`, `get_issue("KAN-1")` → summary *"[MS] Example ticket"*, status *To Do*. ✅
Confirms the reused Confluence credentials authenticate against Jira.

**Verification:** full unit suite `7 failed, 454 passed, 124 errors` vs Phase-1
`7 failed, 435 passed, 124 errors` → **+19 passing, zero regressions**. `ruff --select F` on
Phase 2 code: clean (pre-existing F401s in `deps.py`/`build.py` left untouched).

**Demo note:** deps wires `JiraClient` with `dry_run=False` (real writes) — fine for the live
demo. To rehearse without posting, construct with `dry_run=True`. Real writes (create
sub-task / comment) are first exercised in Phase 5; the smoke test above only reads.
