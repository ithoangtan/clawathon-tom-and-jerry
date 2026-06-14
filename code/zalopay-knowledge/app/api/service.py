from __future__ import annotations

"""Chat service — invokes the LangGraph pipeline and maps state to API models."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from functools import lru_cache
from typing import Any, Iterator

from langchain_core.messages import HumanMessage

from app.common.security import assert_agent_enabled
from app.common.stage_trace import build_stage_trace
from app.graph import get_compiled_graph
from app.graph.nodes.router import OUT_OF_SCOPE_INTENTS
from app.graph.pipeline import PipelineTracker, map_node_to_step_key
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
from app.api.stream_events import build_node_event_data
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


def _to_citation_model(c: dict | CitationModel) -> CitationModel:
    """Map graph citations to API model, dropping internal-only fields (e.g. doc_type)."""
    if isinstance(c, CitationModel):
        return c
    allowed = CitationModel.model_fields.keys()
    payload = {k: v for k, v in c.items() if k in allowed}
    return CitationModel(**payload)


def _refusal_reason(state: dict[str, Any]) -> str | None:
    """Map terminal graph state to a structured refusal reason for the UI."""
    errors = list(state.get("errors") or [])
    intent = state.get("intent", "")
    if intent in OUT_OF_SCOPE_INTENTS:
        return "out_of_scope"
    return None


def state_to_response(state: dict[str, Any]) -> ChatResponse:
    """Map terminal :class:`GraphState` to :class:`ChatResponse`."""
    citations = [_to_citation_model(c) for c in (state.get("citations") or [])]
    conflicts_raw = state.get("conflicts") or []
    conflicts: list[ConflictModel] | None = None
    if conflicts_raw:
        conflicts = []
        for c in conflicts_raw:
            sides = [
                ConflictSide(
                    department=s["department"],
                    statement=s.get("statement", ""),
                    citation=_to_citation_model(s.get("citation", {})),
                )
                for s in c.get("sides", [])
            ]
            conflicts.append(ConflictModel(topic=c.get("topic"), sides=sides))

    clarify = state.get("clarify_question")
    clarifying = None
    if clarify and isinstance(clarify, dict):
        clarifying = ClarifyingQuestion(**clarify)

    refusal_reason = _refusal_reason(state)
    refusals_raw = state.get("refusals") or []
    refusals = list(refusals_raw) if refusals_raw else None

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
        refusals=refusals,
        model_used=state.get("model_used") or None,
    )


def record_chat_outcome(
    ctx: UserContext,
    request: ChatRequest,
    response: ChatResponse,
    *,
    latency_ms: int,
    graph_state: dict[str, Any] | None = None,
) -> None:
    """Persist feedback correlation + audit row for a completed chat."""
    stage_trace = build_stage_trace(graph_state) if graph_state else None
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
        answer_preview=response.answer,
        stage_trace=stage_trace,
    )


def run_chat(ctx: UserContext, request: ChatRequest) -> ChatResponse:
    """Execute the full graph synchronously with a hard deadline."""
    cfg = get_settings()
    assert_agent_enabled(agent_enabled=cfg.agent_enabled)
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
    response = state_to_response(result)
    record_chat_outcome(
        ctx,
        request,
        response,
        latency_ms=latency_ms,
        graph_state=result,
    )
    return response


def _iter_stream_chunks(chunk: object) -> list[tuple[str, dict[str, Any]]]:
    """Normalize LangGraph stream items into ``(mode, payload)`` pairs."""
    if isinstance(chunk, tuple) and len(chunk) == 2 and isinstance(chunk[0], str):
        mode, payload = chunk
        if mode == "updates" and isinstance(payload, dict):
            return [(mode, payload)]
        if mode == "custom" and isinstance(payload, dict):
            return [(mode, payload)]
        return []

    if isinstance(chunk, dict):
        return [("updates", chunk)]
    return []


def _pipeline_events_for_node(
    tracker: PipelineTracker,
    node_name: str,
    update: dict[str, Any],
    *,
    router_started: bool,
) -> tuple[list[dict[str, Any]], bool]:
    """Emit structured ``pipeline`` events for the router step."""
    events: list[dict[str, Any]] = []
    step_key = map_node_to_step_key(node_name)
    if step_key != "router":
        return events, router_started

    if not router_started:
        events.append(
            {
                "event": "pipeline",
                "data": tracker.start_event(step_key, node=node_name),
            }
        )
        router_started = True

    departments = list(update.get("target_departments") or [])
    events.append(
        {
            "event": "pipeline",
            "data": tracker.end_event(
                step_key,
                node=node_name,
                departments=departments,
            ),
        }
    )
    return events, router_started


def stream_chat(ctx: UserContext, request: ChatRequest) -> Iterator[dict[str, Any]]:
    """Stream LangGraph node updates as SSE-friendly event dicts."""
    cfg = get_settings()
    assert_agent_enabled(agent_enabled=cfg.agent_enabled)
    graph = get_compiled_graph()
    started = time.perf_counter()
    tracker = PipelineTracker(started)

    yield {"event": "start", "data": {"question": request.question}}

    final_state: dict[str, Any] = {}
    router_started = False
    try:
        for chunk in graph.stream(
            _initial_state(ctx, request, cfg),
            _graph_config(ctx),
            stream_mode=["updates", "custom"],
        ):
            for mode, payload in _iter_stream_chunks(chunk):
                if mode == "custom":
                    yield {"event": "pipeline", "data": payload}
                    continue

                for node_name, update in payload.items():
                    if isinstance(update, dict):
                        final_state.update(update)
                    elapsed_ms = int((time.perf_counter() - started) * 1000)
                    node_data = build_node_event_data(
                        node_name,
                        update if isinstance(update, dict) else None,
                        elapsed_ms=elapsed_ms,
                        accumulated=final_state,
                    )
                    yield {"event": "node", "data": node_data}

                    if isinstance(update, dict):
                        pipeline_events, router_started = _pipeline_events_for_node(
                            tracker,
                            node_name,
                            update,
                            router_started=router_started,
                        )
                        yield from pipeline_events
    except Exception as exc:
        logger.exception("Graph stream failed")
        yield {"event": "error", "data": {"detail": str(exc)}}
        return

    # If the respond node did not emit an answer via the stream updates (e.g. it
    # wrote only to the root state snapshot), load the final state from the
    # checkpointer rather than re-invoking the full graph.  Re-invoking with a
    # fresh _initial_state resets the conversation context and can trigger a
    # second expensive pipeline run on top of whatever the checkpointer saved.
    if not final_state.get("answer"):
        try:
            snapshot = graph.get_state(_graph_config(ctx))
            if snapshot and snapshot.values:
                final_state = {**snapshot.values, **final_state}
        except Exception as exc:
            logger.error("stream_chat get_state fallback failed: %s", exc, exc_info=True)

    response = state_to_response(final_state)
    latency_ms = int((time.perf_counter() - started) * 1000)
    record_chat_outcome(
        ctx,
        request,
        response,
        latency_ms=latency_ms,
        graph_state=final_state,
    )

    yield {"event": "done", "data": response.model_dump()}
