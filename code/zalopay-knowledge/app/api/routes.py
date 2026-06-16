from __future__ import annotations

"""FastAPI route definitions (chat, sync, dashboard).

Health probes live in ``app.api.app.register_health_routes`` — not here.
"""

import json
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

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
from app.store.session_store import SessionStore

logger = logging.getLogger(__name__)

router = APIRouter()

_sync_service: SyncService | None = None
_session_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store


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


_CURATED_QUESTIONS = {
    "en": [
        "What fraud detection models does Zalopay use in its e-wallet ecosystem?",
        "How does the Lucky Wheel campaign work and what are its v2 configuration steps?",
        "What are the commercial terms and revenue sharing models for bank partnerships?",
    ],
    "vi": [
        "Mô hình phát hiện gian lận trong hệ sinh thái ví điện tử của Zalopay hoạt động như thế nào?",
        "Các bước cấu hình và vận hành chiến dịch Lucky Wheel v2 là gì?",
        "Điều khoản thương mại và mô hình chia sẻ doanh thu trong quan hệ đối tác ngân hàng gồm những gì?",
    ],
}


@router.get("/api/suggested-questions")
def suggested_questions(lang: str = "vi") -> JSONResponse:
    """Return top 3 most frequently asked questions for the chat empty state.

    Falls back to curated starter questions when audit history is empty,
    ensuring suggestions are always grounded in actual indexed documents.
    """
    questions = get_audit_store().popular_questions(limit=3)
    if not questions:
        locale = lang if lang in _CURATED_QUESTIONS else "vi"
        questions = _CURATED_QUESTIONS[locale]
    return JSONResponse(content={"questions": questions})


@router.get("/api/knowledge-gaps")
def knowledge_gaps() -> JSONResponse:
    """Return refused questions and low-rated documents for the Admin gap tracker."""
    refused = get_audit_store().refused_questions(limit=20, days=30)
    low_rated = get_feedback_store().feedback_gaps(limit=20)
    return JSONResponse(content={"refused_questions": refused, "low_rated_docs": low_rated})


# ── Admin: test email ────────────────────────────────────────────────────────

class _TestEmailBody(BaseModel):
    to: str
    subject: str
    body: str


@router.get("/api/admin/gmail-status")
def admin_gmail_status() -> JSONResponse:
    """Check Gmail auth status. Returns ok / need_auth (with auth_url) / not_configured."""
    from app.config import get_settings
    from app.adapters.identity_client import identity_runtime_ready
    cfg = get_settings()

    # Local refresh_token path
    if cfg.gmail_refresh_token and cfg.gmail_client_id and cfg.gmail_client_secret:
        return JSONResponse({"status": "ok", "method": "refresh_token"})

    # AgentBase 3LO path
    if identity_runtime_ready(cfg):
        try:
            from greennode_agentbase.identity import Get3loTokenRequest
            from app.adapters.identity_client import get_identity_client
            from app.adapters.gmail_sender import GMAIL_SEND_SCOPE
            client = get_identity_client()
            result = client.get_3lo_token(
                provider_name="identity-google-space",
                agent_identity_name="identity-google-space",
                request=Get3loTokenRequest(
                    agent_user_id="itk160454@gmail.com",
                    scopes=[GMAIL_SEND_SCOPE],
                ),
            )
            token = (getattr(result, "access_token", None) or "").strip()
            if token:
                return JSONResponse({"status": "ok", "method": "agentbase_3lo"})
            auth_url = (getattr(result, "authorization_url", None) or "").strip()
            if auth_url:
                return JSONResponse({"status": "need_auth", "auth_url": auth_url})
            return JSONResponse({"status": "failed", "detail": "No token and no auth URL returned."})
        except Exception as exc:
            return JSONResponse({"status": "failed", "detail": str(exc)})

    return JSONResponse({"status": "not_configured",
                         "detail": "Chưa cấu hình Gmail. Cần APP_ENV=agentbase + GREENNODE_AGENT_IDENTITY, hoặc GMAIL_REFRESH_TOKEN + GMAIL_CLIENT_ID + GMAIL_CLIENT_SECRET."})


@router.post("/api/admin/test-email")
def admin_test_email(payload: _TestEmailBody) -> JSONResponse:
    """Send a plain-text test email to verify the current Gmail token."""
    from app.adapters.gmail_sender import send_email
    from app.config import get_settings
    cfg = get_settings()
    html_body = f"<pre style='font-family:sans-serif'>{payload.body}</pre>"
    ok = send_email(to=payload.to, subject=payload.subject, body_html=html_body, settings=cfg)
    if ok:
        return JSONResponse({"status": "sent"})
    return JSONResponse({"status": "failed", "detail": "Check server logs for Gmail error."}, status_code=502)


# ── Shared session threads ────────────────────────────────────────────────────

@router.get("/api/sessions")
def list_sessions() -> JSONResponse:
    """Return all shared chat session threads ordered by updated_at DESC."""
    threads = get_session_store().list_all()
    return JSONResponse(content={"threads": threads})


@router.put("/api/sessions/{session_id}", status_code=204)
def upsert_session(session_id: str, body: dict = Body(...)) -> Response:
    """Create or update a session thread."""
    body["sessionId"] = session_id
    get_session_store().upsert(body)
    return Response(status_code=204)


@router.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(session_id: str) -> Response:
    """Delete a session thread."""
    get_session_store().delete(session_id)
    return Response(status_code=204)
