from __future__ import annotations

"""FastAPI route definitions."""

import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.adapters.deps import get_deps
from app.api.context import UserContext, require_user_context
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    DashboardData,
    FeedbackRequest,
    HealthInfo,
    SyncStartResponse,
    SyncStatusResponse,
    SourceStatus,
)
from app.api.service import (
    get_audit_store,
    get_feedback_store,
    record_chat_outcome,
    run_chat,
    stream_chat,
)
from app.config import get_settings
from app.ingestion.orchestrator import SyncService

logger = logging.getLogger(__name__)

router = APIRouter()

_sync_service: SyncService | None = None


def get_sync_service() -> SyncService:
    global _sync_service
    if _sync_service is None:
        _sync_service = SyncService()
    return _sync_service


@router.get("/health", response_model=HealthInfo)
def health() -> HealthInfo:
    cfg = get_settings()
    retriever = get_deps().retriever
    return HealthInfo(
        status="healthy",
        version=cfg.app_version,
        index_ready=retriever.is_ready(),
        config={
            "small_model": cfg.small_model,
            "main_model": cfg.main_model,
            "embedding_model": cfg.embedding_model,
            "grade_threshold": cfg.grade_threshold,
            "topk": cfg.topk,
            "route_confidence_min": cfg.route_confidence_min,
        },
    )


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, ctx: UserContext = Depends(require_user_context)) -> ChatResponse:
    deps = get_deps()
    if not deps.retriever.is_ready():
        raise HTTPException(status_code=503, detail="Knowledge base not ready — please sync first")
    started = time.perf_counter()
    try:
        response = run_chat(ctx, body)
    except TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout") from None
    record_chat_outcome(
        ctx,
        body,
        response,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
    return response


@router.post("/invocations", response_model=ChatResponse)
def invocations(body: ChatRequest, ctx: UserContext = Depends(require_user_context)) -> ChatResponse:
    return chat(body, ctx)


@router.post("/chat/stream")
def chat_stream(body: ChatRequest, ctx: UserContext = Depends(require_user_context)):
    deps = get_deps()
    if not deps.retriever.is_ready():
        raise HTTPException(status_code=503, detail="Knowledge base not ready — please sync first")

    def event_generator():
        for item in stream_chat(ctx, body):
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/feedback", status_code=204)
def feedback(
    body: FeedbackRequest,
    ctx: UserContext = Depends(require_user_context),
) -> Response:
    store = get_feedback_store()
    ok = store.submit(
        feedback_id=body.feedback_id,
        user_id=ctx.user_id,
        rating=body.rating,
        comment=body.comment,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="feedback_id not found")
    return Response(status_code=204)


@router.post("/sync/confluence")
def sync_confluence(ctx: UserContext = Depends(require_user_context)) -> JSONResponse:
    _ = ctx
    svc = get_sync_service()
    started = svc.trigger_confluence()
    payload = SyncStartResponse(
        source="confluence",
        started=started,
        message=(
            "Confluence sync started in background"
            if started
            else "Confluence sync already running"
        ),
    )
    code = status.HTTP_202_ACCEPTED if started else status.HTTP_409_CONFLICT
    return JSONResponse(status_code=code, content=payload.model_dump())


@router.post("/sync/gdrive")
def sync_gdrive(ctx: UserContext = Depends(require_user_context)) -> JSONResponse:
    _ = ctx
    svc = get_sync_service()
    started = svc.trigger_gdrive()
    payload = SyncStartResponse(
        source="gdrive",
        started=started,
        message=(
            "Google Drive sync started in background"
            if started
            else "Google Drive sync already running"
        ),
    )
    code = status.HTTP_202_ACCEPTED if started else status.HTTP_409_CONFLICT
    return JSONResponse(status_code=code, content=payload.model_dump())


@router.get("/sync/status", response_model=SyncStatusResponse)
def sync_status() -> SyncStatusResponse:
    svc = get_sync_service()
    sources = [SourceStatus(**s) for s in svc.orchestrator.status_snapshot()]
    return SyncStatusResponse(sources=sources)


@router.get("/api/dashboard", response_model=DashboardData)
def dashboard() -> DashboardData:
    metrics = get_audit_store().dashboard_metrics()
    up, down = get_feedback_store().counts()
    metrics["feedback_up"] = up
    metrics["feedback_down"] = down
    return DashboardData(**metrics)
