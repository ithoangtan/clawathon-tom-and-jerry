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


import re as _re

_CHECKLIST_RE = _re.compile(
    r'^- (.+?):\s+\*\*(Comply|Violate|Chưa rõ)\*\*\s*(?:—|–|-)\s*(.*)$',
    _re.MULTILINE,
)
_DECISION_RAW_RE = _re.compile(r'\n*DECISION\s*:\s*\S+\s*$', _re.IGNORECASE)
_DECISION_READABLE = {
    "PASS": "✅ Passed",
    "PARTIAL_FAIL": "⚠️ Partial Fail — Needs Clarification",
    "FAIL": "❌ Failed",
}


def _checklist_to_table(text: str) -> str:
    """Convert bullet checklist items to a GFM markdown table for chat display."""
    matches = list(_CHECKLIST_RE.finditer(text))
    if not matches:
        return text
    header = "| Tiêu chí | Kết quả | Dẫn chứng |\n|---|---|---|"
    rows = [
        f"| {m.group(1).strip()} | **{m.group(2).strip()}** | {m.group(3).strip()} |"
        for m in matches
    ]
    table = header + "\n" + "\n".join(rows)
    return text[: matches[0].start()] + table + text[matches[-1].end() :]


def _kan_link(text: str, jira_base: str) -> str:
    if not jira_base:
        return text
    return _re.sub(
        r'\bKAN-(\d+)\b',
        lambda m: f"[{m.group(0)}]({jira_base}/browse/{m.group(0)})",
        text,
    )


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

    # Compute jira base URL early so progress() closure and user message can use it.
    _cfg_early = get_settings()
    _jira_base = (_cfg_early.confluence_base_url or "").rstrip("/")
    if _jira_base.endswith("/wiki"):
        _jira_base = _jira_base[:-5]
    _issue_url = f"{_jira_base}/browse/{event.issue_key}" if _jira_base else "#"

    session_id = str(uuid.uuid4())
    session_store = get_session_store()

    # ── Extract assignee info from raw payload for email notification ─────────
    _raw = event.raw or {}
    _issue_fields_raw = (_raw.get("issue") or {}).get("fields") or {}
    _assignee_raw = _issue_fields_raw.get("assignee") or {}
    _user_raw = _raw.get("user") or {}
    # emailAddress is often hidden in issue.fields.assignee; user.emailAddress has it
    assignee_email = (_assignee_raw.get("emailAddress") or _user_raw.get("emailAddress") or "").strip()
    assignee_name = (_assignee_raw.get("displayName") or _user_raw.get("displayName") or "").strip()
    assignee_avatar = (
        (_assignee_raw.get("avatarUrls") or _user_raw.get("avatarUrls") or {}).get("48x48") or ""
    )

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
        """Emit a progress step with agent_action status. Auto-links KAN-XX keys."""
        text = _kan_link(text, _jira_base)
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

    # First progress message immediately visible — issue key is a clickable link.
    _push(
        "user",
        f"[Jira · [{event.issue_key}]({_issue_url})] Ticket vừa chuyển sang "
        f"**{event.status_to or 'RISK REVIEW'}**. "
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

        # Final message: format for chat display.
        result_text = result.get("result_text") or ""
        decision = result.get("decision") or ""
        verbs = (result.get("reactions") or {}).get("verbs") or []

        if result_text:
            # Strip raw "DECISION: X" line LLM appends (replaced by styled footer below).
            result_text = _DECISION_RAW_RE.sub("", result_text).strip()
            # Convert checklist bullet items → GFM table (consistent with Jira comment).
            result_text = _checklist_to_table(result_text)
            # Auto-link any KAN-XX references left in the text.
            result_text = _kan_link(result_text, _jira_base)

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

        # ── Send email notification to assignee (optional — never blocks workflow) ─
        if assignee_email and result.get("status") not in ("error", "ignored", "invalid"):
            try:
                _send_assignee_notification(
                    event=event,
                    session_id=session_id,
                    result=result,
                    assignee_email=assignee_email,
                    assignee_name=assignee_name,
                    assignee_avatar=assignee_avatar,
                    issue_url=_issue_url,
                    settings=deps.settings,
                    push=_push,
                )
            except Exception:
                logger.warning(
                    "Email notification failed for %s → %s (non-fatal, workflow continues)",
                    event.issue_key, assignee_email, exc_info=True,
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


def _send_assignee_notification(
    *,
    event,
    session_id: str,
    result: dict,
    assignee_email: str,
    assignee_name: str,
    assignee_avatar: str,
    issue_url: str,
    settings,
    push,
) -> None:
    """Send email to assignee and push a chat notification message."""
    from app.adapters.gmail_sender import send_email

    issue_key = event.issue_key
    summary = (result.get("result_text") or "")[:300].strip()
    decision = (result.get("decision") or "").upper()
    decision_label = _DECISION_READABLE.get(decision.replace("-", "_"), decision) if decision else ""

    chat_url = ""
    base = (settings.chat_base_url or "").rstrip("/")
    if base:
        chat_url = f"{base}/chat/{session_id}"

    subject = f"[{issue_key}] Risk Review hoàn tất — {decision_label or 'Xem kết quả'}"

    avatar_html = f'<img src="{assignee_avatar}" width="32" height="32" style="border-radius:50%;vertical-align:middle;margin-right:8px;" />' if assignee_avatar else ""
    chat_link_html = (
        f'<p><a href="{chat_url}" style="font-weight:bold;">🔗 Xem kết quả đầy đủ trên hệ thống</a></p>'
        if chat_url else ""
    )
    jira_link_html = f'<p><a href="{issue_url}">📋 Xem ticket {issue_key} trên Jira</a></p>' if issue_url != "#" else ""

    body_html = f"""
<html><body style="font-family:sans-serif;color:#1a1a2e;max-width:600px;">
  <div style="background:#f4f4f8;padding:20px;border-radius:8px;">
    <h2 style="color:#0052cc;">Risk Review — {issue_key}</h2>
    <p>Xin chào {avatar_html}<strong>{assignee_name or assignee_email}</strong>,</p>
    <p>Workflow <strong>Campaign Risk Review</strong> cho ticket <strong>{issue_key}</strong> đã hoàn tất.</p>
    {"<p><strong>Kết quả: " + decision_label + "</strong></p>" if decision_label else ""}
    <blockquote style="border-left:4px solid #0052cc;padding-left:12px;color:#555;">
      {summary.replace(chr(10), "<br>")}{"..." if len(result.get("result_text") or "") > 300 else ""}
    </blockquote>
    {chat_link_html}
    {jira_link_html}
    <hr style="border:none;border-top:1px solid #ddd;margin-top:20px;"/>
    <p style="font-size:12px;color:#888;">Tin nhắn này được gửi tự động bởi Zalopay Knowledge Agent.</p>
  </div>
</body></html>
"""

    sent = send_email(to=assignee_email, subject=subject, body_html=body_html, settings=settings)

    avatar_md = f"![avatar]({assignee_avatar})" if assignee_avatar else ""
    recipient = f"{avatar_md} **{assignee_name}** ({assignee_email})" if assignee_name else f"**{assignee_email}**"

    if sent:
        notify_text = (
            f"📧 **Đã gửi email thông báo** tới {recipient}"
            + (f" — [Xem conversation]({chat_url})" if chat_url else "")
        )
    else:
        notify_text = f"⚠️ **Gửi email thất bại** cho {recipient} — workflow vẫn hoàn tất, kiểm tra log Gmail để biết thêm."
        logger.warning("Gmail notification skipped or failed for %s → %s", event.issue_key, assignee_email)

    push(
        "assistant",
        notify_text,
        f"wh-notify-{session_id[:6]}",
        response={
            "status": "agent_action",
            "answer": notify_text,
            "citations": [],
            "source_departments": [],
            "confidence": 0,
            "feedback_id": "",
        },
    )


def _json(code: int, body: dict) -> Response:
    return Response(content=json.dumps(body), media_type="application/json", status_code=code)
