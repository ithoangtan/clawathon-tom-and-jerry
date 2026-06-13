from __future__ import annotations

"""``router`` node — intent classification and department fan-out selection.

Uses the SMALL model tier with ``router.v1.yaml``.  It writes ``intent``,
``target_departments``, ``routing_confidence`` and (when confidence is too low)
``clarify_question`` to the state.  It never answers the question itself.

Three control paths leave this node:

1. **Short-circuit intents** (greeting / capability_query / action_request):
   ``target_departments=[]`` — the ``respond`` node emits a canned reply.
2. **Clarify**: confidence below ``ROUTE_CONFIDENCE_MIN`` ⇒ a clarifying
   question is set and no department branches run.
3. **Fan-out**: one department subgraph per entry in ``target_departments``.

User-pinned departments bypass the LLM and the confidence gate entirely.
"""

import logging
from typing import Callable

from app.common.access import ACCESS_DENIED_ERROR, access_denied_message
from app.common.departments import department_catalog_text, iter_keys
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

_VALID_DEPARTMENTS = frozenset(iter_keys())


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
        allowed = set(state.get("allowed_departments") or iter_keys())
        lang = state.get("request_language", "en")

        # ── Path 0: user-pinned departments bypass the LLM ────────────────────
        pinned_raw = list(state.get("pinned") or [])
        pinned = [d for d in pinned_raw if d in allowed]
        if pinned_raw and pinned:
            logger.info("Router: honouring %d pinned department(s)", len(pinned))
            return {
                "intent": "pinned",
                "target_departments": pinned,
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
        raw_targets = [
            d for d in data.get("target_departments", []) if d in _VALID_DEPARTMENTS
        ]
        targets = [d for d in raw_targets if d in allowed]

        # Router classified to department(s) the user cannot access — refuse, no leakage.
        if raw_targets and not targets and intent not in SHORT_CIRCUIT_INTENTS:
            logger.info(
                "Access denied: routed targets %s not in allowed %s",
                raw_targets,
                sorted(allowed),
            )
            return _access_denied_route(lang)

        # ── Path 2: short-circuit intents (no retrieval needed) ───────────────
        if intent in SHORT_CIRCUIT_INTENTS:
            return {
                "intent": intent,
                "target_departments": [],
                "routing_confidence": confidence,
                "clarify_question": None,
            }

        # ── Path 3: clarify on low confidence / no usable target ──────────────
        if not targets or confidence < cfg.route_confidence_min:
            logger.info(
                "Router: clarify (intent=%s confidence=%.2f targets=%s)",
                intent,
                confidence,
                targets,
            )
            return {
                "intent": intent,
                "target_departments": [],
                "routing_confidence": confidence,
                "clarify_question": _clarify_prompt(state.get("request_language", "en"), allowed),
            }

        # ── Path 4: normal fan-out ────────────────────────────────────────────
        logger.info("Router: intent=%s targets=%s conf=%.2f", intent, targets, confidence)
        return {
            "intent": intent,
            "target_departments": targets,
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
        conversation_history=history_block,
    )
    return [
        {"role": "system", "content": rendered["system"]},
        {"role": "user", "content": rendered["user"]},
    ]


def _access_denied_route(lang: str) -> dict:
    """Terminal refusal when routing targets departments outside the allowlist."""
    return {
        "intent": "access_denied",
        "target_departments": [],
        "routing_confidence": 0.0,
        "clarify_question": None,
        "status": "refused",
        "answer": access_denied_message(lang),
        "errors": [ACCESS_DENIED_ERROR],
    }


def _fallback_route(allowed: set[str], *, reason: str, lang: str = "en") -> dict:
    """Fan out to every allowed department when the router cannot classify."""
    if not allowed:
        return _access_denied_route(lang)
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


def _clarify_prompt(lang: str, allowed: set[str] | None = None) -> dict:
    """Build the ``ClarifyingQuestion`` payload (matches the API schema shape)."""
    options = sorted(allowed) if allowed else list(iter_keys())
    if lang == "vi":
        prompt = (
            "Câu hỏi của bạn có thể liên quan đến nhiều bộ phận. "
            "Bạn muốn hỏi bộ phận nào?"
        )
    else:
        prompt = (
            "Your question could relate to more than one department. "
            "Which department are you asking about?"
        )
    return {"prompt": prompt, "options": options}
