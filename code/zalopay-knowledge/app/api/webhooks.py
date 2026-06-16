from __future__ import annotations

"""Inbound webhook routes — currently the Jira Automation callback.

``POST /webhooks/jira`` receives a Jira Automation "Send web request" call when a
ticket changes (status / comment / field). It is intentionally **not** behind the
AgentBase identity dependency (Jira sends no ``X-GreenNode-AgentBase-*`` headers,
so ``GatewayTrustMiddleware`` lets it through); instead it authenticates with a
shared secret header.

S1 scope: authenticate, normalise the event, drop self-triggered + duplicate
events, and log/acknowledge. Reacting to events (matching the workflow page's
``## Triggers`` and running actions) is S2.
"""

import hmac
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Header, Request, Response, status

from app.config import get_settings
from app.integrations.jira_events import EventDeduper, JiraEvent, is_self_event, normalize_jira_event

logger = logging.getLogger(__name__)

webhook_router = APIRouter(tags=["webhooks"])

# Process-local dedup (single-replica demo). See EventDeduper docstring for the
# multi-replica production note.
_deduper = EventDeduper()


def _process_event(event: JiraEvent) -> None:
    """Background worker: resolve workflow → match trigger → run action.

    Runs after the 200 ack so Jira does not time out / retry. Builds deps lazily
    and never raises (handler degrades to a structured result). Indirected here
    so tests can monkeypatch it to avoid heavy deps / network.

    Creates a session in the DB before processing so the chat UI sidebar
    shows a "Đang xử lý..." entry immediately. Updates status to "done" or
    "error" after the handler completes.
    """
    import uuid
    from app.adapters.deps import get_deps
    from app.api.routes import get_session_store
    from app.integrations.jira_handler import handle_jira_event
    from app.workflow.labels import WORKFLOW_LABEL_PREFIX
    from app.workflow.registry import WORKFLOW_REGISTRY

    # Determine workflow slug from event labels eagerly (before full jira fetch).
    # We'll update the session title once we have the real issue summary.
    session_id = str(uuid.uuid4())
    session_store = get_session_store()

    # Detect in-code workflow slug from event raw payload labels if available.
    raw_labels: list[str] = []
    if event.raw:
        issue_fields = (event.raw.get("issue") or {}).get("fields") or {}
        raw_labels = issue_fields.get("labels") or []
    wf_label = next((lbl for lbl in raw_labels if lbl.startswith(WORKFLOW_LABEL_PREFIX)), None)
    slug = wf_label[len(WORKFLOW_LABEL_PREFIX):] if wf_label else ""
    workflow_id = slug if slug in WORKFLOW_REGISTRY else (slug or "unknown")

    try:
        session_store.create_processing_session(
            session_id=session_id,
            title=f"[{event.issue_key}] Campaign Risk Review",
            workflow_id=workflow_id,
            jira_key=event.issue_key,
        )
    except Exception:  # noqa: BLE001
        logger.warning("Could not create processing session for %s", event.issue_key)

    try:
        deps = get_deps()
        result = handle_jira_event(
            event,
            llm=deps.llm,
            retriever=deps.retriever,
            jira=deps.jira,
            confluence_writer=deps.confluence_writer,
            settings=deps.settings,
        )
        logger.info("Jira webhook processed %s → %s", event.issue_key, result.get("status"))
        final_status = "done" if result.get("status") not in ("error",) else "error"
    except Exception:  # noqa: BLE001 — background work must never crash the worker
        logger.exception("Jira webhook background processing failed for %s", event.issue_key)
        final_status = "error"

    try:
        session_store.update_processing_status(session_id, final_status)
    except Exception:  # noqa: BLE001
        logger.warning("Could not update processing status for session %s", session_id)


@webhook_router.post("/webhooks/jira")
async def jira_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
) -> Response:
    """Authenticate, normalise, dedupe and acknowledge a Jira change event."""
    cfg = get_settings()

    # ── Auth: shared secret ───────────────────────────────────────────────────
    configured = (cfg.jira_webhook_secret or "").strip()
    if not configured:
        # Endpoint disabled until a secret is set — fail closed.
        return _json(status.HTTP_503_SERVICE_UNAVAILABLE, {"detail": "Jira webhook not configured"})
    if not x_webhook_secret or not hmac.compare_digest(x_webhook_secret, configured):
        logger.warning("Jira webhook: rejected (bad/missing X-Webhook-Secret)")
        return _json(status.HTTP_401_UNAUTHORIZED, {"detail": "invalid webhook secret"})

    # ── Body ──────────────────────────────────────────────────────────────────
    try:
        payload = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return _json(status.HTTP_400_BAD_REQUEST, {"detail": "invalid JSON body"})
    if not isinstance(payload, dict):
        return _json(status.HTTP_400_BAD_REQUEST, {"detail": "expected a JSON object"})

    event = normalize_jira_event(payload)
    if not event.issue_key:
        logger.info("Jira webhook: payload had no issue key — ignored")
        return _json(status.HTTP_200_OK, {"status": "ignored", "reason": "no_issue_key"})

    # ── Loop guard: ignore the agent's own actions ────────────────────────────
    if is_self_event(event, cfg.jira_agent_account_id or None):
        logger.info("Jira webhook: ignoring self-event on %s (actor=%s)", event.issue_key, event.actor_account_id)
        return _json(status.HTTP_200_OK, {"status": "ignored", "reason": "self_event"})

    # ── Idempotency ───────────────────────────────────────────────────────────
    key = event.dedup_key()
    if _deduper.seen_before(key):
        logger.info("Jira webhook: duplicate event %s on %s — ignored", key, event.issue_key)
        return _json(status.HTTP_200_OK, {"status": "ignored", "reason": "duplicate"})

    # ── Acknowledge fast, then process in background (S2 trigger→action) ──────
    logger.info(
        "Jira webhook received: type=%s issue=%s status=%s→%s field=%s actor=%s",
        event.event_type, event.issue_key, event.status_from, event.status_to,
        event.field, event.actor_account_id,
    )
    background_tasks.add_task(_process_event, event)
    return _json(
        status.HTTP_200_OK,
        {
            "status": "received",
            "event_type": event.event_type,
            "issue_key": event.issue_key,
            "status_from": event.status_from,
            "status_to": event.status_to,
            "field": event.field,
        },
    )


def _json(code: int, body: dict) -> Response:
    return Response(content=json.dumps(body), media_type="application/json", status_code=code)
