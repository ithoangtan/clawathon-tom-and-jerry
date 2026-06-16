from __future__ import annotations

"""Append-only audit log for queries, answers, and refusals."""

import json
import logging
import time
import uuid
from typing import Any

import pymysql.connections

from app.common.pii import mask_pii
from app.store.db import get_connection, ensure_index

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS queries (
    id           VARCHAR(36)   NOT NULL,
    ts           DOUBLE        NOT NULL,
    user_id      VARCHAR(255),
    session_id   VARCHAR(255),
    role         VARCHAR(50),
    question     TEXT,
    departments  TEXT,
    status       VARCHAR(50),
    confidence   DOUBLE,
    latency_ms   INT,
    feedback_id  VARCHAR(36),
    citations_json    MEDIUMTEXT,
    answer_preview    TEXT,
    tokens            INT           DEFAULT 0,
    stage_trace_json  MEDIUMTEXT,
    model_used        VARCHAR(255),
    PRIMARY KEY (id)
) CHARACTER SET utf8mb4
"""


class AuditStore:
    """MySQL-backed audit log (table ``queries``)."""

    def __init__(self) -> None:
        self.ensure_schema()

    def _connect(self) -> pymysql.connections.Connection:
        return get_connection()

    def ensure_schema(self) -> None:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(_CREATE_TABLE)
            ensure_index(conn, "queries", "idx_queries_ts", "ts DESC")
            conn.commit()
        finally:
            conn.close()

    def log_query(
        self,
        *,
        user_id: str,
        session_id: str,
        role: str,
        question: str,
        departments: list[str],
        status: str,
        confidence: float,
        latency_ms: int,
        feedback_id: str,
        citations: list[dict] | None = None,
        answer_preview: str = "",
        tokens: int = 0,
        stage_trace: dict | None = None,
        model_used: str | None = None,
    ) -> str:
        """Record one query/answer event. Returns the audit row id."""
        row_id = str(uuid.uuid4())
        preview = mask_pii(answer_preview[:500]) if answer_preview else ""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO queries (
                        id, ts, user_id, session_id, role, question, departments,
                        status, confidence, latency_ms, feedback_id, citations_json,
                        answer_preview, tokens, stage_trace_json, model_used
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        row_id,
                        time.time(),
                        user_id,
                        session_id,
                        role,
                        mask_pii(question),
                        json.dumps(departments),
                        status,
                        confidence,
                        latency_ms,
                        feedback_id,
                        json.dumps(citations or []),
                        preview,
                        tokens,
                        json.dumps(stage_trace) if stage_trace else None,
                        model_used or None,
                    ),
                )
            conn.commit()
        finally:
            conn.close()
        return row_id

    def dashboard_metrics(self, *, history_limit: int = 100) -> dict[str, Any]:
        """Aggregate metrics for ``GET /api/dashboard``."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS n FROM queries")
                total = cur.fetchone()["n"]
                if total == 0:
                    return {
                        "query_count": 0,
                        "deflection_rate": 0.0,
                        "answered_wrong_rate": 0.0,
                        "refusal_rate": 0.0,
                        "partial_rate": 0.0,
                        "conflict_rate": 0.0,
                        "latency_p50_ms": 0.0,
                        "latency_p95_ms": 0.0,
                        "feedback_up": 0,
                        "feedback_down": 0,
                        "total_tokens": 0,
                        "history": [],
                    }

                cur.execute("SELECT COUNT(*) AS n FROM queries WHERE status = 'refused'")
                refused = cur.fetchone()["n"]

                cur.execute("SELECT COUNT(*) AS n FROM queries WHERE status = 'partial'")
                partial = cur.fetchone()["n"]

                cur.execute("SELECT COUNT(*) AS n FROM queries WHERE status = 'answered'")
                answered = cur.fetchone()["n"]

                cur.execute("SELECT latency_ms FROM queries ORDER BY ts")
                latencies = [r["latency_ms"] for r in cur.fetchall()]

                cur.execute("SELECT COALESCE(SUM(tokens), 0) AS t FROM queries")
                tokens = cur.fetchone()["t"]

                cur.execute(
                    """
                    SELECT ts, question, departments, status, confidence, latency_ms, model_used
                    FROM queries ORDER BY ts DESC LIMIT %s
                    """,
                    (history_limit,),
                )
                history_rows = cur.fetchall()

            history = []
            for r in history_rows:
                from datetime import datetime, timezone

                history.append(
                    {
                        "ts": datetime.fromtimestamp(r["ts"], tz=timezone.utc)
                        .isoformat()
                        .replace("+00:00", "Z"),
                        "question": r["question"],
                        "departments": json.loads(r["departments"] or "[]"),
                        "status": r["status"],
                        "confidence": r["confidence"],
                        "latency_ms": r["latency_ms"],
                        "model_used": r["model_used"] or None,
                    }
                )

            latencies_sorted = sorted(latencies)
            p50 = _percentile(latencies_sorted, 50)
            p95 = _percentile(latencies_sorted, 95)

            return {
                "query_count": total,
                "deflection_rate": (answered + partial) / total,
                "answered_wrong_rate": 0.0,
                "refusal_rate": refused / total,
                "partial_rate": partial / total,
                "conflict_rate": 0.0,
                "latency_p50_ms": float(p50),
                "latency_p95_ms": float(p95),
                "feedback_up": 0,
                "feedback_down": 0,
                "total_tokens": int(tokens),
                "history": history,
            }
        finally:
            conn.close()


    def popular_questions(self, *, limit: int = 3) -> list[str]:
        """Return the N most *frequently asked* answered questions (confidence >= 0.5).

        Deduplicates by question text and ranks by how often each was asked
        (recency breaks ties), so the UI surfaces genuinely popular questions.
        """
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT question, COUNT(*) AS freq, MAX(ts) AS last_ts
                    FROM queries
                    WHERE question IS NOT NULL
                      AND question != ''
                      AND status = 'answered'
                      AND confidence >= 0.5
                    GROUP BY question
                    ORDER BY freq DESC, last_ts DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
            return [r["question"] for r in rows]
        finally:
            conn.close()

    def refused_questions(self, *, limit: int = 20, days: int = 30) -> list[dict]:
        """Return recent refused questions — potential documentation gaps."""
        conn = get_connection()
        cutoff = time.time() - days * 86400
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT question, departments, COUNT(*) AS cnt,
                           MAX(ts) AS last_seen
                    FROM queries
                    WHERE status = 'refused'
                      AND ts >= %s
                      AND question IS NOT NULL
                    GROUP BY question, departments
                    ORDER BY cnt DESC, last_seen DESC
                    LIMIT %s
                    """,
                    (cutoff, limit),
                )
                rows = cur.fetchall()
            from datetime import datetime, timezone
            result = []
            for r in rows:
                last = datetime.fromtimestamp(r["last_seen"], tz=timezone.utc).isoformat().replace("+00:00", "Z")
                depts = []
                try:
                    depts = json.loads(r["departments"] or "[]")
                except Exception:
                    pass
                result.append({
                    "question": r["question"],
                    "count": int(r["cnt"]),
                    "last_seen": last,
                    "departments": depts,
                })
            return result
        finally:
            conn.close()


def _percentile(sorted_vals: list[int], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return float(sorted_vals[f])
    return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])
