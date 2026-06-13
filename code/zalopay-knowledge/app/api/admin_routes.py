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
            message = f"Confluence sync for {body.department} started in background"
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


@router.get("/sync/history", response_model=AdminSyncHistoryResponse)
def admin_sync_history(
    source: str | None = Query(default=None, pattern="^(confluence|gdrive)$"),
    limit: int = Query(default=10, ge=1, le=20),
) -> AdminSyncHistoryResponse:
    svc = get_sync_service()
    entries = svc.orchestrator.history_snapshot(source=source, limit=limit)
    return AdminSyncHistoryResponse(entries=entries)
