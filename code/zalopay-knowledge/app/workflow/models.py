from __future__ import annotations

"""Typed schema for a parsed workflow definition.

These models mirror the Confluence page template in
``use-case/SOLUTION-workflow-platform.md`` (Tầng 1):

- a **metadata header** table (trigger / owner / participants / definition status /
  Jira source / version),
- an optional ``## Lifecycle`` table (per-instance status machine the workflow
  defines for itself — never hardcoded in this code), and
- an ordered list of **steps**, one per H2 heading.

The parser (:mod:`app.workflow.parser`) validates raw LLM JSON into a
:class:`WorkflowDefinition`; the executor iterates ``steps`` and dispatches by
``WorkflowStep.type``.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# The five canonical definition-lifecycle states of a workflow *page* (the SOP
# template itself) — distinct from the per-instance ``lifecycle`` table below.
DefinitionStatus = Literal["DRAFT", "IN_REVIEW", "ACTIVE", "DEPRECATED", "ARCHIVED"]

# Step dispatch types the executor knows how to run.
StepType = Literal["fetch", "rag", "checklist", "synthesize", "action", "gate"]

# Where the Jira parent comes from — supplied by the user, or created by the agent.
JiraSource = Literal["existing-ticket", "auto-create"]


class LifecycleState(BaseModel):
    """One row of the workflow's per-instance ``## Lifecycle`` table.

    Each workflow defines its own instance state machine on the Confluence page;
    the agent reads it rather than assuming any fixed set of statuses.
    """

    status: str
    """Instance status name, e.g. ``SUBMITTED`` / ``UNDER REVIEW``."""

    meaning: str = ""
    """Human description of what the status means."""

    next: list[str] = Field(default_factory=list)
    """Allowed transitions; an empty list marks a terminal state."""


class WorkflowStep(BaseModel):
    """A single executable step (one H2 heading on the workflow page)."""

    index: int
    """1-based position in document order."""

    title: str
    """Step heading text, e.g. ``Fetch Jira ticket + campaign page``."""

    responsible_role: str | None = None
    """Role that owns the step, e.g. ``Risk Reviewer`` (from ``Responsible:``)."""

    responsible_department: str | None = None
    """Department the role belongs to, e.g. ``Risk`` — drives RAG domain + Jira assignee."""

    type: StepType = "synthesize"
    """Dispatch type; inferred from the step's ``Type:`` field (or its action wording)."""

    input: str | None = None
    """What data/information the step needs (``Input:``)."""

    action: str | None = None
    """What the step does (``Action:``) — used as the RAG/synthesis instruction."""

    output: str | None = None
    """The step's deliverable (``Output:``)."""

    checklist: list[str] = Field(default_factory=list)
    """Verbatim checklist items to evaluate/render."""

    policy_ref: str | None = None
    """Link or text of the source SOP/policy (``> Policy ref:``)."""

    condition: str | None = None
    """Branch condition for ``gate`` steps (e.g. ``quà > 1 triệu → escalate``)."""


class WorkflowTrigger(BaseModel):
    """One row of the workflow page's ``## Triggers`` table — an event→action rule.

    The agent reacts to inbound Jira events (status/comment/field change) by
    matching them against these rules (``app.workflow.triggers.match_trigger``)
    and running the ``action`` instruction.
    """

    event_type: Literal["status_changed", "comment_added", "field_changed"]

    from_status: str | None = None
    """For ``status_changed``: required source status, or ``*``/None = any."""

    to_status: str | None = None
    """For ``status_changed``: required target status (None = any)."""

    field: str | None = None
    """For ``field_changed``: the field name that must have changed."""

    field_to: str | None = None
    """For ``field_changed``: required new value (None = any)."""

    comment_contains: str | None = None
    """For ``comment_added``: substring the comment must contain (None = any)."""

    action: str
    """Free-text instruction describing what to do when this trigger fires
    (e.g. "Post tổng kết review lên Confluence", "Chạy step 2-3")."""


class WorkflowReaction(BaseModel):
    """One row of the workflow page's ``## Reactions`` table — decision→side-effects.

    After the agent runs a trigger's action and the LLM emits a ``DECISION:``
    token, the generic reaction dispatcher (``app.workflow.reactions``) looks up
    the matching row and applies its ``verbs``. Verbs and their arguments are
    **data on the Confluence page**, so a new workflow declares its own reactions
    with no code change — code only supplies the capability primitives.
    """

    decision: str
    """The decision token this row reacts to, e.g. ``PASS`` / ``PARTIAL_FAIL`` / ``FAIL``."""

    verbs: list[str] = Field(default_factory=list)
    """Side-effect verbs, e.g. ``["comment", "reassign:reporter", "label:risk-rejected"]``.

    Supported by the dispatcher: ``comment``, ``reassign:<reporter|accountId>``,
    ``label:<name>``, ``append_confluence``. Unknown verbs are logged and skipped.
    """


class WorkflowDefinition(BaseModel):
    """The full parsed workflow page."""

    name: str
    """Workflow name (the page H1), e.g. ``Risk: Campaign Review — Lucky Wheel``."""

    trigger: str | None = None
    owner: str | None = None
    participants: list[str] = Field(default_factory=list)

    definition_status: DefinitionStatus = "DRAFT"
    """Lifecycle state of the SOP template itself; only ``ACTIVE`` is executable."""

    jira_source: JiraSource | None = None
    version: str | None = None

    lifecycle: list[LifecycleState] = Field(default_factory=list)
    """The workflow's own per-instance status machine (read, never hardcoded)."""

    executable_statuses: list[str] = Field(default_factory=list)
    """Instance statuses the agent may act on (from ``Executable statuses:``)."""

    steps: list[WorkflowStep] = Field(default_factory=list)
    """Ordered steps the executor runs."""

    triggers: list[WorkflowTrigger] = Field(default_factory=list)
    """Event→action rules from the ``## Triggers`` table (Jira webhook reactions)."""

    reactions: list[WorkflowReaction] = Field(default_factory=list)
    """Decision→side-effect rules from the ``## Reactions`` table (applied after an action)."""

    # ── Normalisation ─────────────────────────────────────────────────────────

    @field_validator("definition_status", mode="before")
    @classmethod
    def _normalise_status(cls, value: object) -> object:
        """Map legacy/loose status spellings onto the 5 canonical values.

        The parser prompt already normalises, but we re-apply here so the model
        is robust to ``IN DEV`` / ``in process`` / ``in-review`` style inputs and
        so the rule lives in exactly one place.
        """
        if not isinstance(value, str):
            return value
        token = value.strip().upper().replace("-", " ")
        legacy = {
            "IN DEV": "DRAFT",
            "DEVELOPMENT": "DRAFT",
            "IN PROCESS": "ACTIVE",
            "IN PROGRESS": "ACTIVE",
            "LIVE": "ACTIVE",
            "IN REVIEW": "IN_REVIEW",
            "REVIEW": "IN_REVIEW",
        }
        if token in legacy:
            return legacy[token]
        # Canonical values use an underscore (IN_REVIEW); collapse spaces back.
        return token.replace(" ", "_")
