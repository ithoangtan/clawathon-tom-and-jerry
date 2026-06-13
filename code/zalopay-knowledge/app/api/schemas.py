from __future__ import annotations

"""API request/response schemas — the FE↔BE wire contract.

These models are the single source of truth for the JSON shapes exchanged
between the React frontend and the FastAPI backend.  The TypeScript mirror is
at ``frontend/src/lib/types.ts``.  The authoritative endpoint documentation
is at ``docs/API-CONTRACT.md``.

IMPORTANT: field names use ``snake_case`` to match the JSON wire format
exactly (the frontend does NOT camelCase-transform them).  Any change to a
field name, type, or optionality here MUST be mirrored in types.ts and
API-CONTRACT.md before parallel frontend/backend work can proceed.
"""

from typing import Annotated, Literal, Optional

from pydantic import AfterValidator, ConfigDict, Field
from pydantic import BaseModel as _Base

from app.common.departments import ROLES, get_department


# ── Primitive literals (used in both request and response shapes) ─────────────

def _validate_department_key(value: str) -> str:
    try:
        get_department(value)
    except KeyError as exc:
        raise ValueError(str(exc)) from exc
    return value


def _validate_role(value: str) -> str:
    if value not in ROLES:
        raise ValueError(f"Unknown role {value!r}. Valid roles: {', '.join(ROLES)}")
    return value


Department = Annotated[str, AfterValidator(_validate_department_key)]
Role = Annotated[str, AfterValidator(_validate_role)]
AnswerStatus = Literal["answered", "refused", "partial"]
RefusalReason = Literal["out_of_scope"]
Lang = Literal["en", "vi"]


# ── Shared leaf models ────────────────────────────────────────────────────────

class CitationModel(_Base):
    """A single document citation attached to an answer."""

    model_config = ConfigDict(extra="forbid")

    title: str
    url: str
    section: Optional[str] = None
    last_modified: Optional[str] = None
    lifecycle_state: Optional[str] = None
    deprecated: bool = False
    successor_url: Optional[str] = None
    source_type: Optional[str] = None
    page: Optional[int] = None
    excerpt: Optional[str] = None
    """Chunk text snippet (~400 chars) for the Citation Evidence Inspector."""
    chunk_id: Optional[str] = None
    """Stable chunk id when sourced from retrieval."""
    doc_type: Optional[str] = None
    """Document type (PRD, Risk, Operation, …) for filtering and disclaimer heuristics."""


class ConflictSide(_Base):
    """One side of a factual conflict between two department sources."""

    model_config = ConfigDict(extra="forbid")

    department: Department
    statement: str
    citation: CitationModel


class ConflictModel(_Base):
    """A detected factual conflict surfaced by the reconcile node."""

    model_config = ConfigDict(extra="forbid")

    topic: Optional[str] = None
    sides: list[ConflictSide] = Field(default_factory=list)


class ClarifyingQuestion(_Base):
    """A clarifying question emitted when routing confidence is too low."""

    model_config = ConfigDict(extra="forbid")

    prompt: str
    """The question text to show the user."""

    options: list[Department] = Field(default_factory=list)
    """Quick-reply department options (the user taps one to pin that dept)."""


# ── Request models ────────────────────────────────────────────────────────────

class ChatRequest(_Base):
    """Body of ``POST /chat``."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=4000)
    """The user's natural-language question."""

    target_departments: Optional[list[Department]] = None
    """Optional explicit department pins set by the UI DepartmentTargetBar.
    When provided, the router skips confidence gating for these departments."""


class FeedbackRequest(_Base):
    """Body of ``POST /feedback``."""

    model_config = ConfigDict(extra="forbid")

    feedback_id: str = Field(..., min_length=1)
    """UUID from the ``ChatResponse.feedback_id`` field."""

    rating: Literal["up", "down"]

    comment: Optional[str] = Field(default=None, max_length=2000)


# ── Response models ───────────────────────────────────────────────────────────

class ChatResponse(_Base):
    """Body of a successful ``POST /chat`` response."""

    # Allow extra keys for forward-compatibility (callers should ignore unknowns)
    model_config = ConfigDict(extra="allow")

    answer: str
    """Markdown-formatted answer text with inline ``[n]`` citation markers."""

    citations: list[CitationModel] = Field(default_factory=list)
    """Ordered list of citations corresponding to ``[1]``…``[n]`` markers."""

    source_departments: list[Department] = Field(default_factory=list)
    """Departments that contributed to this answer."""

    confidence: float = Field(..., ge=0.0, le=1.0)
    """Aggregate confidence score 0–1."""

    feedback_id: str
    """Opaque UUID to use when submitting feedback via ``POST /feedback``."""

    status: AnswerStatus
    """Overall answer status."""

    conflicts: Optional[list[ConflictModel]] = None
    """Non-empty when the reconcile node detected genuine factual conflicts."""

    clarifying_question: Optional[ClarifyingQuestion] = None
    """Non-null when the router emits a clarifying question instead of answering."""

    lang: Optional[Lang] = None
    """Language of the response (``"en"`` or ``"vi"``)."""

    refusal_reason: Optional[RefusalReason] = None
    """Set when ``status`` is ``refused`` for a reason other than missing docs (e.g. access denied)."""

    refusals: Optional[list[Department]] = None
    """Departments that were queried but returned no usable answer (partial tier)."""


class SyncStartResponse(_Base):
    """Body returned by ``POST /sync/confluence`` and ``POST /sync/gdrive``."""

    model_config = ConfigDict(extra="forbid")

    source: str
    """Which source was triggered: ``"confluence"`` or ``"gdrive"``."""

    started: bool
    """True if a new sync job was started; False if one was already running (409)."""

    message: str
    """Human-readable status message."""


class SourceStatus(_Base):
    """Per-source sync status entry in ``SyncStatusResponse``."""

    model_config = ConfigDict(extra="allow")

    source: str
    """Source identifier: ``"confluence"`` or ``"gdrive"``."""

    state: Literal["running", "idle", "error"]

    doc_count: int = 0
    chunk_count: int = 0

    last_success_at: Optional[str] = None
    """ISO-8601 timestamp of the last successful sync completion."""

    freshness_hours: Optional[float] = None
    """Hours since the last successful sync; None if never synced."""

    errors: list[str] = Field(default_factory=list)
    """Recent error messages (last N, capped by the orchestrator)."""

    progress: Optional[dict] = None
    """Optional running-sync progress payload (page counts, current space, etc.)."""


class SyncStatusResponse(_Base):
    """Body of ``GET /sync/status``."""

    model_config = ConfigDict(extra="allow")

    sources: list[SourceStatus] = Field(default_factory=list)


class AdminSyncRequest(_Base):
    """Body of ``POST /api/admin/sync``."""

    model_config = ConfigDict(extra="forbid")

    source: Literal["confluence", "gdrive"]
    department: Optional[Department] = None
    """When set with ``source=confluence``, sync only this department's space."""


class AdminSyncStartResponse(_Base):
    """Body returned by ``POST /api/admin/sync``."""

    model_config = ConfigDict(extra="forbid")

    source: str
    department: Optional[Department] = None
    started: bool
    job_id: Optional[str] = None
    message: str


class SyncedContentItem(_Base):
    """One synced document in admin status/history payloads."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str
    url: Optional[str] = None


class AdminDepartmentSyncStatus(_Base):
    """Per-department sync result within an admin job."""

    model_config = ConfigDict(extra="forbid")

    department: Department
    space_key: Optional[str] = None
    status: Literal["pending", "running", "success", "failed"]
    page_count: int = 0
    chunk_count: int = 0
    synced_items: list[SyncedContentItem] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class AdminJobStatus(_Base):
    """Sync job status for one source (confluence or gdrive)."""

    model_config = ConfigDict(extra="allow")

    job_id: Optional[str] = None
    status: Literal["pending", "running", "success", "failed"]
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    last_success_at: Optional[str] = None
    target_department: Optional[Department] = None
    doc_count: int = 0
    chunk_count: int = 0
    errors: list[str] = Field(default_factory=list)
    progress: Optional[dict] = None
    departments: list[AdminDepartmentSyncStatus] = Field(default_factory=list)


class AdminDepartmentIndexStatus(_Base):
    """Indexed corpus snapshot for one department."""

    model_config = ConfigDict(extra="forbid")

    chunk_count: int = 0
    doc_count: int = 0
    has_data: bool = False


class AdminSyncStatusResponse(_Base):
    """Body of ``GET /api/admin/sync/status``."""

    model_config = ConfigDict(extra="allow")

    jobs: dict[str, AdminJobStatus] = Field(default_factory=dict)
    departments_indexed: dict[Department, AdminDepartmentIndexStatus] = Field(
        default_factory=dict
    )


class AdminSyncHistoryEntry(_Base):
    """One row in ``GET /api/admin/sync/history``."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    source: str
    status: Literal["pending", "running", "success", "failed"]
    started_at: str
    finished_at: Optional[str] = None
    department: Optional[Department] = None
    doc_count: int = 0
    chunk_count: int = 0
    errors: list[str] = Field(default_factory=list)
    departments: list[AdminDepartmentSyncStatus] = Field(default_factory=list)


class AdminSyncHistoryResponse(_Base):
    """Body of ``GET /api/admin/sync/history``."""

    model_config = ConfigDict(extra="forbid")

    entries: list[AdminSyncHistoryEntry] = Field(default_factory=list)


class HistoryItem(_Base):
    """One row in the query history table on the Dashboard."""

    model_config = ConfigDict(extra="allow")

    ts: str
    """ISO-8601 timestamp of the query."""

    question: str
    departments: list[Department] = Field(default_factory=list)
    status: AnswerStatus
    confidence: float = Field(..., ge=0.0, le=1.0)
    latency_ms: int


class DashboardData(_Base):
    """Body of ``GET /api/dashboard``."""

    model_config = ConfigDict(extra="allow")

    query_count: int = 0
    deflection_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    """North-star: share of queries answered (full or partial) without doc refusal."""
    answered_wrong_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    """Guardrail: thumbs-down / total feedback (0 when no feedback yet)."""
    refusal_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    partial_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    conflict_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    feedback_up: int = 0
    feedback_down: int = 0
    total_tokens: int = 0
    history: list[HistoryItem] = Field(default_factory=list)
    eval_golden_total: int = 0
    eval_faithfulness: float = Field(default=0.0, ge=0.0, le=1.0)
    eval_answer_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    eval_refusal_precision: float = Field(default=0.0, ge=0.0, le=1.0)
    eval_refusal_recall: float = Field(default=0.0, ge=0.0, le=1.0)
    eval_context_recall_at_5: float = Field(default=0.0, ge=0.0, le=1.0)
    eval_context_precision_at_5: float = Field(default=0.0, ge=0.0, le=1.0)
    eval_last_run_at: Optional[str] = None
    eval_mode: Optional[str] = None


class HealthInfo(_Base):
    """Body of ``GET /health`` and related probe endpoints."""

    model_config = ConfigDict(extra="allow")

    status: Literal["healthy"] = "healthy"
    version: Optional[str] = None
    index_ready: bool = False
    maas_ready: bool = False
    """True when MaaS responds to a lightweight models-list ping."""
    ready: bool = False
    """True when both ``index_ready`` and ``maas_ready`` (readiness gate)."""
    config: Optional[dict] = None
    """Non-sensitive config snapshot (model names, thresholds) for the Settings ConfigPanel."""
