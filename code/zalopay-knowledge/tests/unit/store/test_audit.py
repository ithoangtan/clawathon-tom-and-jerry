from __future__ import annotations

import json
import sqlite3

import pytest

from app.store.audit import AuditStore, _percentile


class TestAuditStoreLogging:
    def test_log_query_returns_uuid(self, audit_store: AuditStore) -> None:
        row_id = audit_store.log_query(
            user_id="u1",
            session_id="s1",
            role="engineer",
            question="What is the escalation policy?",
            departments=["risk"],
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
            departments=["risk"],
            status="answered",
            confidence=0.5,
            latency_ms=100,
            feedback_id="fb-pii",
        )
        conn = sqlite3.connect(str(audit_store._path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT question FROM queries WHERE feedback_id = ?", ("fb-pii",)
            ).fetchone()
            assert "[email]" in row["question"]
            assert "alice@example.com" not in row["question"]
        finally:
            conn.close()

    def test_log_query_stores_departments_and_user_for_audit_trail(
        self, audit_store: AuditStore
    ) -> None:
        """FR-7.1: queries logged with user, departments, latency."""
        audit_store.log_query(
            user_id="user-42",
            session_id="sess-99",
            role="risk",
            question="Threshold policy?",
            departments=["risk", "grow_enablement"],
            status="answered",
            confidence=0.88,
            latency_ms=512,
            feedback_id="fb-audit-trail",
            tokens=42,
        )
        conn = sqlite3.connect(str(audit_store._path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT user_id, session_id, role, departments, latency_ms, tokens "
                "FROM queries WHERE feedback_id = ?",
                ("fb-audit-trail",),
            ).fetchone()
            assert row["user_id"] == "user-42"
            assert row["session_id"] == "sess-99"
            assert row["role"] == "risk"
            assert json.loads(row["departments"]) == ["risk", "grow_enablement"]
            assert row["latency_ms"] == 512
            assert row["tokens"] == 42
        finally:
            conn.close()

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
        conn = sqlite3.connect(str(audit_store._path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT status, confidence FROM queries WHERE feedback_id = ?",
                ("fb-refused",),
            ).fetchone()
            assert row["status"] == "refused"
            assert row["confidence"] == 0.0
        finally:
            conn.close()


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
            departments=["risk"],
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
            departments=["risk", "legal"],
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
            departments=["risk", "compliance"],
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
            departments=["risk"],
            status="answered",
            confidence=0.7,
            latency_ms=120,
            feedback_id=feedback_id,
        )
        conn = sqlite3.connect(str(audit_store._path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT feedback_id, citations_json FROM queries WHERE feedback_id = ?",
                (feedback_id,),
            ).fetchone()
            assert row["feedback_id"] == feedback_id
            assert json.loads(row["citations_json"]) == []
        finally:
            conn.close()


class TestPercentile:
    def test_percentile_single_value(self) -> None:
        assert _percentile([42], 50) == 42.0

    def test_percentile_interpolation(self) -> None:
        assert _percentile([10, 20, 30, 40], 50) == 25.0

    def test_percentile_empty(self) -> None:
        assert _percentile([], 50) == 0.0
