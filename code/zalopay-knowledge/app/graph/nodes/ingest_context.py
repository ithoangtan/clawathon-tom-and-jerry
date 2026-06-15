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

import json
import logging
import time
from typing import Callable, Optional

from app.common.departments import routable_keys
from app.config import Settings, get_settings
from app.graph.nodes._helpers import build_retrieval_query, detect_language, format_conversation_history
from app.graph.state import GraphState, _RESET_SENTINEL
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
        # Reset terminal state from any previous turn in this session so a
        # prior refusal does not block routing for the current question.
        # Also reset deadline_ts so a stale deadline from an interrupted run
        # (e.g. server hot-reload mid-request) never causes instant budget exhaustion.
        # dept_results uses a sentinel to discard stale results from prior turns.
        out: dict = {
            "status": None,
            "answer": None,
            "citations": [],
            "conflicts": None,
            "clarify_question": None,
            "source_departments": [],
            "errors": [],
            "refusals": [],
            "deadline_ts": time.time() + cfg.graph_budget_s,
            "dept_results": [{_RESET_SENTINEL: True}],
        }

        # ── Language ──────────────────────────────────────────────────────────
        lang = state.get("request_language") or detect_language(state.get("question", ""))
        out["request_language"] = lang

        # ── STM conversation context (FR-1.3) ───────────────────────────────────
        messages = state.get("messages") or []
        out["conversation_history"] = format_conversation_history(messages, exclude_last=True)
        out["retrieval_query"] = build_retrieval_query(state.get("question", ""), messages)

        # ── Allowed departments (FR-7.2 role-based access control) ───────────
        role = state.get("role", "")
        allowed_depts = _resolve_allowed_departments(role, cfg.role_dept_access_json)
        out["allowed_departments"] = allowed_depts

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


def _resolve_allowed_departments(role: str, role_dept_access_json: str) -> list[str]:
    """Return the department keys this role may access.

    When ``role_dept_access_json`` is empty or the role is not listed, all
    departments are allowed (open-access default).
    """
    all_keys = list(routable_keys())
    if not role_dept_access_json:
        return all_keys
    try:
        mapping: dict[str, list[str]] = json.loads(role_dept_access_json)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Invalid role_dept_access_json — defaulting to all departments")
        return all_keys
    if role not in mapping:
        return all_keys
    allowed = [k for k in mapping[role] if k in set(all_keys)]
    return allowed if allowed else all_keys


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
