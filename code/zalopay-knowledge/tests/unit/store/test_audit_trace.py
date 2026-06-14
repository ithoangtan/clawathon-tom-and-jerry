from __future__ import annotations

import json

from app.store.audit import AuditStore
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def test_log_query_persists_stage_trace(tmp_path) -> None:
    store = AuditStore()
    trace = {
        "query": "What is KYC?",
        "rewrite": "KYC policy",
        "chunks": {RISK:  [{"chunk_id": "c1", "score": 0.9}]},
        "grades": {RISK:  {"status": "answered"}},
        "citations": [{"title": "KYC", "url": "https://example.com"}],
        "verify": {RISK:  {"status": "answered", "citation_count": 1}},
    }

    row_id = store.log_query(
        user_id="u1",
        session_id="s1",
        role="engineer",
        question="What is KYC?",
        departments=[RISK],
        status="answered",
        confidence=0.9,
        latency_ms=1200,
        feedback_id="fb-1",
        stage_trace=trace,
    )

    conn = store._connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT stage_trace_json FROM queries WHERE id = %s",
                (row_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    assert row is not None
    persisted = json.loads(row["stage_trace_json"])
    assert persisted["query"] == "What is KYC?"
    assert persisted["chunks"][RISK][0]["chunk_id"] == "c1"
