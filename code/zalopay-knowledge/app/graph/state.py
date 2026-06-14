from __future__ import annotations

"""LangGraph graph state for the Zalopay Knowledge Agent.

This module defines the canonical ``GraphState`` TypedDict plus all supporting
TypedDicts and reducer helpers.  Every graph node receives and returns a
subset of this state — never instantiate it directly outside of tests.

Reducer contract
----------------
``evidence`` and ``dept_results`` use commutative reducers so concurrent
department subgraph branches can write to the same state key without
clobbering each other.  The LangGraph runtime calls these automatically when
multiple branches return the same key in the same superstep.
"""

import operator
from typing import Annotated, Literal, Optional

# pydantic (used by LangGraph to derive state schemas) requires the
# typing_extensions TypedDict on Python < 3.12 — using typing.TypedDict raises
# PydanticUserError at graph introspection time.  typing_extensions ships as a
# pydantic dependency, so this import is always available.
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


# ── Supporting TypedDicts ─────────────────────────────────────────────────────

class Chunk(TypedDict, total=False):
    """A retrieved evidence chunk stored in ``GraphState.evidence``."""

    chunk_id: str
    department: str
    doc_type: str
    title: str
    url: str
    section: Optional[str]
    last_modified: Optional[str]
    lifecycle_state: str  # "active" | "deprecated" | "sunset"
    source_type: str      # "confluence" | "pdf"
    page: Optional[int]
    text: str
    score: float
    compressed_text: Optional[str]
    """Sentences extracted by the compress node; synthesize prefers this over text."""


class Citation(TypedDict, total=False):
    """A source citation included in the final response."""

    title: str
    url: str
    section: Optional[str]
    last_modified: Optional[str]
    lifecycle_state: Optional[str]
    deprecated: bool
    successor_url: Optional[str]
    source_type: Optional[str]
    page: Optional[int]
    excerpt: Optional[str]
    """Chunk text snippet (~400 chars) for the Citation Evidence Inspector."""
    chunk_id: Optional[str]
    """Stable chunk id when sourced from retrieval."""
    doc_type: Optional[str]
    """Document type for high-stakes disclaimer heuristics."""


class ConflictSide(TypedDict, total=False):
    """One side of a factual conflict between department sources."""

    department: str
    statement: str
    citation: Citation


class Conflict(TypedDict, total=False):
    """A detected factual conflict that must be surfaced to the user."""

    topic: Optional[str]
    sides: list[ConflictSide]


class DeptResult(TypedDict, total=False):
    """The outcome of a single department subgraph run."""

    department: str
    status: str  # "answered" | "refused" | "timeout"
    answer: str
    citations: list[Citation]
    confidence: float
    warnings: list[str]


# ── Reducers ──────────────────────────────────────────────────────────────────

def merge_dict(a: dict, b: dict) -> dict:
    """Commutative dict merge reducer for ``evidence``.

    Each concurrent department branch writes its own key into ``evidence``
    (``evidence[department] = [chunk, ...]``).  This reducer simply merges
    both dicts so no branch clobbers another.  Order of application does not
    matter (commutative).

    Args:
        a: Existing evidence dict from state.
        b: Incoming partial evidence dict from a branch.

    Returns:
        Merged dict (new object, both inputs are unchanged).
    """
    return {**a, **b}


# Sentinel dict key used by ingest_context to signal a full reset of dept_results.
_RESET_SENTINEL = "__reset__"


def dept_results_reducer(a: list, b: list) -> list:
    """Reducer for ``dept_results`` that supports per-turn reset.

    Concurrent department branches APPEND their single :class:`DeptResult` to the
    list (the normal ``operator.add`` behaviour).  ``ingest_context`` returns
    ``[{_RESET_SENTINEL: True}]`` at the start of each turn to discard stale
    results from previous turns before the new branches write their results.

    The sentinel is never seen by reconcile because it is replaced by the real
    dept_branch results within the same graph execution.
    """
    if b and isinstance(b[0], dict) and b[0].get(_RESET_SENTINEL):
        return []  # Clear accumulated results from previous turns
    return (a or []) + (b or [])


# ── Graph state ───────────────────────────────────────────────────────────────

class GraphState(TypedDict, total=False):
    """The full mutable state passed between LangGraph nodes.

    ``total=False`` means all keys are optional by default — nodes declare
    only the keys they read and write.  Use ``Annotated`` with a reducer for
    keys that are written by concurrent branches.

    Field groups
    ------------
    Context     — populated by ``ingest_context`` before routing.
    Routing     — populated by the ``router`` node.
    Evidence    — populated by ``retrieve`` nodes (one per department).
    Results     — populated by ``synthesize``/``verify`` branches.
    Response    — populated by ``reconcile`` and ``respond``.
    Meta        — populated by ``respond`` for audit / feedback.
    """

    # ── Context ──────────────────────────────────────────────────────────────
    session_id: str
    """AgentBase / local session identifier (required header)."""

    user_id: str
    """Calling user identifier (required header)."""

    role: str
    """User role: engineer | pm | ops | risk | business."""

    home_department: str
    """User's primary department key — used for tiebreaking and role-style hints."""

    request_language: str
    """Detected request language: ``"en"`` or ``"vi"``."""

    allowed_departments: list[str]
    """Departments to fan out to — always all departments (knowledge is open)."""

    # ── Input ────────────────────────────────────────────────────────────────
    question: str
    """The original user question."""

    retrieval_query: str
    """Query sent to the retriever — may include STM context for follow-ups."""

    conversation_history: str
    """Formatted prior turns for router / synthesis prompts (FR-1.3)."""

    pinned: list[str]
    """Departments explicitly pinned by the user (bypasses router confidence gate)."""

    # ── Routing ──────────────────────────────────────────────────────────────
    target_departments: list[str]
    """Departments chosen by the router (or pinned by the user)."""

    intent: str
    """Classified intent label (e.g. ``policy_lookup``, ``process_question``, ``greeting``)."""

    routing_confidence: float
    """Router confidence score 0–1."""

    clarify_question: Optional[str]
    """Clarifying question to emit when routing confidence < ROUTE_CONFIDENCE_MIN."""

    # ── Evidence (parallel writes from concurrent branches) ───────────────────
    evidence: Annotated[dict[str, list[Chunk]], merge_dict]
    """Map of department key → list of retrieved chunks.
    Written by concurrent ``retrieve`` nodes; merged by the ``merge_dict`` reducer."""

    # ── Department results (parallel writes, list append) ─────────────────────
    dept_results: Annotated[list[DeptResult], dept_results_reducer]
    """Results from each department's synthesize→verify pipeline.
    Written by concurrent branches; supports per-turn reset via dept_results_reducer."""

    # ── Response ─────────────────────────────────────────────────────────────
    citations: list[Citation]
    """Final deduplicated citation list for the response."""

    source_departments: list[str]
    """Departments that contributed an answered result — maps to
    ``ChatResponse.source_departments``.  Set by the ``respond`` node."""

    confidence: float
    """Aggregate confidence score 0–1 for the merged answer."""

    refusals: list[str]
    """Departments that refused (grade gate or verify failure)."""

    conflicts: list[Conflict]
    """Detected factual conflicts between department answers."""

    recalled_preferences: Optional[str]
    """User preference context recalled from STM (e.g. preferred language, verbosity)."""

    answer: str
    """The final merged/synthesized answer text."""

    status: str
    """Overall response status: ``answered`` | ``refused`` | ``partial``."""

    # ── Conversation history (managed by LangGraph add_messages reducer) ──────
    messages: Annotated[list, add_messages]
    """Conversation message history.  Uses LangGraph's built-in ``add_messages``
    reducer so concurrent writes are handled safely."""

    # ── Meta / audit ─────────────────────────────────────────────────────────
    feedback_id: str
    """UUID issued by ``respond`` node — used by ``POST /feedback`` to correlate."""

    memory_degraded: bool
    """True when STM recall failed and the agent is operating statelessly."""

    errors: list[str]
    """Non-fatal errors accumulated during the run (displayed in debug mode)."""

    deadline_ts: float
    """Unix timestamp of the global graph budget deadline (set by the API handler)."""


# ── Department subgraph state ─────────────────────────────────────────────────

class DeptState(TypedDict, total=False):
    """Isolated state for a single department branch.

    The router fans out one branch per target department via the LangGraph
    ``Send`` API (``Send("dept_subgraph", DeptState payload)``).  Each branch
    runs ``retrieve → grade → synthesize → verify`` against its own copy of
    this state and never sees another department's intermediate data.

    The ONLY key written back to the parent :class:`GraphState` is
    ``dept_results`` (concatenated by ``operator.add``) and ``evidence``
    (merged by ``merge_dict``) — both use the same reducers as the parent so
    LangGraph can join the parallel branches without clobbering.
    """

    # ── Inputs (set by the Send payload from the router fan-out) ───────────────
    department: str
    """The department key this branch is responsible for."""

    question: str
    """The user question (copied from GraphState)."""

    retrieval_query: str
    """Retriever query, expanded with STM context when needed."""

    conversation_history: str
    """Prior conversation turns for grounded follow-up answers."""

    role: str
    """User role — drives synthesis tone via the role-style map."""

    home_department: str
    """User's home department — used for role-style hints."""

    request_language: str
    """``"en"`` or ``"vi"`` — synthesis output language."""

    recalled_preferences: Optional[str]
    """User STM preferences, or None when memory is degraded/empty."""

    deadline_ts: float
    """Branch budget deadline (Unix ts) — nodes refuse rather than overrun it."""

    # ── retrieve output ───────────────────────────────────────────────────────
    chunks: list[Chunk]
    """Raw chunks returned by the retriever, sorted by score descending."""

    # ── grade output ──────────────────────────────────────────────────────────
    graded_chunks: list[Chunk]
    """Chunks that passed the grade gate, re-scored with the LLM relevance score."""

    # ── synthesize output ─────────────────────────────────────────────────────
    draft_answer: str
    """The grounded answer with inline ``[n]`` citation markers (or the
    ``CANNOT_ANSWER_FROM_SOURCES`` sentinel)."""

    draft_citations: list[Citation]
    """Citations indexed 1:1 with the ``[n]`` markers in ``draft_answer``."""

    # ── Outputs reduced into the parent GraphState ────────────────────────────
    evidence: Annotated[dict[str, list[Chunk]], merge_dict]
    """``{department: graded_chunks}`` — merged into the parent for audit/debug."""

    dept_results: Annotated[list[DeptResult], dept_results_reducer]
    """A single-element list with this branch's :class:`DeptResult`,
    merged into the parent by ``dept_results_reducer``."""
