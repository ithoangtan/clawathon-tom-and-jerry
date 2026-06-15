# Phase 3 — Workflow Parser (LLM-based): page text → structured steps

## Goal

Turn the full text of a workflow Confluence page into a typed `WorkflowDefinition` object the
executor can iterate. Use **LLM-based extraction** (not a deterministic markdown parser).

## Background (verified in repo)

- Prompts: versioned YAML in `app/prompts/`, loaded via `load_prompt("name")`
  (`app/prompts/__init__.py`); each declares `required_inputs`, `system`, `user`;
  `prompt.render(**kwargs)` → `{"system", "user"}`. See `app/prompts/router.v1.yaml`.
- LLM: `LLMPort.complete(*, tier, messages, temperature=0.0, response_format="json"|"text", ...)`
  (`app/ports/llm.py`). Use `ModelTier.SMALL` with `response_format="json"`. JSON parsing helper
  exists — reuse `parse_json_response` (used in `app/graph/nodes/router.py`).
- Pydantic is already used for schemas (`app/api/schemas.py`).
- The page template the parser targets is defined in
  `use-case/SOLUTION-workflow-platform.md` (Tầng 1): metadata header table, `## Lifecycle`
  table, and H2 = step with Responsible / Type / Input / Action / Output / checklist / Policy ref.

## What to build

### 1. Models (`app/workflow/models.py`)

```python
class LifecycleState(BaseModel):
    status: str            # e.g. SUBMITTED
    meaning: str
    next: list[str]        # allowed transitions; [] = terminal

class WorkflowStep(BaseModel):
    index: int
    title: str
    responsible_role: str | None      # "Risk Reviewer"
    responsible_department: str | None # "Risk"
    type: Literal["fetch","rag","checklist","synthesize","action","gate"]
    input: str | None
    action: str | None
    output: str | None
    checklist: list[str] = []
    policy_ref: str | None            # link/text of SOP source
    condition: str | None             # for gate steps

class WorkflowDefinition(BaseModel):
    name: str
    trigger: str | None
    owner: str | None
    participants: list[str] = []
    definition_status: Literal["DRAFT","IN_REVIEW","ACTIVE","DEPRECATED","ARCHIVED"]
    jira_source: Literal["existing-ticket","auto-create"] | None
    version: str | None
    lifecycle: list[LifecycleState] = []
    executable_statuses: list[str] = []  # instance statuses the agent may act on
    steps: list[WorkflowStep]
```

### 2. Prompt (`app/prompts/workflow_parse.v1.yaml`)

- `required_inputs`: `page_text`.
- `system`: instruct the model to extract the metadata header, the `## Lifecycle` table, and
  the ordered steps into a strict JSON object matching `WorkflowDefinition`. Rules:
  - `definition_status` and `jira_source` come from the metadata header table; normalise
    `definition_status` to the 5 canonical values (map legacy `IN DEV`→`DRAFT`, `IN PROCESS`→`ACTIVE`).
  - Each H2 heading is one step, in document order, `index` starting at 1.
  - Infer `type` from the step's stated `Type:` field; if absent, infer from the action wording.
  - Preserve checklist items verbatim; capture `policy_ref` text/link if present.
  - For `gate` steps capture the branching `condition`.
  - Return **only** JSON. If a field is unknown, use null / empty list — never invent.
- `user`: `{page_text}`.

### 3. Parser (`app/workflow/parser.py`)

```python
def parse_workflow(page_text: str, *, llm: LLMPort, settings=None) -> WorkflowDefinition: ...
```
- Render the prompt, call `llm.complete(tier=SMALL, response_format="json")`, parse with
  `parse_json_response`, validate into `WorkflowDefinition`.
- On LLM/validation failure raise a typed `WorkflowParseError` (the executor will turn this into
  a graceful refusal).
- Provide a tiny helper `is_executable(defn) -> tuple[bool, str|None]`: returns
  `(True, None)` for `ACTIVE`; `(False, warning)` for `DEPRECATED`; `(False, reason)` otherwise.
  (The executor enforces the gate; keep the rule here so it's centralised and testable.)

## Acceptance criteria

- Given the sample page text (use the template/examples in the SOLUTION doc, or create a
  fixture page), `parse_workflow` returns a `WorkflowDefinition` with correct `name`,
  `definition_status`, `jira_source`, ordered steps with the right `type`, checklist items,
  and policy refs.
- `is_executable` returns the correct gate decision for each `definition_status`.
- Malformed LLM output → `WorkflowParseError`, not a crash.

## Tests

- `tests/unit/test_workflow_parser.py`: mock `LLMPort.complete` to return canned JSON for a
  fixture page; assert the parsed `WorkflowDefinition` fields. Add cases for the status gate
  (`ACTIVE`/`DEPRECATED`/`DRAFT`) and for malformed JSON → `WorkflowParseError`.

## Verify

`python -m ruff check .` and `make test-unit`.

---

## Copy-paste Agent Prompt

> You are working in `code/zalopay-knowledge/`. Implement **Phase 3**: an LLM-based workflow
> parser that converts a workflow Confluence page's full text into a typed object.
>
> 1. Read `use-case/SOLUTION-workflow-platform.md` (Tầng 1 = the page template the parser must
>    understand, and the definition-lifecycle section). Read `app/prompts/__init__.py` +
>    `app/prompts/router.v1.yaml` (prompt format/loader), `app/ports/llm.py` (LLMPort,
>    ModelTier), and `app/graph/nodes/router.py` (how `parse_json_response` + JSON LLM calls
>    are used). Note Pydantic usage in `app/api/schemas.py`.
> 2. Create `app/workflow/models.py` with Pydantic models `LifecycleState`, `WorkflowStep`,
>    `WorkflowDefinition` (fields per the SOLUTION template: name, trigger, owner, participants,
>    definition_status ∈ DRAFT/IN_REVIEW/ACTIVE/DEPRECATED/ARCHIVED, jira_source ∈
>    existing-ticket/auto-create, version, lifecycle table, ordered steps with
>    type ∈ fetch/rag/checklist/synthesize/action/gate, responsible role+department, input,
>    action, output, checklist[], policy_ref, condition).
> 3. Create `app/prompts/workflow_parse.v1.yaml` (required_inputs: page_text) instructing the
>    model to emit strict JSON matching `WorkflowDefinition`: normalise `definition_status`
>    (map legacy `IN DEV`→DRAFT, `IN PROCESS`→ACTIVE), one step per H2 in order, infer `type`,
>    preserve checklist + policy_ref verbatim, capture gate `condition`, return JSON only, use
>    null/empty for unknowns (never invent).
> 4. Create `app/workflow/parser.py`: `parse_workflow(page_text, *, llm, settings=None) ->
>    WorkflowDefinition` (render prompt → `llm.complete(tier=SMALL, response_format="json")` →
>    `parse_json_response` → validate). Raise `WorkflowParseError` on failure. Add
>    `is_executable(defn) -> (bool, str|None)` centralising the ACTIVE-only gate
>    (DEPRECATED → False + warning; others → False + reason).
> 5. Add `tests/unit/test_workflow_parser.py` mocking `LLMPort.complete` with canned JSON for a
>    fixture page; assert parsed fields, the status gate decisions, and malformed-JSON →
>    `WorkflowParseError`.
>
> Run `python -m ruff check .` and `make test-unit`. Report changes + test output.
