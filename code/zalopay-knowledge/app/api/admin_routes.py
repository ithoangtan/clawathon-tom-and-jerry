from __future__ import annotations

"""Admin sync API — trigger jobs and inspect detailed status/history."""

import logging

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

logger = logging.getLogger(__name__)

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


@router.post("/reindex")
def admin_reindex(ctx: UserContext = Depends(require_user_context)) -> JSONResponse:
    """Force full re-index: clear sync_sources cache + delete OpenSearch indexes.

    Use this after changing the embedding model (same or different dimension).
    After this call, trigger a full sync via POST /api/admin/sync to re-embed
    all documents with the new model.

    What this does:
    1. Deletes all rows in sync_sources (clears content-hash dedup cache).
    2. Deletes all OpenSearch department indexes (removes stale vectors).

    The next sync will re-embed every document from scratch.
    """
    _ = ctx
    cfg = get_settings()

    deleted_indexes: list[str] = []
    cleared_sources: int = 0

    # Step 1 — clear sync_sources so the next sync re-processes every doc
    try:
        if cfg.db_host and cfg.db_user:
            from app.store.db import get_connection

            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM sync_sources")
                    cleared_sources = cur.rowcount
                conn.commit()
            finally:
                conn.close()
            logger.info("admin_reindex: cleared %d rows from sync_sources", cleared_sources)
        else:
            # FAISS / SQLite mode
            from app.config import get_settings as _cfg
            from pathlib import Path
            from app.store.meta import MetaStore

            index_dir = Path(cfg.index_dir)
            meta = MetaStore(index_dir / "meta.db")
            from app.common.departments import iter_keys
            for dept in iter_keys():
                meta.clear_department(dept)
            logger.info("admin_reindex: cleared MetaStore sync sources")
    except Exception as exc:
        logger.error("admin_reindex: failed to clear sync_sources: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to clear sync cache: {exc}") from exc

    # Step 2 — delete OpenSearch indexes so stale vectors are gone
    if cfg.vector_store == "opensearch" and cfg.opensearch_host:
        try:
            from opensearchpy import OpenSearch
            from app.common.departments import iter_keys

            client = OpenSearch(
                hosts=[{"host": cfg.opensearch_host, "port": cfg.opensearch_port}],
                http_auth=(cfg.opensearch_user, cfg.opensearch_password),
                use_ssl=cfg.opensearch_use_ssl,
                verify_certs=cfg.opensearch_verify_certs,
                ssl_show_warn=False,
            )
            prefix = cfg.opensearch_index_prefix
            for dept in iter_keys():
                index = f"{prefix}_{dept}"
                if client.indices.exists(index=index):
                    client.indices.delete(index=index)
                    deleted_indexes.append(index)
                    logger.info("admin_reindex: deleted OpenSearch index %s", index)
        except Exception as exc:
            logger.error("admin_reindex: failed to delete OpenSearch indexes: %s", exc)
            raise HTTPException(
                status_code=500,
                detail=f"Sync cache cleared but failed to delete vector indexes: {exc}",
            ) from exc

    return JSONResponse(
        status_code=200,
        content={
            "cleared_sync_sources": cleared_sources,
            "deleted_indexes": deleted_indexes,
            "message": (
                f"Re-index prepared: cleared {cleared_sources} sync cache rows"
                + (f", deleted {len(deleted_indexes)} vector index(es)" if deleted_indexes else "")
                + ". Trigger a full sync to re-embed all documents."
            ),
        },
    )


@router.get("/sync/history", response_model=AdminSyncHistoryResponse)
def admin_sync_history(
    source: str | None = Query(default=None, pattern="^(confluence|gdrive)$"),
    limit: int = Query(default=10, ge=1, le=20),
) -> AdminSyncHistoryResponse:
    svc = get_sync_service()
    entries = svc.orchestrator.history_snapshot(source=source, limit=limit)
    return AdminSyncHistoryResponse(entries=entries)
