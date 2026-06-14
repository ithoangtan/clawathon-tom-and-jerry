from __future__ import annotations

"""FastAPI route definitions (chat, sync, dashboard).

Health probes live in ``app.api.app.register_health_routes`` — not here.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.adapters.deps import get_deps
from app.api.context import UserContext, require_user_context
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    DashboardData,
    FeedbackRequest,
    SourceStatus,
    SyncStartResponse,
    SyncStatusResponse,
)
from app.api.service import (
    get_audit_store,
    get_feedback_store,
    run_chat,
    stream_chat,
)
from app.ingestion.orchestrator import SyncService
from app.metrics import load_eval_snapshot, merge_dashboard_metrics

logger = logging.getLogger(__name__)

router = APIRouter()

_sync_service: SyncService | None = None


def get_sync_service() -> SyncService:
    global _sync_service
    if _sync_service is None:
        _sync_service = SyncService()
    return _sync_service


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, ctx: UserContext = Depends(require_user_context)) -> ChatResponse:
    deps = get_deps()
    if not deps.retriever.is_ready():
        raise HTTPException(status_code=503, detail="Knowledge base not ready — please sync first")
    try:
        return run_chat(ctx, body)
    except TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout") from None


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
    audit = get_audit_store().dashboard_metrics()
    up, down = get_feedback_store().counts()
    metrics = merge_dashboard_metrics(
        audit,
        feedback_up=up,
        feedback_down=down,
        eval_snapshot=load_eval_snapshot(),
    )
    return DashboardData(**metrics)


@router.get("/api/knowledge-gaps")
def knowledge_gaps() -> JSONResponse:
    """Return refused questions and low-rated documents for the Admin gap tracker."""
    refused = get_audit_store().refused_questions(limit=20, days=30)
    low_rated = get_feedback_store().feedback_gaps(limit=20)
    return JSONResponse(content={"refused_questions": refused, "low_rated_docs": low_rated})
