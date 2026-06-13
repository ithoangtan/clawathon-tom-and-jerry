from __future__ import annotations

"""Admin sync API — trigger jobs and inspect detailed status/history."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.api.context import UserContext, require_user_context
from app.api.routes import get_sync_service
from app.api.schemas import (
    AdminSyncHistoryResponse,
    AdminSyncRequest,
    AdminSyncStartResponse,
    AdminSyncStatusResponse,
)
from app.common.departments import get_department
from app.config import Settings, get_settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/sync")
def admin_sync(
    body: AdminSyncRequest,
    ctx: UserContext = Depends(require_user_context),
) -> JSONResponse:
    _ = ctx
    svc = get_sync_service()
    orch = svc.orchestrator

    if body.source == "confluence":
        try:
            started = svc.trigger_confluence(department=body.department)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    elif body.source == "gdrive":
        if body.department:
            raise HTTPException(
                status_code=400,
                detail="department filter is only supported for confluence sync",
            )
        started = svc.trigger_gdrive()
    else:
        raise HTTPException(status_code=400, detail="Unsupported sync source")

    running_job_id = orch.current_job_id(body.source) if started else None

    if started:
        message = f"{body.source} sync started in background"
        if body.department:
            dept_name = get_department(body.department).display_name()
            message = f"Confluence sync for {dept_name} started in background"
        code = status.HTTP_202_ACCEPTED
    else:
        message = f"{body.source} sync already running"
        code = status.HTTP_409_CONFLICT

    payload = AdminSyncStartResponse(
        source=body.source,
        department=body.department,
        started=started,
        job_id=running_job_id,
        message=message,
    )
    return JSONResponse(status_code=code, content=payload.model_dump())


@router.get("/sync/status", response_model=AdminSyncStatusResponse)
def admin_sync_status() -> AdminSyncStatusResponse:
    svc = get_sync_service()
    snapshot = svc.orchestrator.admin_status_snapshot()
    return AdminSyncStatusResponse(**snapshot)


@router.get("/gdrive/authorize")
def gdrive_authorize(settings: Settings = Depends(get_settings)) -> JSONResponse:
    """Initiate or check Google Drive 3LO authorization.

    Returns {"status": "authorized"} when Drive is already authorized.
    Returns {"status": "pending", "authorization_url": "..."} when the admin
    must open the URL in a browser and click Allow to grant access.
    """
    if not settings.is_agentbase:
        raise HTTPException(status_code=400, detail="Only available in AgentBase runtime")

    provider = (settings.gdrive_oauth_provider or "").strip()
    identity = (settings.greennode_agent_identity or "").strip()
    if not provider or not identity:
        raise HTTPException(
            status_code=400,
            detail="GDRIVE_OAUTH_PROVIDER or GREENNODE_AGENT_IDENTITY not configured",
        )

    try:
        from greennode_agentbase.identity import Get3loTokenRequest

        from app.adapters.identity_client import get_identity_client

        client = get_identity_client()
        result = client.get_3lo_token(
            provider_name=provider,
            agent_identity_name=identity,
            request=Get3loTokenRequest(
                agent_user_id=settings.gdrive_oauth_agent_user_id,
                scopes=settings.gdrive_oauth_scope_list,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    access_token = (getattr(result, "access_token", None) or "").strip()
    if access_token:
        return JSONResponse({"status": "authorized"})

    auth_url = getattr(result, "authorization_url", None)
    if auth_url:
        return JSONResponse({"status": "pending", "authorization_url": auth_url})

    raise HTTPException(status_code=502, detail="AgentBase returned neither token nor auth URL")


@router.get("/sync/history", response_model=AdminSyncHistoryResponse)
def admin_sync_history(
    source: str | None = Query(default=None, pattern="^(confluence|gdrive)$"),
    limit: int = Query(default=10, ge=1, le=20),
) -> AdminSyncHistoryResponse:
    svc = get_sync_service()
    entries = svc.orchestrator.history_snapshot(source=source, limit=limit)
    return AdminSyncHistoryResponse(entries=entries)
