from __future__ import annotations

"""Security middleware — gateway trust and kill-switch."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.common.security import validate_gateway_trust
from app.config import get_settings

logger = logging.getLogger(__name__)

# Paths that stay available when the agent is disabled.
_KILL_SWITCH_ALLOWLIST = frozenset(
    {
        "/health",
        "/health/live",
        "/health/ready",
        "/sync/status",
        "/api/dashboard",
        "/api/admin/sync/status",
        "/api/admin/sync/history",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
)


def _is_agent_route(path: str) -> bool:
    if path in _KILL_SWITCH_ALLOWLIST:
        return False
    if path == "/" or path.startswith("/assets/"):
        return False
    return True


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request: method, path, status code, and latency.

    Errors (5xx) are logged at ERROR level so they surface clearly in monitor.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(
                "UNHANDLED EXCEPTION %s %s (%dms) — %s: %s",
                request.method,
                request.url.path,
                latency_ms,
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            raise

        latency_ms = int((time.perf_counter() - start) * 1000)
        status = response.status_code
        if status >= 500:
            logger.error(
                "%s %s → %d (%dms)",
                request.method,
                request.url.path,
                status,
                latency_ms,
            )
        elif status >= 400:
            logger.warning(
                "%s %s → %d (%dms)",
                request.method,
                request.url.path,
                status,
                latency_ms,
            )
        else:
            logger.info(
                "%s %s → %d (%dms)",
                request.method,
                request.url.path,
                status,
                latency_ms,
            )
        return response


class GatewayTrustMiddleware(BaseHTTPMiddleware):
    """Reject spoofed AgentBase identity headers before route handlers run."""

    async def dispatch(self, request: Request, call_next) -> Response:
        cfg = get_settings()
        if not cfg.gateway_trust_required:
            return await call_next(request)

        error = validate_gateway_trust(
            request.headers,
            trust_required=True,
            trust_secret=cfg.gateway_trust_secret,
        )
        if error:
            logger.warning(
                "Gateway trust rejected request path=%s remote=%s",
                request.url.path,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(status_code=403, content={"detail": error})
        return await call_next(request)


class KillSwitchMiddleware(BaseHTTPMiddleware):
    """Instantly disable chat/sync when ``AGENT_ENABLED=false``."""

    async def dispatch(self, request: Request, call_next) -> Response:
        cfg = get_settings()
        if cfg.agent_enabled or not _is_agent_route(request.url.path):
            return await call_next(request)

        logger.warning("Kill-switch active — rejected path=%s", request.url.path)
        return JSONResponse(
            status_code=503,
            content={"detail": "Knowledge agent is temporarily disabled"},
        )
