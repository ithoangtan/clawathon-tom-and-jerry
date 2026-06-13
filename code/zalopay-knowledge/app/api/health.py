from __future__ import annotations

"""Liveness and readiness probes (G5 / DevOps MUST)."""

import logging
from typing import Any

from app.adapters.deps import get_deps
from app.config import get_settings

logger = logging.getLogger(__name__)


def _maas_reachable() -> bool:
    """Return True when MaaS responds within the configured ping budget."""
    llm = get_deps().llm
    ping = getattr(llm, "is_reachable", None)
    if not callable(ping):
        logger.warning("LLM adapter has no is_reachable(); treating MaaS as unavailable")
        return False
    try:
        return bool(ping(timeout_s=get_settings().health_ping_timeout_s))
    except Exception as exc:  # noqa: BLE001 — probe must never raise
        logger.warning("MaaS readiness check failed: %s", exc)
        return False


def probe_liveness() -> dict[str, Any]:
    """Fast liveness check — no MaaS ping, always safe to call."""
    cfg = get_settings()
    try:
        index_ready = get_deps().retriever.is_ready()
    except Exception:  # noqa: BLE001 — liveness must never raise
        index_ready = False
    return {
        "status": "healthy",
        "version": cfg.app_version,
        "index_ready": index_ready,
        "maas_ready": False,
        "ready": False,
        "config": {
            "small_model": cfg.small_model,
            "main_model": cfg.main_model,
            "embedding_model": cfg.embedding_model,
            "grade_threshold": cfg.grade_threshold,
            "topk": cfg.topk,
            "route_confidence_min": cfg.route_confidence_min,
        },
    }


def probe_status() -> dict[str, Any]:
    """Full readiness check — includes MaaS ping (may be slow)."""
    cfg = get_settings()
    retriever = get_deps().retriever
    index_ready = retriever.is_ready()
    maas_ready = _maas_reachable()
    return {
        "status": "healthy",
        "version": cfg.app_version,
        "index_ready": index_ready,
        "maas_ready": maas_ready,
        "ready": index_ready and maas_ready,
        "config": {
            "small_model": cfg.small_model,
            "main_model": cfg.main_model,
            "embedding_model": cfg.embedding_model,
            "grade_threshold": cfg.grade_threshold,
            "topk": cfg.topk,
            "route_confidence_min": cfg.route_confidence_min,
        },
    }


def is_live() -> bool:
    """Process is up — always true while the handler runs."""
    return True


def is_ready() -> bool:
    """Traffic-ready: FAISS index loaded and MaaS reachable."""
    status = probe_status()
    return bool(status["index_ready"] and status["maas_ready"])
