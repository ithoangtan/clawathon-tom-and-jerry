from __future__ import annotations

"""``respond`` node — final response assembly (graph terminal).

The single exit point of the graph.  It reconciles the several ways the run can
arrive here into one consistent state that the API layer maps directly onto
``ChatResponse``:

* **ingest refusal** (index not ready): ``ingest_context`` already set
  ``status="refused"`` + ``answer`` — pass it through.
* **short-circuit intent** (greeting / capability / action): emit a canned,
  source-free reply.
* **normal**: take ``reconcile``'s ``answer`` / ``citations`` / ``conflicts`` /
  ``confidence`` / ``status`` as-is. Knowledge questions always fan out across
  all accessible departments; refusal ("not in docs") only when truly absent.

Always issues a fresh ``feedback_id`` and computes ``source_departments``.
No LLM call.
"""

import logging
import uuid
from typing import Callable

from langchain_core.messages import AIMessage

from app.common.departments import routable_departments
from app.common.product_copy import maybe_append_high_stakes_disclaimer, out_of_scope_notice
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

        # ── Case 2: short-circuit intents (no retrieval happened) ─────────────
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
        # Workflow-execution path produces no dept_results — honour the source
        # departments the executor set directly on the state.
        if not source_departments and state.get("source_departments"):
            source_departments = list(state["source_departments"])
        # Collect distinct model IDs that produced answers (typically one)
        models_used = list(dict.fromkeys(
            r["model_used"] for r in results if r.get("model_used")
        ))

        answer = state.get("answer") or _empty_message(lang)
        status = state.get("status") or ("answered" if source_departments else "refused")

        if status in ("answered", "partial") and answer:
            answer = maybe_append_high_stakes_disclaimer(
                answer,
                lang=lang,
                citations=list(state.get("citations") or []),
                departments=source_departments,
            )

        out.update(
            status=status,
            answer=answer,
            citations=list(state.get("citations") or []),
            confidence=float(state.get("confidence", 0.0)),
            source_departments=source_departments,
            conflicts=list(state.get("conflicts") or []),
            model_used=", ".join(models_used) if models_used else "",
        )
        refusals = state.get("refusals")
        if refusals:
            out["refusals"] = list(refusals)
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
            "Xin chào! Tôi là trợ lý tri thức nội bộ của Zalopay. Bạn cần tìm "
            "thông tin gì từ tài liệu của các bộ phận?"
            if vi
            else "Hi! I'm Zalopay's internal knowledge assistant. What can I help "
            "you find in the team documentation?"
        )
    if intent == "capability_query":
        scope = out_of_scope_notice("vi" if vi else "en")
        depts = routable_departments()
        if vi:
            dept_lines = "\n".join(
                f"- **{d.name_vi}** (`{d.key}`): {d.description_vi}" for d in depts
            )
            return (
                f"Hiện tại có **{len(depts)} bộ phận** được hỗ trợ:\n\n"
                f"{dept_lines}\n\n"
                "Tôi trả lời câu hỏi dựa trên tài liệu nội bộ của các bộ phận trên — kèm trích dẫn nguồn. "
                "Tôi không truy cập internet và sẽ từ chối nếu tài liệu không hỗ trợ câu trả lời.\n\n"
                f"{scope}"
            )
        else:
            dept_lines = "\n".join(
                f"- **{d.name_en}** (`{d.key}`): {d.description_en}" for d in depts
            )
            return (
                f"There are currently **{len(depts)} departments** covered:\n\n"
                f"{dept_lines}\n\n"
                "I answer questions grounded in the internal documentation of the teams above — "
                "always with source citations. I never browse the internet and I'll refuse when "
                "the documents don't support an answer.\n\n"
                f"{scope}"
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
