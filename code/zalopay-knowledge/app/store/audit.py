from __future__ import annotations

"""Append-only audit log for queries, answers, and refusals."""

import json
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from app.common.pii import mask_pii

logger = logging.getLogger(__name__)


class AuditStore:
    """SQLite-backed audit log at ``{index_dir}/audit.db``."""

    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self.ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_schema(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS queries (
                    id TEXT PRIMARY KEY,
                    ts REAL NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    role TEXT,
                    question TEXT,
                    departments TEXT,
                    status TEXT,
                    confidence REAL,
                    latency_ms INTEGER,
                    feedback_id TEXT,
                    citations_json TEXT,
                    answer_preview TEXT,
                    tokens INTEGER DEFAULT 0,
                    model_used TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_queries_ts ON queries (ts DESC)")
            # Migrate older schemas created before answer_preview existed.
            columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(queries)").fetchall()
            }
            if "answer_preview" not in columns:
                conn.execute("ALTER TABLE queries ADD COLUMN answer_preview TEXT")
            if "stage_trace_json" not in columns:
                conn.execute("ALTER TABLE queries ADD COLUMN stage_trace_json TEXT")
            if "model_used" not in columns:
                conn.execute("ALTER TABLE queries ADD COLUMN model_used TEXT")
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
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO queries (
                    id, ts, user_id, session_id, role, question, departments,
                    status, confidence, latency_ms, feedback_id, citations_json,
                    answer_preview, tokens, stage_trace_json, model_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        conn = self._connect()
        try:
            total = conn.execute("SELECT COUNT(*) AS n FROM queries").fetchone()["n"]
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

            refused = conn.execute(
                "SELECT COUNT(*) AS n FROM queries WHERE status = 'refused'"
            ).fetchone()["n"]
            partial = conn.execute(
                "SELECT COUNT(*) AS n FROM queries WHERE status = 'partial'"
            ).fetchone()["n"]
            answered = conn.execute(
                "SELECT COUNT(*) AS n FROM queries WHERE status = 'answered'"
            ).fetchone()["n"]
            latencies = [
                r["latency_ms"]
                for r in conn.execute("SELECT latency_ms FROM queries ORDER BY ts").fetchall()
            ]
            tokens = conn.execute("SELECT COALESCE(SUM(tokens), 0) AS t FROM queries").fetchone()["t"]

            history_rows = conn.execute(
                """
                SELECT ts, question, departments, status, confidence, latency_ms, model_used
                FROM queries ORDER BY ts DESC LIMIT ?
                """,
                (history_limit,),
            ).fetchall()

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
                "conflict_rate": 0.0,  # filled by feedback store if needed
                "latency_p50_ms": float(p50),
                "latency_p95_ms": float(p95),
                "feedback_up": 0,
                "feedback_down": 0,
                "total_tokens": int(tokens),
                "history": history,
            }
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
