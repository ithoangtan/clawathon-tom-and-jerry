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

from typing import Literal, Optional

from pydantic import ConfigDict, Field
from pydantic import BaseModel as _Base


# ── Primitive literals (used in both request and response shapes) ─────────────

Department = Literal["risk", "grow_enablement", "bank_partnerships"]
Role = Literal["engineer", "pm", "ops", "risk", "business"]
AnswerStatus = Literal["answered", "refused", "partial"]
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
    """Body of ``GET /dashboard``."""

    model_config = ConfigDict(extra="allow")

    query_count: int = 0
    refusal_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    partial_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    conflict_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    feedback_up: int = 0
    feedback_down: int = 0
    total_tokens: int = 0
    history: list[HistoryItem] = Field(default_factory=list)


class HealthInfo(_Base):
    """Body of ``GET /health``."""

    model_config = ConfigDict(extra="allow")

    status: Literal["healthy"] = "healthy"
    version: Optional[str] = None
    index_ready: bool = False
    config: Optional[dict] = None
    """Non-sensitive config snapshot (model names, thresholds) for the Settings ConfigPanel."""
