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

    Runs after the 200 ack so Jira does not time out / retry. Creates a session
    immediately and emits incremental progress messages so the chat UI shows a
    live activity feed while processing. Updates status to "done" / "error" when
    the handler completes.
    """
    import uuid
    from datetime import datetime, timezone
    from app.adapters.deps import get_deps
    from app.api.routes import get_session_store
    from app.integrations.jira_handler import handle_jira_event
    from app.workflow.labels import WORKFLOW_LABEL_PREFIX
    from app.workflow.registry import WORKFLOW_REGISTRY

    session_id = str(uuid.uuid4())
    session_store = get_session_store()

    raw_labels: list[str] = []
    if event.raw:
        issue_fields = (event.raw.get("issue") or {}).get("fields") or {}
        raw_labels = issue_fields.get("labels") or []
    wf_label = next((lbl for lbl in raw_labels if lbl.startswith(WORKFLOW_LABEL_PREFIX)), None)
    slug = wf_label[len(WORKFLOW_LABEL_PREFIX):] if wf_label else ""
    workflow_id = slug if slug in WORKFLOW_REGISTRY else (slug or "unknown")

    # ── Live-progress machinery ───────────────────────────────────────────────
    _messages: list[dict] = []

    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _push(role: str, content: str, msg_id: str, response: dict | None = None) -> None:
        msg: dict = {"role": role, "content": content, "id": msg_id, "timestamp": _now()}
        if response:
            msg["response"] = response
        _messages.append(msg)
        try:
            session_store.update_messages(session_id, _messages)
        except Exception:  # noqa: BLE001
            pass

    def progress(text: str, step: int) -> None:
        """Emit a progress step as an assistant message with agent_action status."""
        _push(
            "assistant",
            text,
            f"wh-step-{session_id[:6]}-{step}",
            response={
                "status": "agent_action",
                "answer": text,
                "citations": [],
                "source_departments": [],
                "confidence": 0,
                "feedback_id": "",
            },
        )

    # ── Create session immediately so sidebar shows the entry ─────────────────
    try:
        session_store.create_processing_session(
            session_id=session_id,
            title=f"[{event.issue_key}] Campaign Risk Review",
            workflow_id=workflow_id,
            jira_key=event.issue_key,
        )
    except Exception:  # noqa: BLE001
        logger.warning("Could not create processing session for %s", event.issue_key)

    # First progress message immediately visible.
    _push(
        "user",
        f"[Jira · {event.issue_key}] Ticket vừa chuyển sang **{event.status_to or 'RISK REVIEW'}**. "
        f"Kích hoạt workflow **Campaign Risk Review**.",
        f"wh-user-{session_id[:6]}",
    )
    progress(
        f"📋 **Nhận sự kiện từ Jira**\n"
        f"Ticket **{event.issue_key}** chuyển trạng thái → **{event.status_to or 'RISK REVIEW'}**. "
        f"Đang bắt đầu quy trình review campaign tự động...",
        1,
    )

    try:
        deps = get_deps()
        result = handle_jira_event(
            event,
            llm=deps.llm,
            retriever=deps.retriever,
            jira=deps.jira,
            confluence_writer=deps.confluence_writer,
            settings=deps.settings,
            progress=progress,
        )
        logger.info("Jira webhook processed %s → %s", event.issue_key, result.get("status"))
        final_status = "done" if result.get("status") not in ("error",) else "error"

        # Final message: the full risk report from the LLM.
        result_text = result.get("result_text") or ""
        decision = result.get("decision") or ""
        verbs = (result.get("reactions") or {}).get("verbs") or []

        # Auto-link KAN-\d+ ticket references in the result text.
        import re as _re
        cfg_inner = deps.settings
        _jira_base = (cfg_inner.confluence_base_url or "").rstrip("/")
        if _jira_base.endswith("/wiki"):
            _jira_base = _jira_base[:-5]
        if _jira_base:
            result_text = _re.sub(
                r'\bKAN-(\d+)\b',
                lambda m: f"[{m.group(0)}]({_jira_base}/browse/{m.group(0)})",
                result_text,
            )

        if result_text:
            _DECISION_READABLE = {
                "PASS": "✅ Passed",
                "PARTIAL_FAIL": "⚠️ Partial Fail — Needs Clarification",
                "FAIL": "❌ Failed",
            }
            footer = ""
            if decision:
                readable = _DECISION_READABLE.get(decision.upper().replace("-", "_"), decision)
                footer = f"\n\n---\n**{readable}**"
            if verbs:
                footer += f" | {', '.join(verbs)}"
            full_answer = result_text + footer
            _push(
                "assistant",
                full_answer,
                f"wh-result-{session_id[:6]}",
                response={
                    "status": "answered",
                    "answer": full_answer,
                    "citations": [],
                    "source_departments": ["risk"],
                    "confidence": 0.9,
                    "feedback_id": "",
                },
            )
    except Exception:  # noqa: BLE001
        logger.exception("Jira webhook background processing failed for %s", event.issue_key)
        final_status = "error"
        progress(f"❌ **Lỗi**: Không thể hoàn thành xử lý cho {event.issue_key}.", 99)

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
