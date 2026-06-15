"""Contract tests for POST /webhooks/jira (S1)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.config import get_settings

SECRET = "test-secret-123"


@pytest.fixture
def processed() -> list:
    return []


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, processed: list) -> TestClient:
    monkeypatch.setenv("JIRA_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("JIRA_AGENT_ACCOUNT_ID", "agent-acc-1")
    get_settings.cache_clear()
    import app.api.webhooks as wh
    from app.integrations.jira_events import EventDeduper
    # Fresh deduper per test so duplicate-detection cases don't bleed across tests.
    wh._deduper = EventDeduper()
    # Stub background processing so tests don't build real deps / hit the network.
    monkeypatch.setattr(wh, "_process_event", lambda event: processed.append(event))
    yield TestClient(create_app())
    get_settings.cache_clear()


def _status_payload(event_id: str = "KAN-1-001", actor: str = "human-acc") -> dict:
    return {
        "event_type": "status_changed",
        "issue_key": "KAN-1",
        "status_from": "SUBMITTED",
        "status_to": "UNDER REVIEW",
        "actor": actor,
        "event_id": event_id,
    }


def test_valid_status_event_acknowledged(client: TestClient, processed: list):
    resp = client.post("/webhooks/jira", json=_status_payload(), headers={"X-Webhook-Secret": SECRET})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "received"
    assert body["event_type"] == "status_changed"
    assert body["issue_key"] == "KAN-1"
    assert body["status_from"] == "SUBMITTED" and body["status_to"] == "UNDER REVIEW"
    # Background processing was scheduled for this event.
    assert len(processed) == 1 and processed[0].issue_key == "KAN-1"


def test_ignored_events_not_processed(client: TestClient, processed: list):
    # A comment by the agent's own account is a self-event → NOT processed.
    client.post(
        "/webhooks/jira",
        json={"event_type": "comment_added", "issue_key": "KAN-1",
              "comment": "[Agent] done", "actor": "agent-acc-1", "event_id": "self-c"},
        headers={"X-Webhook-Secret": SECRET},
    )
    assert processed == []


def test_status_change_by_agent_account_is_processed(client: TestClient, processed: list):
    # Shared-account setup: a status change still gets processed (not self).
    client.post(
        "/webhooks/jira",
        json=_status_payload(event_id="shared-1", actor="agent-acc-1"),
        headers={"X-Webhook-Secret": SECRET},
    )
    assert len(processed) == 1 and processed[0].issue_key == "KAN-1"


def test_wrong_secret_rejected(client: TestClient):
    resp = client.post("/webhooks/jira", json=_status_payload(), headers={"X-Webhook-Secret": "nope"})
    assert resp.status_code == 401


def test_missing_secret_rejected(client: TestClient):
    resp = client.post("/webhooks/jira", json=_status_payload())
    assert resp.status_code == 401


def test_duplicate_event_ignored(client: TestClient):
    h = {"X-Webhook-Secret": SECRET}
    first = client.post("/webhooks/jira", json=_status_payload("dup-1"), headers=h)
    second = client.post("/webhooks/jira", json=_status_payload("dup-1"), headers=h)
    assert first.json()["status"] == "received"
    assert second.json()["status"] == "ignored"
    assert second.json()["reason"] == "duplicate"


def test_self_event_ignored(client: TestClient):
    # A comment authored by the agent account → loop guard ignores it.
    resp = client.post(
        "/webhooks/jira",
        json={"event_type": "comment_added", "issue_key": "KAN-1",
              "comment": "[Agent] x", "actor": "agent-acc-1", "event_id": "self-1"},
        headers={"X-Webhook-Secret": SECRET},
    )
    assert resp.json()["status"] == "ignored"
    assert resp.json()["reason"] == "self_event"


def test_comment_event_parsed(client: TestClient):
    payload = {
        "event_type": "comment_added",
        "issue_key": "KAN-2",
        "comment": "@agent recheck policy",
        "actor": "human-acc",
        "event_id": "c-1",
    }
    resp = client.post("/webhooks/jira", json=payload, headers={"X-Webhook-Secret": SECRET})
    assert resp.status_code == 200
    assert resp.json()["event_type"] == "comment_added"


def test_classic_issue_data_payload_parsed(client: TestClient):
    # Jira default "Issue data" shape (no explicit event_type).
    payload = {
        "webhookEvent": "jira:issue_updated",
        "timestamp": 1718000000000,
        "user": {"accountId": "human-acc"},
        "issue": {"key": "KAN-3", "fields": {"status": {"name": "DONE"}}},
        "changelog": {"items": [{"field": "status", "fromString": "APPROVED", "toString": "DONE"}]},
    }
    resp = client.post("/webhooks/jira", json=payload, headers={"X-Webhook-Secret": SECRET})
    assert resp.status_code == 200
    body = resp.json()
    assert body["event_type"] == "status_changed"
    assert body["issue_key"] == "KAN-3"
    assert body["status_to"] == "DONE"


def test_webhook_disabled_when_no_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JIRA_WEBHOOK_SECRET", "")
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())
        resp = client.post("/webhooks/jira", json=_status_payload(), headers={"X-Webhook-Secret": "x"})
        assert resp.status_code == 503
    finally:
        get_settings.cache_clear()
