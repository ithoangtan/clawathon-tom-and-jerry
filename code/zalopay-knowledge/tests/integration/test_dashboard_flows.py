"""Integration tests for GET /api/dashboard — MVP north-star metrics."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import create_app
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def test_dashboard_tracks_partial_refusal_and_conflict_rates() -> None:
    """Dashboard aggregates partial/refused rows for PM guardrail metrics."""
    from app.api.service import get_audit_store

    client = TestClient(create_app())
    store = get_audit_store()
    store.log_query(
        user_id="dash-user",
        session_id="dash-session",
        role="engineer",
        question="How does merchant onboarding work?",
        departments=[GROW],
        status="partial",
        confidence=0.55,
        latency_ms=2100,
        feedback_id="fb-dash-partial",
    )
    store.log_query(
        user_id="dash-user",
        session_id="dash-session",
        role="engineer",
        question="What is today's transaction volume?",
        departments=[],
        status="refused",
        confidence=0.0,
        latency_ms=320,
        feedback_id="fb-dash-refused",
    )

    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    body = resp.json()

    assert body["query_count"] >= 2
    assert body["partial_rate"] > 0.0
    assert body["refusal_rate"] > 0.0
    statuses = {row["status"] for row in body["history"]}
    assert "partial" in statuses
    assert "refused" in statuses
