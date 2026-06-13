from __future__ import annotations

"""Application entrypoint — FastAPI server on port 8080."""

import logging

from app.api.app import create_app
from app.config import get_settings

logger = logging.getLogger(__name__)

app = create_app()


if get_settings().is_agentbase:
    try:
        from greennode_agentbase import GreenNodeAgentBaseApp, PingStatus, RequestContext

        from app.api.context import parse_context_from_headers
        from app.api.schemas import ChatRequest
        from app.api.service import run_chat
        from app.common.security import AgentDisabledError, apply_gateway_trust_headers

        agentbase_app = GreenNodeAgentBaseApp()
        cfg = get_settings()

        @agentbase_app.entrypoint
        def agentbase_handler(payload: dict, context: RequestContext) -> dict:
            if not cfg.agent_enabled:
                return {
                    "status": "error",
                    "error": "Knowledge agent is temporarily disabled",
                }
            headers = dict(context.request_headers or {})
            if context.user_id:
                headers["X-GreenNode-AgentBase-User-Id"] = context.user_id
            if context.session_id:
                headers["X-GreenNode-AgentBase-Session-Id"] = context.session_id
            if context.user_id and context.session_id:
                apply_gateway_trust_headers(
                    headers,
                    user_id=context.user_id,
                    session_id=context.session_id,
                    trust_secret=cfg.gateway_trust_secret,
                )
            try:
                user_ctx = parse_context_from_headers(headers)
            except ValueError as exc:
                return {"status": "error", "error": str(exc)}
            question = payload.get("question") or payload.get("message", "")
            req = ChatRequest(
                question=question,
                target_departments=payload.get("target_departments"),
            )
            try:
                response = run_chat(user_ctx, req)
            except AgentDisabledError as exc:
                return {"status": "error", "error": str(exc)}
            return response.model_dump()

        @agentbase_app.ping
        def agentbase_ping() -> PingStatus:
            from app.api.health import is_ready

            return PingStatus.HEALTHY if is_ready() else PingStatus.UNHEALTHY

        logger.info("AgentBase SDK handlers registered")
    except ImportError:
        logger.warning(
            "APP_ENV=agentbase but greennode-agentbase is not installed"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=get_settings().is_local,
    )
