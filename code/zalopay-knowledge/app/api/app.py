from __future__ import annotations

"""FastAPI application factory.

Single ``create_app()`` used by tests, ``main.py``, and uvicorn. Production
entrypoint (``main.py``) registers AgentBase handlers after calling this.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
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
    app.include_router(router)

    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")

    return app
