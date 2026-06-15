from __future__ import annotations

import json

import pytest

from app.store.audit import AuditStore, _percentile
from app.store.db import get_connection
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def _fetch_query(feedback_id: str) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM queries WHERE feedback_id = %s", (feedback_id,))
            return cur.fetchone()
    finally:
        conn.close()


class TestAuditStoreLogging:
    def test_log_query_returns_uuid(self, audit_store: AuditStore) -> None:
        row_id = audit_store.log_query(
            user_id="u1",
            session_id="s1",
            role="engineer",
            question="What is the escalation policy?",
            departments=[RISK],
            status="answered",
            confidence=0.92,
            latency_ms=450,
            feedback_id="fb-001",
            citations=[{"chunk_id": "c1", "title": "Policy"}],
            tokens=120,
        )
        assert row_id
        assert len(row_id) == 36  # UUID format

    def test_log_query_masks_pii_in_question(self, audit_store: AuditStore) -> None:
        audit_store.log_query(
            user_id="u1",
            session_id="s1",
            role="engineer",
            question="Email me at alice@example.com",
            departments=[RISK],
            status="answered",
            confidence=0.5,
            latency_ms=100,
            feedback_id="fb-pii",
        )
        row = _fetch_query("fb-pii")
        assert row is not None
        assert "[email]" in row["question"]
        assert "alice@example.com" not in row["question"]

    def test_log_query_stores_departments_and_user_for_audit_trail(
        self, audit_store: AuditStore
    ) -> None:
        """FR-7.1: queries logged with user, departments, latency."""
        audit_store.log_query(
            user_id="user-42",
            session_id="sess-99",
            role=RISK,
            question="Threshold policy?",
            departments=[RISK, GROW],
            status="answered",
            confidence=0.88,
            latency_ms=512,
            feedback_id="fb-audit-trail",
            tokens=42,
        )
        row = _fetch_query("fb-audit-trail")
        assert row is not None
        assert row["user_id"] == "user-42"
        assert row["session_id"] == "sess-99"
        assert row["role"] == RISK
        assert json.loads(row["departments"]) == [RISK, GROW]
        assert row["latency_ms"] == 512
        assert row["tokens"] == 42

    def test_log_refusal(self, audit_store: AuditStore) -> None:
        audit_store.log_query(
            user_id="u2",
            session_id="s2",
            role="pm",
            question="Unknown topic",
            departments=["legal"],
            status="refused",
            confidence=0.0,
            latency_ms=80,
            feedback_id="fb-refused",
        )
        row = _fetch_query("fb-refused")
        assert row is not None
        assert row["status"] == "refused"
        assert row["confidence"] == 0.0


class TestAuditStoreRetrieval:
    def test_dashboard_metrics_empty(self, audit_store: AuditStore) -> None:
        metrics = audit_store.dashboard_metrics()
        assert metrics["query_count"] == 0
        assert metrics["refusal_rate"] == 0.0
        assert metrics["deflection_rate"] == 0.0
        assert metrics["answered_wrong_rate"] == 0.0
        assert metrics["history"] == []

    def test_dashboard_metrics_aggregates_queries(self, audit_store: AuditStore) -> None:
        audit_store.log_query(
            user_id="u1",
            session_id="s1",
            role="engineer",
            question="Q1",
            departments=[RISK],
            status="answered",
            confidence=0.9,
            latency_ms=100,
            feedback_id="fb-1",
            tokens=50,
        )
        audit_store.log_query(
            user_id="u1",
            session_id="s1",
            role="engineer",
            question="Q2",
            departments=[RISK, "legal"],
            status="refused",
            confidence=0.0,
            latency_ms=200,
            feedback_id="fb-2",
            tokens=10,
        )
        audit_store.log_query(
            user_id="u1",
            session_id="s1",
            role="engineer",
            question="Q3",
            departments=["legal"],
            status="partial",
            confidence=0.6,
            latency_ms=300,
            feedback_id="fb-3",
            tokens=30,
        )

        metrics = audit_store.dashboard_metrics(history_limit=2)
        assert metrics["query_count"] == 3
        assert metrics["refusal_rate"] == pytest.approx(1 / 3)
        assert metrics["partial_rate"] == pytest.approx(1 / 3)
        assert metrics["deflection_rate"] == pytest.approx(2 / 3)
        assert metrics["total_tokens"] == 90
        assert metrics["latency_p50_ms"] == 200.0
        assert len(metrics["history"]) == 2
        assert metrics["history"][0]["question"] == "Q3"
        assert metrics["history"][0]["departments"] == ["legal"]

    def test_dashboard_history_deserializes_departments(self, audit_store: AuditStore) -> None:
        audit_store.log_query(
            user_id="u1",
            session_id="s1",
            role="engineer",
            question="Dept test",
            departments=[RISK, "compliance"],
            status="answered",
            confidence=0.8,
            latency_ms=150,
            feedback_id="fb-dept",
        )
        history = audit_store.dashboard_metrics()["history"]
        assert history[0]["departments"] == ["risk", "compliance"]

    def test_feedback_id_stored_for_correlation(self, audit_store: AuditStore) -> None:
        feedback_id = "correlate-me-123"
        audit_store.log_query(
            user_id="u1",
            session_id="s1",
            role="engineer",
            question="Correlate?",
            departments=[RISK],
            status="answered",
            confidence=0.7,
            latency_ms=120,
            feedback_id=feedback_id,
        )
        row = _fetch_query(feedback_id)
        assert row is not None
        assert row["feedback_id"] == feedback_id
        assert json.loads(row["citations_json"]) == []


class TestPopularQuestions:
    def _log(self, store: AuditStore, question: str, fid: str) -> None:
        store.log_query(
            user_id="u1",
            session_id="s1",
            role="engineer",
            question=question,
            departments=[RISK],
            status="answered",
            confidence=0.9,
            latency_ms=100,
            feedback_id=fid,
        )

    def test_empty_db_returns_empty(self, audit_store: AuditStore) -> None:
        assert audit_store.popular_questions() == []

    def test_returns_most_frequent_first(self, audit_store: AuditStore) -> None:
        self._log(audit_store, "Q-rare", "fb-r1")
        for i in range(3):
            self._log(audit_store, "Q-popular", f"fb-p{i}")
        for i in range(2):
            self._log(audit_store, "Q-medium", f"fb-m{i}")

        result = audit_store.popular_questions(limit=3)
        assert result[0] == "Q-popular"
        assert result[1] == "Q-medium"
        assert result[2] == "Q-rare"

    def test_respects_limit(self, audit_store: AuditStore) -> None:
        for i in range(5):
            self._log(audit_store, f"Unique question {i}", f"fb-u{i}")
        result = audit_store.popular_questions(limit=3)
        assert len(result) == 3

    def test_fewer_than_limit_returns_all(self, audit_store: AuditStore) -> None:
        self._log(audit_store, "Only question", "fb-only")
        result = audit_store.popular_questions(limit=3)
        assert result == ["Only question"]

    def test_excludes_null_question(self, audit_store: AuditStore) -> None:
        # log_query masks PII but always stores something; we test via direct insert
        from app.store.db import get_connection
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO queries (id, ts, user_id, session_id, role, question, departments, status, confidence, latency_ms, feedback_id) "
                    "VALUES (%s, %s, %s, %s, %s, NULL, '[]', 'answered', 0.5, 100, %s)",
                    ("null-q-id", 1.0, "u1", "s1", "engineer", "fb-null-q"),
                )
            conn.commit()
        finally:
            conn.close()
        result = audit_store.popular_questions(limit=10)
        assert all(q is not None and q != "" for q in result)


class TestPercentile:
    def test_percentile_single_value(self) -> None:
        assert _percentile([42], 50) == 42.0

    def test_percentile_interpolation(self) -> None:
        assert _percentile([10, 20, 30, 40], 50) == 25.0

    def test_percentile_empty(self) -> None:
        assert _percentile([], 50) == 0.0
