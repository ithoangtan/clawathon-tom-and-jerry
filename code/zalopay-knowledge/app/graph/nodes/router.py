from __future__ import annotations

"""``router`` node — intent classification and department fan-out.

Uses the SMALL model tier with ``router.v1.yaml``.  It writes ``intent``,
``target_departments`` and ``routing_confidence`` to the state and never answers
the question itself.

Control paths:

1. **Greeting fast-path** (deterministic, no LLM): obvious greetings / small-talk
   short-circuit to a friendly canned reply — never clarify, never "not in docs".
2. **Short-circuit intents** (greeting / capability_query / action_request):
   ``target_departments=[]`` — the ``respond`` node emits a canned reply.
3. **Workflow execution**: routed to the discover→execute path.
4. **Knowledge questions**: fan out to **ALL** departments the role may access
   (no department clarification — a question may live in several places; we
   answer from the combined grounded context, refusing only when truly absent).

User-pinned departments still bypass the LLM and answer only those.
"""

import logging
import re
from typing import Callable

from app.common.departments import (
    department_catalog_text,
    format_department_keys_for_prompt,
    routable_keys,
)
from app.config import Settings, get_settings
from app.graph.nodes._helpers import budget_exceeded, parse_json_response
from app.graph.state import GraphState
from app.ports.errors import LLMUnavailable
from app.ports.llm import LLMPort
from app.ports.types import ModelTier
from app.prompts import load_prompt

logger = logging.getLogger(__name__)

# Intents that need no retrieval — handled by a canned reply in ``respond``.
SHORT_CIRCUIT_INTENTS = frozenset(
    {"greeting", "capability_query", "action_request"}
)

# Intent that routes to the workflow-execution path (discover → execute) instead
# of the department fan-out.  Handled specially in ``build._make_route_after_router``.
WORKFLOW_INTENT = "workflow_execution"

# Out-of-scope intents — refusal with escalation pointer (no retrieval).
OUT_OF_SCOPE_INTENTS = frozenset({"status_or_data", "customer_facing_info", "external_system_info"})

# Deterministic greeting / small-talk detector — keeps chit-chat friendly and
# off the wiki-retrieval path (no clarify, no "not in docs"). Conservative: only
# short messages so real knowledge questions that happen to contain "chào"/"thanks"
# still fan out normally. The LLM intent path covers anything this misses.
_GREETING_RE = re.compile(
    r"(?:^|\b)(?:hi|hello|hey|yo|howdy|good\s+(?:morning|afternoon|evening)|thanks|thank\s+you)(?:\b|$)"
    r"|xin\s*chào|\bchào\b|\balo\b|\bhế\s*lô\b"
    r"|có\s+ai|ai\s+(?:ở\s+)?đó|ai\s+đấy"
    r"|cảm\s+ơn|cám\s+ơn"
    r"|bạn\s+(?:là\s+ai|tên\s+(?:gì|là)|khỏe\s+không)",
    re.IGNORECASE,
)


def _looks_like_greeting(question: str) -> bool:
    q = (question or "").strip()
    if not q or len(q) > 30:
        return False
    return bool(_GREETING_RE.search(q))


def make_router_node(
    llm: LLMPort,
    *,
    settings: Settings | None = None,
) -> Callable[[GraphState], dict]:
    """Build the ``router`` node bound to the LLM adapter.

    Args:
        llm: The SMALL-tier-capable LLM adapter.
        settings: Injectable for tests; defaults to :func:`get_settings`.

    Returns:
        A LangGraph node callable ``(GraphState) -> dict``.
    """
    cfg = settings or get_settings()
    prompt = load_prompt("router")

    def router(state: GraphState) -> dict:
        allowed = set(state.get("allowed_departments") or routable_keys())
        lang = state.get("request_language", "en")

        # ── Path 0: user-pinned departments bypass the LLM ────────────────────
        pinned_raw = list(state.get("pinned") or [])
        pinned = [d for d in pinned_raw if d in allowed]
        if pinned_raw and not pinned:
            # All pinned departments are outside the role's allowlist → deny.
            logger.warning("Router: all pinned departments denied (role=%s, pinned=%s)", state.get("role"), pinned_raw)
            denied_names = ", ".join(pinned_raw)
            if lang == "vi":
                msg = f"Bạn không có quyền truy cập các phòng ban: {denied_names}."
            else:
                msg = f"You do not have permission to access the requested department(s): {denied_names}."
            return {
                "intent": "pinned",
                "target_departments": [],
                "routing_confidence": 0.0,
                "clarify_question": None,
                "status": "refused",
                "answer": msg,
                "errors": ["access_denied"],
            }
        if pinned_raw and pinned:
            logger.info("Router: honouring %d pinned department(s)", len(pinned))
            return {
                "intent": "pinned",
                "target_departments": pinned,
                "routing_confidence": 1.0,
                "clarify_question": None,
            }

        # ── Path G: deterministic greeting / small-talk (no LLM, no clarify) ──
        if _looks_like_greeting(state.get("question", "")):
            logger.info("Router: greeting fast-path")
            return {
                "intent": "greeting",
                "target_departments": [],
                "routing_confidence": 1.0,
                "clarify_question": None,
            }

        # ── Guard: out of budget before we even start ─────────────────────────
        if budget_exceeded(state.get("deadline_ts")):
            logger.warning("Router: budget exhausted before classification")
            return _fallback_route(allowed, reason="budget_exceeded", lang=lang)

        # ── Path 1: LLM classification ────────────────────────────────────────
        messages = _build_messages(
            prompt,
            state.get("question", ""),
            state.get("conversation_history") or "",
            lang=state.get("request_language", "en"),
        )
        try:
            result = llm.complete(
                tier=ModelTier.SMALL,
                messages=messages,
                temperature=0.0,
                response_format="json",
                timeout_s=cfg.branch_timeout_s,
            )
            data = parse_json_response(result.text)
        except (LLMUnavailable, ValueError) as exc:
            # Degrade: fan out to all allowed departments rather than fail.
            logger.warning("Router classification failed (%s); fanning out wide", exc)
            return _fallback_route(allowed, reason="router_unavailable", lang=lang)

        intent = str(data.get("intent", "unclear"))
        confidence = _clamp(data.get("confidence", 0.0))

        # ── Path 2: short-circuit intents (no retrieval needed) ───────────────
        if intent in SHORT_CIRCUIT_INTENTS:
            return {
                "intent": intent,
                "target_departments": [],
                "routing_confidence": confidence,
                "clarify_question": None,
            }

        # ── Path 2a': workflow execution (run a named/known workflow) ─────────
        # No department fan-out and no clarify gate — the workflow path resolves
        # the target itself in ``discover_workflow`` (see build wiring).
        if intent == WORKFLOW_INTENT:
            logger.info("Router: workflow_execution (conf=%.2f)", confidence)
            return {
                "intent": WORKFLOW_INTENT,
                "target_departments": [],
                "routing_confidence": confidence,
                "clarify_question": None,
            }

        # ── Path 3: knowledge question → fan out to ALL accessible departments ─
        # No department clarification: a question may live in several places, so we
        # search everything the role can access and let the grounded pipeline
        # (grade → synthesize → verify → reconcile) answer from the combined
        # context — refusing only when truly nothing relevant exists. The LLM's
        # department picks (``raw_targets``) are advisory only and intentionally
        # ignored here. ``confidence`` is kept for telemetry/UI, not for gating.
        fan = sorted(allowed)
        logger.info("Router: intent=%s → fan-out all %d dept(s) conf=%.2f", intent, len(fan), confidence)
        return {
            "intent": intent,
            "target_departments": fan,
            "routing_confidence": confidence,
            "clarify_question": None,
        }

    return router


# ── Internals ───────────────────────────────────────────────────────────────────

def _build_messages(
    prompt,
    question: str,
    conversation_history: str,
    *,
    lang: str = "en",
) -> list[dict]:
    history_block = conversation_history or "(none)"
    rendered = prompt.render(
        question=question,
        department_catalog=department_catalog_text(lang),
        department_keys=format_department_keys_for_prompt(),
        conversation_history=history_block,
    )
    return [
        {"role": "system", "content": rendered["system"]},
        {"role": "user", "content": rendered["user"]},
    ]


def _fallback_route(allowed: set[str], *, reason: str, lang: str = "en") -> dict:
    """Fan out to every allowed department when the router cannot classify."""
    return {
        "intent": "unclear",
        "target_departments": list(allowed),
        "routing_confidence": 0.0,
        "clarify_question": None,
        "errors": [reason],
    }


def _clamp(value, lo: float = 0.0, hi: float = 1.0) -> float:
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return 0.0
