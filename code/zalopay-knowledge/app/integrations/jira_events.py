from __future__ import annotations

"""Normalise inbound Jira webhook payloads into a typed :class:`JiraEvent`.

The agent reacts to three event kinds — **status change**, **comment added**,
and **field change**. The payload shape is whatever the Jira Automation rule's
"Send web request" action sends. We recommend a *custom* body (see
``docs/workflow-build`` / the webhook guide) that includes an explicit
``event_type`` discriminator and old→new values, e.g.::

    {"event_type": "status_changed", "issue_key": "{{issue.key}}",
     "status_from": "{{fieldChange.fromString}}", "status_to": "{{fieldChange.toString}}",
     "actor": "{{initiator.accountId}}", "event_id": "{{issue.key}}-{{now.toMillis}}"}

…but we also best-effort parse Jira's default "Issue data" payload (which carries
``webhookEvent`` + a full ``issue`` object) so either configuration works.
"""

import hashlib
import logging
from collections import OrderedDict
from dataclasses import dataclass, field as dc_field
from typing import Any, Literal

logger = logging.getLogger(__name__)

EventType = Literal["status_changed", "comment_added", "field_changed", "issue_updated", "unknown"]


@dataclass
class JiraEvent:
    """A normalised Jira change signal."""

    event_type: EventType
    issue_key: str
    status_from: str | None = None
    status_to: str | None = None
    field: str | None = None
    field_from: str | None = None
    field_to: str | None = None
    comment_body: str | None = None
    actor_account_id: str | None = None
    event_id: str | None = None
    raw: dict[str, Any] = dc_field(default_factory=dict)

    def dedup_key(self) -> str:
        """Stable key for idempotency.

        Prefer the explicit ``event_id`` from the payload; otherwise derive a
        hash from the salient fields so identical retries collapse.
        """
        if self.event_id:
            return self.event_id
        basis = "|".join(
            str(x) for x in (
                self.event_type, self.issue_key, self.status_from, self.status_to,
                self.field, self.field_to, self.comment_body,
            )
        )
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:32]


def _s(value: Any) -> str | None:
    """Return a non-empty stripped string, or None (drops Jira's literal nulls)."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "{{fieldchange.fromstring}}"}:
        return None
    return text


def normalize_jira_event(payload: dict[str, Any]) -> JiraEvent:
    """Parse a Jira Automation / webhook payload into a :class:`JiraEvent`.

    Handles two shapes:

    1. **Custom body** (recommended): a flat dict with ``event_type`` set.
    2. **Issue data / classic webhook**: nested ``issue`` + ``webhookEvent``.
    """
    if not isinstance(payload, dict):
        return JiraEvent(event_type="unknown", issue_key="", raw={})

    # ── Shape 1: explicit custom body ─────────────────────────────────────────
    explicit = _s(payload.get("event_type"))
    if explicit:
        et: EventType = explicit if explicit in (
            "status_changed", "comment_added", "field_changed", "issue_updated"
        ) else "unknown"
        return JiraEvent(
            event_type=et,
            issue_key=_s(payload.get("issue_key")) or "",
            status_from=_s(payload.get("status_from")),
            status_to=_s(payload.get("status_to")),
            field=_s(payload.get("field")),
            field_from=_s(payload.get("from") or payload.get("field_from")),
            field_to=_s(payload.get("to") or payload.get("field_to")),
            comment_body=_s(payload.get("comment")),
            actor_account_id=_s(payload.get("actor") or payload.get("actor_account_id")),
            event_id=_s(payload.get("event_id")),
            raw=payload,
        )

    # ── Shape 2: classic webhook / "Issue data" ──────────────────────────────
    issue = payload.get("issue") or {}
    fields = issue.get("fields") or {}
    issue_key = _s(issue.get("key")) or ""
    webhook_event = _s(payload.get("webhookEvent")) or ""
    actor = (payload.get("user") or payload.get("comment", {}).get("author") or {})
    actor_id = _s(actor.get("accountId"))

    if "comment" in webhook_event or payload.get("comment"):
        comment = payload.get("comment") or {}
        return JiraEvent(
            event_type="comment_added",
            issue_key=issue_key,
            comment_body=_s(comment.get("body")),
            actor_account_id=actor_id or _s((comment.get("author") or {}).get("accountId")),
            event_id=_s(payload.get("timestamp")) and f"{issue_key}-{payload.get('timestamp')}",
            raw=payload,
        )

    # status / field change via changelog
    status_from = status_to = changed_field = field_from = field_to = None
    for item in (payload.get("changelog") or {}).get("items", []) or []:
        if item.get("field") == "status":
            status_from, status_to = _s(item.get("fromString")), _s(item.get("toString"))
        else:
            changed_field = _s(item.get("field"))
            field_from, field_to = _s(item.get("fromString")), _s(item.get("toString"))

    if status_to is not None:
        et = "status_changed"
    elif changed_field is not None:
        et = "field_changed"
    else:
        et = "issue_updated"
        status_to = _s((fields.get("status") or {}).get("name"))

    return JiraEvent(
        event_type=et,
        issue_key=issue_key,
        status_from=status_from,
        status_to=status_to,
        field=changed_field,
        field_from=field_from,
        field_to=field_to,
        actor_account_id=actor_id,
        event_id=_s(payload.get("timestamp")) and f"{issue_key}-{payload.get('timestamp')}",
        raw=payload,
    )


def is_self_event(event: JiraEvent, agent_account_id: str | None) -> bool:
    """True when the event is a side-effect the agent itself produced.

    Breaks feedback loops without over-filtering. The agent only ever **comments**
    and **changes labels** on Jira — it never transitions a ticket's status. So an
    event by the agent's account is only "self" when it is a ``comment_added`` or a
    label ``field_changed``. ``status_changed`` is always human-driven and must be
    processed even when the human shares the agent's Atlassian account (common in
    single-account setups).

    When the agent account or the event actor is unknown, returns False
    (cannot safely filter).
    """
    if not agent_account_id or not event.actor_account_id:
        return False
    if event.actor_account_id != agent_account_id:
        return False
    if event.event_type == "comment_added":
        return True
    if event.event_type == "field_changed" and (event.field or "").lower() == "labels":
        return True
    return False


class EventDeduper:
    """Bounded in-memory set of recently-seen dedup keys.

    Jira retries a webhook on timeout, so the same logical event can arrive more
    than once. This collapses duplicates within the process.

    NB: in-process only — a multi-replica deploy needs a shared store (Redis /
    the MySQL audit DB). Acceptable for single-replica demo; see the webhook
    guide for the production note.
    """

    def __init__(self, maxlen: int = 2048) -> None:
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._maxlen = maxlen

    def seen_before(self, key: str) -> bool:
        if key in self._seen:
            self._seen.move_to_end(key)
            return True
        self._seen[key] = None
        if len(self._seen) > self._maxlen:
            self._seen.popitem(last=False)
        return False
