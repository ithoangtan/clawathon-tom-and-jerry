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
        from app.api.service import record_chat_outcome, run_chat

        agentbase_app = GreenNodeAgentBaseApp()

        @agentbase_app.entrypoint
        def agentbase_handler(payload: dict, context: RequestContext) -> dict:
            headers = dict(context.request_headers or {})
            if context.user_id:
                headers["X-GreenNode-AgentBase-User-Id"] = context.user_id
            if context.session_id:
                headers["X-GreenNode-AgentBase-Session-Id"] = context.session_id
            try:
                user_ctx = parse_context_from_headers(headers)
            except ValueError as exc:
                return {"status": "error", "error": str(exc)}
            question = payload.get("question") or payload.get("message", "")
            req = ChatRequest(
                question=question,
                target_departments=payload.get("target_departments"),
            )
            import time

            started = time.perf_counter()
            response = run_chat(user_ctx, req)
            record_chat_outcome(
                user_ctx,
                req,
                response,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
            return response.model_dump()

        @agentbase_app.ping
        def agentbase_ping() -> PingStatus:
            from app.adapters.deps import get_deps

            return (
                PingStatus.HEALTHY
                if get_deps().retriever.is_ready()
                else PingStatus.UNHEALTHY
            )

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
