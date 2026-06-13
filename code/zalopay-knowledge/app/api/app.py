from __future__ import annotations

"""FastAPI application factory.

Single ``create_app()`` used by tests, ``main.py``, and uvicorn. Production
entrypoint (``main.py``) registers AgentBase handlers after calling this.

Health probes (liveness vs readiness) are registered here — not on the main API
router — so orchestrators can target ``/health/ready`` independently of chat.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import is_live, is_ready, probe_status
from app.api.spa_static import SPAStaticFiles
from app.api.middleware import GatewayTrustMiddleware, KillSwitchMiddleware
from app.api.routes import router
from app.api.schemas import HealthInfo
from app.common.logging_config import setup_logging
from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    cfg = get_settings()
    logger.info("Starting zalopay-knowledge v%s (env=%s)", cfg.app_version, cfg.app_env)
    from app.adapters.deps import get_deps
    from app.api.service import get_audit_store, get_feedback_store

    get_deps()
    get_audit_store().ensure_schema()
    get_feedback_store().ensure_schema()
    yield
    logger.info("Shutting down")


def register_health_routes(app: FastAPI) -> None:
    """Mount liveness/readiness probes (DevOps MUST §3 — separate from liveness)."""

    @app.get("/health", response_model=HealthInfo, tags=["health"])
    def health() -> HealthInfo:
        """Process snapshot — always 200 while HTTP server is up."""
        if not is_live():
            raise HTTPException(status_code=503, detail="Process not live")
        return HealthInfo(**probe_status())

    @app.get("/health/live", response_model=HealthInfo, tags=["health"])
    def health_live() -> HealthInfo:
        """Liveness — always 200 while accepting requests (no index/MaaS gate)."""
        return HealthInfo(**probe_status())

    @app.get("/health/ready", response_model=HealthInfo, tags=["health"])
    def health_ready(response: Response) -> HealthInfo:
        """Readiness — FAISS loaded + MaaS ping; 503 until traffic-ready."""
        payload = probe_status()
        if not is_ready():
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthInfo(**payload)


def create_app() -> FastAPI:
    cfg = get_settings()
    app = FastAPI(
        title="Zalopay Knowledge Agent",
        version=cfg.app_version,
        description="Citation-grounded internal knowledge assistant",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Security runs after CORS in the stack (executes before routes on ingress).
    app.add_middleware(GatewayTrustMiddleware)
    app.add_middleware(KillSwitchMiddleware)

    register_health_routes(app)
    app.include_router(router)

    from app.api.admin_routes import router as admin_router

    app.include_router(admin_router)

    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if dist.is_dir():
        app.mount("/", SPAStaticFiles(directory=str(dist), html=True), name="frontend")

    return app
