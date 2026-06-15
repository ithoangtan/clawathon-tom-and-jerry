from __future__ import annotations

"""Match an inbound Jira event against a workflow's ``## Triggers`` rules.

Stateless: given a normalised :class:`~app.integrations.jira_events.JiraEvent`
and a parsed :class:`~app.workflow.models.WorkflowDefinition`, return the first
trigger whose event type + conditions match (document order = priority).
"""

from app.integrations.jira_events import JiraEvent
from app.workflow.models import WorkflowDefinition, WorkflowTrigger


def _eq(a: str | None, b: str | None) -> bool:
    """Case-insensitive, whitespace-tolerant equality (``None`` never matches)."""
    if a is None or b is None:
        return False
    return a.strip().casefold() == b.strip().casefold()


def _wild(spec: str | None) -> bool:
    """True when a trigger field means 'any' (empty or ``*``)."""
    return spec is None or spec.strip() in {"", "*"}


def match_trigger(event: JiraEvent, defn: WorkflowDefinition) -> WorkflowTrigger | None:
    """Return the first trigger matching *event*, or None.

    Matching rules per event type:
    - ``status_changed``: ``to_status`` must match (unless wildcard) and
      ``from_status`` must match (unless wildcard).
    - ``comment_added``: ``comment_contains`` substring must be present
      (case-insensitive; wildcard = any comment).
    - ``field_changed``: ``field`` name must match (unless wildcard) and
      ``field_to`` must match the new value (unless wildcard).
    """
    for trig in defn.triggers:
        if trig.event_type != event.event_type:
            continue

        if event.event_type == "status_changed":
            if not _wild(trig.to_status) and not _eq(trig.to_status, event.status_to):
                continue
            if not _wild(trig.from_status) and not _eq(trig.from_status, event.status_from):
                continue
            return trig

        if event.event_type == "comment_added":
            if not _wild(trig.comment_contains):
                if (trig.comment_contains or "").strip().casefold() not in (event.comment_body or "").casefold():
                    continue
            return trig

        if event.event_type == "field_changed":
            if not _wild(trig.field) and not _eq(trig.field, event.field):
                continue
            if not _wild(trig.field_to) and not _eq(trig.field_to, event.field_to):
                continue
            return trig

    return None
