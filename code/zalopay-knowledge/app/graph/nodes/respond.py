from __future__ import annotations

"""``respond`` node — final response assembly (graph terminal).

The single exit point of the graph.  It reconciles the several ways the run can
arrive here into one consistent state that the API layer maps directly onto
``ChatResponse``:

* **ingest refusal** (index not ready): ``ingest_context`` already set
  ``status="refused"`` + ``answer`` — pass it through.
* **clarify**: the router set ``clarify_question`` — surface it, no answer body.
* **short-circuit intent** (greeting / capability / action): emit a canned,
  source-free reply.
* **normal**: take ``reconcile``'s ``answer`` / ``citations`` / ``conflicts`` /
  ``confidence`` / ``status`` as-is.

Always issues a fresh ``feedback_id`` and computes ``source_departments``.
No LLM call.
"""

import logging
import uuid
from typing import Callable

from langchain_core.messages import AIMessage

from app.config import Settings, get_settings
from app.graph.nodes.router import SHORT_CIRCUIT_INTENTS
from app.graph.state import DeptResult, GraphState

logger = logging.getLogger(__name__)


def make_respond_node(
    *,
    settings: Settings | None = None,
) -> Callable[[GraphState], dict]:
    """Build the ``respond`` node.

    Takes no ports — it only shapes existing state.  ``settings`` is accepted
    for symmetry with the other node factories and future use (e.g. capability
    text driven by config).
    """
    _ = settings or get_settings()

    def respond(state: GraphState) -> dict:
        feedback_id = str(uuid.uuid4())
        lang = state.get("request_language", "en")
        out: dict = {"feedback_id": feedback_id}

        # ── Case 1: ingest already produced a terminal refusal ────────────────
        if state.get("status") == "refused" and state.get("answer"):
            out.update(
                status="refused",
                answer=state["answer"],
                citations=[],
                confidence=0.0,
                source_departments=[],
            )
            if state.get("errors"):
                out["errors"] = list(state["errors"])
            out["messages"] = [AIMessage(content=state["answer"])]
            return out

        # ── Case 2: router asked a clarifying question ────────────────────────
        if state.get("clarify_question"):
            cq = state["clarify_question"]
            out.update(
                status="refused",
                answer=cq.get("prompt", "") if isinstance(cq, dict) else "",
                citations=[],
                confidence=state.get("routing_confidence", 0.0),
                source_departments=[],
                clarify_question=cq,
            )
            if out["answer"]:
                out["messages"] = [AIMessage(content=out["answer"])]
            return out

        # ── Case 3: short-circuit intents (no retrieval happened) ─────────────
        intent = state.get("intent", "")
        if intent in SHORT_CIRCUIT_INTENTS:
            out.update(
                status="answered",
                answer=_canned_reply(intent, lang),
                citations=[],
                confidence=1.0,
                source_departments=[],
            )
            out["messages"] = [AIMessage(content=out["answer"])]
            return out

        # ── Case 4: normal answer from reconcile ──────────────────────────────
        results: list[DeptResult] = list(state.get("dept_results") or [])
        source_departments = [
            r["department"] for r in results if r.get("status") == "answered" and r.get("answer")
        ]

        answer = state.get("answer") or _empty_message(lang)
        status = state.get("status") or ("answered" if source_departments else "refused")

        out.update(
            status=status,
            answer=answer,
            citations=list(state.get("citations") or []),
            confidence=float(state.get("confidence", 0.0)),
            source_departments=source_departments,
            conflicts=list(state.get("conflicts") or []),
        )
        logger.info(
            "respond: status=%s depts=%s citations=%d feedback_id=%s",
            status,
            source_departments,
            len(out["citations"]),
            feedback_id,
        )
        if answer:
            out["messages"] = [AIMessage(content=answer)]
        return out

    return respond


# ── Canned replies for source-free intents ───────────────────────────────────────

def _canned_reply(intent: str, lang: str) -> str:
    vi = lang == "vi"
    if intent == "greeting":
        return (
            "Xin chào! Tôi là trợ lý tri thức nội bộ của ZaloPay. Bạn cần tìm "
            "thông tin gì từ tài liệu của các bộ phận?"
            if vi
            else "Hi! I'm ZaloPay's internal knowledge assistant. What can I help "
            "you find in the team documentation?"
        )
    if intent == "capability_query":
        return (
            "Tôi có thể trả lời câu hỏi dựa trên tài liệu nội bộ của các bộ phận "
            "Risk, Grow Enablement và Bank Partnerships — kèm trích dẫn nguồn. "
            "Tôi không truy cập internet và sẽ từ chối nếu tài liệu không hỗ trợ câu trả lời."
            if vi
            else "I answer questions grounded in the internal documentation of the "
            "Risk, Grow Enablement, and Bank Partnerships teams — always with "
            "source citations. I never browse the internet and I'll refuse when "
            "the documents don't support an answer."
        )
    # action_request
    return (
        "Tôi chỉ có thể tra cứu và trả lời thông tin từ tài liệu nội bộ, "
        "không thể thực hiện hành động hay thay đổi hệ thống."
        if vi
        else "I can only look up and answer information from the internal "
        "documentation — I can't perform actions or change any systems."
    )


def _empty_message(lang: str) -> str:
    return (
        "Xin lỗi, tôi chưa thể tạo câu trả lời cho câu hỏi này."
        if lang == "vi"
        else "Sorry, I couldn't produce an answer for this question."
    )
