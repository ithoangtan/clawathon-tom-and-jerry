from __future__ import annotations

"""``ingest_context`` node — the graph entry point.

Runs once before routing.  It normalises the request context that the rest of
the pipeline depends on:

* detects the request language (cheap, token-free heuristic),
* derives the departments this user/role is allowed to query,
* recalls user preferences from short-term memory (STM) when available,
* fails fast with a refusal when the knowledge base index is not ready.

It performs no LLM calls.
"""

import logging
from typing import Callable, Optional

from app.common.departments import iter_keys
from app.config import Settings, get_settings
from app.graph.nodes._helpers import detect_language
from app.graph.state import GraphState
from app.ports.errors import RetrieverUnavailable
from app.ports.retriever import RetrieverPort

logger = logging.getLogger(__name__)

# A recall callable takes (user_id, session_id) and returns a preference string
# (or None).  It may raise; the node treats any failure as "memory degraded".
RecallFn = Callable[[str, str], Optional[str]]


def make_ingest_context_node(
    retriever: RetrieverPort,
    *,
    recall: RecallFn | None = None,
    settings: Settings | None = None,
) -> Callable[[GraphState], dict]:
    """Build the ``ingest_context`` node bound to its dependencies.

    Args:
        retriever: Used only for an ``is_ready()`` liveness check.
        recall: Optional STM recall function.  When ``None`` (local/stateless),
                the node sets ``recalled_preferences=None`` without degrading.
        settings: Injectable for tests; defaults to :func:`get_settings`.

    Returns:
        A LangGraph node callable ``(GraphState) -> dict`` returning only the
        keys it sets.
    """
    cfg = settings or get_settings()

    def ingest_context(state: GraphState) -> dict:
        out: dict = {}

        # ── Language ──────────────────────────────────────────────────────────
        lang = state.get("request_language") or detect_language(state.get("question", ""))
        out["request_language"] = lang

        # ── Allowed departments (RBAC) ────────────────────────────────────────
        role = state.get("role") or "business"
        access = cfg.role_dept_access
        allowed = access.get(role)
        if allowed is None:
            # Unknown role → conservative default of all departments, logged.
            logger.warning("Unknown role %r — defaulting to all departments", role)
            allowed = list(iter_keys())
        out["allowed_departments"] = list(allowed)

        # ── Index readiness ───────────────────────────────────────────────────
        try:
            ready = retriever.is_ready()
        except RetrieverUnavailable:
            ready = False
        if not ready:
            logger.warning("Retriever index not ready — short-circuiting to refusal")
            out["status"] = "refused"
            out["answer"] = _kb_unavailable_message(lang)
            out["errors"] = ["retriever_not_ready"]
            return out

        # ── STM preference recall ─────────────────────────────────────────────
        if recall is None:
            out["recalled_preferences"] = None
            out["memory_degraded"] = False
        else:
            try:
                out["recalled_preferences"] = recall(
                    state.get("user_id", ""), state.get("session_id", "")
                )
                out["memory_degraded"] = False
            except Exception as exc:  # noqa: BLE001 — degrade, never fail the request
                logger.warning("STM recall failed, continuing statelessly: %s", exc)
                out["recalled_preferences"] = None
                out["memory_degraded"] = True

        return out

    return ingest_context


def _kb_unavailable_message(lang: str) -> str:
    """Localised 'knowledge base not ready' refusal text."""
    if lang == "vi":
        return (
            "Cơ sở tri thức hiện chưa sẵn sàng (chưa được đồng bộ). "
            "Vui lòng chạy đồng bộ dữ liệu rồi thử lại."
        )
    return (
        "The knowledge base is not ready yet (no documents have been indexed). "
        "Please run a sync and try again."
    )
