"""Unit tests for Jira event normalisation + helpers (S1)."""

from __future__ import annotations

from app.integrations.jira_events import EventDeduper, is_self_event, normalize_jira_event


def test_custom_status_payload():
    ev = normalize_jira_event({
        "event_type": "status_changed", "issue_key": "KAN-1",
        "status_from": "A", "status_to": "B", "actor": "u1", "event_id": "e1",
    })
    assert ev.event_type == "status_changed"
    assert (ev.status_from, ev.status_to) == ("A", "B")
    assert ev.dedup_key() == "e1"


def test_custom_field_payload_aliases():
    ev = normalize_jira_event({
        "event_type": "field_changed", "issue_key": "KAN-9",
        "field": "priority", "from": "Low", "to": "High",
    })
    assert ev.field == "priority"
    assert (ev.field_from, ev.field_to) == ("Low", "High")


def test_jira_null_literals_dropped():
    ev = normalize_jira_event({
        "event_type": "status_changed", "issue_key": "KAN-1",
        "status_from": "null", "status_to": "B",
    })
    assert ev.status_from is None and ev.status_to == "B"


def test_classic_comment_payload():
    ev = normalize_jira_event({
        "webhookEvent": "comment_created",
        "issue": {"key": "KAN-2"},
        "comment": {"body": "hi", "author": {"accountId": "u2"}},
    })
    assert ev.event_type == "comment_added"
    assert ev.comment_body == "hi"
    assert ev.actor_account_id == "u2"


def test_classic_status_changelog():
    ev = normalize_jira_event({
        "webhookEvent": "jira:issue_updated",
        "user": {"accountId": "u3"},
        "issue": {"key": "KAN-3", "fields": {"status": {"name": "DONE"}}},
        "changelog": {"items": [{"field": "status", "fromString": "APPROVED", "toString": "DONE"}]},
    })
    assert ev.event_type == "status_changed"
    assert (ev.status_from, ev.status_to) == ("APPROVED", "DONE")


def test_dedup_key_stable_without_event_id():
    p = {"event_type": "status_changed", "issue_key": "KAN-1", "status_to": "B"}
    assert normalize_jira_event(p).dedup_key() == normalize_jira_event(p).dedup_key()


def test_is_self_event_comment_by_agent():
    ev = normalize_jira_event({"event_type": "comment_added", "issue_key": "K-1", "actor": "agent"})
    assert is_self_event(ev, "agent") is True
    assert is_self_event(ev, "someone") is False
    assert is_self_event(ev, None) is False  # unknown agent → cannot filter


def test_status_change_by_agent_account_is_not_self():
    # The agent never transitions status — a status change by the agent's account
    # is a human action (shared-account setup) and must be processed.
    ev = normalize_jira_event({"event_type": "status_changed", "issue_key": "K-1",
                               "status_to": "APPROVED", "actor": "agent"})
    assert is_self_event(ev, "agent") is False


def test_label_change_by_agent_is_self():
    ev = normalize_jira_event({"event_type": "field_changed", "issue_key": "K-1",
                               "field": "labels", "to": "wf-x", "actor": "agent"})
    assert is_self_event(ev, "agent") is True


def test_event_deduper():
    d = EventDeduper(maxlen=2)
    assert d.seen_before("a") is False
    assert d.seen_before("a") is True
    d.seen_before("b")
    d.seen_before("c")  # evicts "a" (maxlen=2)
    assert d.seen_before("a") is False
