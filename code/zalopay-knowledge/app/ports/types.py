from __future__ import annotations

"""Shared data types referenced by the port Protocols.

These are the canonical transfer objects that flow between graph nodes and
adapters.  Never put business logic here — only structure definitions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


# ── LLM types ────────────────────────────────────────────────────────────────

class ModelTier(str, Enum):
    """LLM tier selection.

    SMALL is used for low-latency tasks: routing, grading, verification.
    MAIN is used for quality-critical generation: synthesis, reconcile.
    """

    SMALL = "small"
    MAIN = "main"


@dataclass
class LLMResult:
    """Result returned by :class:`app.ports.llm.LLMPort.complete`."""

    text: str
    """Raw text content of the first choice."""

    raw: dict
    """Full API response as a dict (for debugging / audit logging)."""

    usage: dict
    """Token usage: typically {'prompt_tokens': N, 'completion_tokens': M, 'total_tokens': T}."""

    degraded: bool = False
    """True when a retry or fallback was invoked — surfaced in the cost dashboard."""

    model_used: str = ""
    """Actual model ID that produced this result (may differ from the configured primary when a fallback was used)."""


# ── Retriever types ───────────────────────────────────────────────────────────

LifecycleState = Literal["active", "deprecated", "sunset"]
SourceType = Literal["confluence", "pdf"]


@dataclass
class RetrievedChunk:
    """A single chunk returned by :class:`app.ports.retriever.RetrieverPort.search`.

    Field naming matches :class:`app.api.schemas.CitationModel` so the API
    layer can construct a citation with a shallow copy of these fields.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    chunk_id: str
    """Stable unique id for this chunk (used as FAISS vector id key)."""

    department: str
    """Department key this chunk belongs to (see ``app.common.departments`` registry)."""

    # ── Document metadata ─────────────────────────────────────────────────────
    doc_type: str
    """Classified document type (e.g. ``policy``, ``runbook``, ``faq``, ``guide``)."""

    title: str
    """Document title as it appears in Confluence or the PDF filename."""

    url: str
    """Canonical URL or Drive file URL for this document."""

    section: str | None
    """Section heading path, e.g. ``Introduction > Prerequisites``."""

    last_modified: str | None
    """ISO-8601 datetime string when the source document was last modified."""

    lifecycle_state: LifecycleState
    """Lifecycle state.  ``sunset`` chunks are excluded at retrieval time.
    ``deprecated`` chunks are returned but must be annotated with a staleness warning."""

    source_type: SourceType
    """Origin of this chunk — ``confluence`` or ``pdf``."""

    page: int | None
    """PDF page number (1-indexed); None for Confluence chunks."""

    # ── Content ───────────────────────────────────────────────────────────────
    text: str
    """The chunk text that will be injected into prompts."""

    score: float
    """Cosine similarity score in [0, 1] (higher = more relevant)."""

    source: str | None = None
    """Upstream document id (Confluence page id, Drive file id, etc.)."""

    anchor: str | None = None
    """Deep-link anchor slug for the chunk section, when available."""

    space: str | None = None
    """Confluence space key; ``None`` for PDF/SharePoint sources."""

    labels: str | None = None
    """JSON-encoded list of source labels (Confluence labels, file tags)."""

    author: str | None = None
    """Last-known author or owner display name from the source system."""

    acl: str | None = None
    """JSON-encoded ACL group list; MVP default ``["all-employees"]``."""
