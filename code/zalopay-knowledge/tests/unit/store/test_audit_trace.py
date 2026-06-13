from __future__ import annotations

import json

from app.store.audit import AuditStore


def test_log_query_persists_stage_trace(tmp_path) -> None:
    store = AuditStore(tmp_path / "audit.db")
    trace = {
        "query": "What is KYC?",
        "rewrite": "KYC policy",
        "chunks": {"risk": [{"chunk_id": "c1", "score": 0.9}]},
        "grades": {"risk": {"status": "answered"}},
        "citations": [{"title": "KYC", "url": "https://example.com"}],
        "verify": {"risk": {"status": "answered", "citation_count": 1}},
    }

    row_id = store.log_query(
        user_id="u1",
        session_id="s1",
        role="engineer",
        question="What is KYC?",
        departments=["risk"],
        status="answered",
        confidence=0.9,
        latency_ms=1200,
        feedback_id="fb-1",
        stage_trace=trace,
    )

    conn = store._connect()
    try:
        row = conn.execute(
            "SELECT stage_trace_json FROM queries WHERE id = ?",
            (row_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    persisted = json.loads(row["stage_trace_json"])
    assert persisted["query"] == "What is KYC?"
    assert persisted["chunks"]["risk"][0]["chunk_id"] == "c1"
