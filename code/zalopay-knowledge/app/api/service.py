from __future__ import annotations

"""Chat service — invokes the LangGraph pipeline and maps state to API models."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from functools import lru_cache
from typing import Any, Iterator

from langchain_core.messages import HumanMessage

from app.graph import get_compiled_graph
from app.api.context import UserContext
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    CitationModel,
    ClarifyingQuestion,
    ConflictModel,
    ConflictSide,
)
from app.config import Settings, get_settings
from app.store.audit import AuditStore
from app.store.feedback import FeedbackStore

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)


@lru_cache(maxsize=1)
def get_audit_store() -> AuditStore:
    cfg = get_settings()
    from pathlib import Path

    return AuditStore(Path(cfg.index_dir) / "audit.db")


@lru_cache(maxsize=1)
def get_feedback_store() -> FeedbackStore:
    cfg = get_settings()
    from pathlib import Path

    return FeedbackStore(Path(cfg.index_dir) / "feedback.db")


def _initial_state(ctx: UserContext, request: ChatRequest, cfg: Settings) -> dict[str, Any]:
    return {
        "session_id": ctx.session_id,
        "user_id": ctx.user_id,
        "role": ctx.role,
        "home_department": ctx.home_department,
        "question": request.question,
        "pinned": list(request.target_departments or []),
        "deadline_ts": time.time() + cfg.graph_budget_s,
        "messages": [HumanMessage(content=request.question)],
    }


def _graph_config(ctx: UserContext) -> dict[str, Any]:
    return {"configurable": {"thread_id": ctx.session_id, "actor_id": ctx.user_id}}


def state_to_response(state: dict[str, Any]) -> ChatResponse:
    """Map terminal :class:`GraphState` to :class:`ChatResponse`."""
    citations = [
        CitationModel(**c) if isinstance(c, dict) else CitationModel.model_validate(c)
        for c in (state.get("citations") or [])
    ]
    conflicts_raw = state.get("conflicts") or []
    conflicts: list[ConflictModel] | None = None
    if conflicts_raw:
        conflicts = []
        for c in conflicts_raw:
            sides = [
                ConflictSide(
                    department=s["department"],
                    statement=s.get("statement", ""),
                    citation=CitationModel(**s.get("citation", {})),
                )
                for s in c.get("sides", [])
            ]
            conflicts.append(ConflictModel(topic=c.get("topic"), sides=sides))

    clarify = state.get("clarify_question")
    clarifying = None
    if clarify and isinstance(clarify, dict):
        clarifying = ClarifyingQuestion(**clarify)

    errors = list(state.get("errors") or [])
    refusal_reason = "access_denied" if "access_denied" in errors else None

    return ChatResponse(
        answer=state.get("answer") or "",
        citations=citations,
        source_departments=state.get("source_departments") or [],
        confidence=float(state.get("confidence", 0.0)),
        feedback_id=state.get("feedback_id") or "",
        status=state.get("status") or "refused",
        conflicts=conflicts,
        clarifying_question=clarifying,
        lang=state.get("request_language"),
        refusal_reason=refusal_reason,
    )


def record_chat_outcome(
    ctx: UserContext,
    request: ChatRequest,
    response: ChatResponse,
    *,
    latency_ms: int,
) -> None:
    """Persist feedback correlation + audit row for a completed chat."""
    get_feedback_store().register_pending(response.feedback_id)
    get_audit_store().log_query(
        user_id=ctx.user_id,
        session_id=ctx.session_id,
        role=ctx.role,
        question=request.question,
        departments=response.source_departments,
        status=response.status,
        confidence=response.confidence,
        latency_ms=latency_ms,
        feedback_id=response.feedback_id,
        citations=[c.model_dump() for c in response.citations],
    )


def run_chat(ctx: UserContext, request: ChatRequest) -> ChatResponse:
    """Execute the full graph synchronously with a hard deadline."""
    cfg = get_settings()
    graph = get_compiled_graph()
    started = time.perf_counter()

    def _invoke() -> dict[str, Any]:
        return graph.invoke(
            _initial_state(ctx, request, cfg),
            _graph_config(ctx),
        )

    try:
        future = _executor.submit(_invoke)
        result = future.result(timeout=cfg.graph_budget_s)
    except FuturesTimeout:
        raise TimeoutError("Request timeout") from None
    except Exception as exc:
        logger.exception("Graph invocation failed")
        raise RuntimeError(str(exc)) from exc

    latency_ms = int((time.perf_counter() - started) * 1000)
    return state_to_response(result)


def stream_chat(ctx: UserContext, request: ChatRequest) -> Iterator[dict[str, Any]]:
    """Stream LangGraph node updates as SSE-friendly event dicts."""
    cfg = get_settings()
    graph = get_compiled_graph()
    started = time.perf_counter()

    yield {"event": "start", "data": {"question": request.question}}

    final_state: dict[str, Any] = {}
    try:
        for chunk in graph.stream(
            _initial_state(ctx, request, cfg),
            _graph_config(ctx),
            stream_mode="updates",
        ):
            for node_name, update in chunk.items():
                yield {"event": "node", "data": {"node": node_name}}
                if isinstance(update, dict):
                    final_state.update(update)
    except Exception as exc:
        logger.exception("Graph stream failed")
        yield {"event": "error", "data": {"detail": str(exc)}}
        return

    # Merge with any values only set on the full state
    if not final_state.get("answer"):
        try:
            final_state = graph.invoke(
                _initial_state(ctx, request, cfg),
                _graph_config(ctx),
            )
        except Exception:
            pass

    response = state_to_response(final_state)
    latency_ms = int((time.perf_counter() - started) * 1000)
    record_chat_outcome(ctx, request, response, latency_ms=latency_ms)

    yield {"event": "done", "data": response.model_dump()}
