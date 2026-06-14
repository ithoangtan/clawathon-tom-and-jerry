from __future__ import annotations

"""Feedback store — correlates thumbs up/down with audit feedback_ids."""

import logging
import time

from app.store.db import get_connection

logger = logging.getLogger(__name__)


class FeedbackStore:
    """MySQL-backed feedback store (tables ``feedback`` and ``pending_feedback``)."""

    def __init__(self) -> None:
        self.ensure_schema()

    def ensure_schema(self) -> None:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS feedback (
                        feedback_id  VARCHAR(36)  NOT NULL,
                        created_at   DOUBLE       NOT NULL,
                        user_id      VARCHAR(255),
                        rating       VARCHAR(10)  NOT NULL,
                        comment      TEXT,
                        PRIMARY KEY (feedback_id)
                    ) CHARACTER SET utf8mb4
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pending_feedback (
                        feedback_id  VARCHAR(36)  NOT NULL,
                        created_at   DOUBLE       NOT NULL,
                        PRIMARY KEY (feedback_id)
                    ) CHARACTER SET utf8mb4
                    """
                )
            conn.commit()
        finally:
            conn.close()

    def register_pending(self, feedback_id: str) -> None:
        """Record a feedback_id issued by the respond node."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT IGNORE INTO pending_feedback (feedback_id, created_at) VALUES (%s, %s)",
                    (feedback_id, time.time()),
                )
            conn.commit()
        finally:
            conn.close()

    def submit(
        self,
        *,
        feedback_id: str,
        user_id: str,
        rating: str,
        comment: str | None,
    ) -> bool:
        """Submit feedback. Returns False if feedback_id is unknown."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pending_feedback WHERE feedback_id = %s",
                    (feedback_id,),
                )
                if not cur.fetchone():
                    return False
                cur.execute(
                    """
                    REPLACE INTO feedback (feedback_id, created_at, user_id, rating, comment)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (feedback_id, time.time(), user_id, rating, comment),
                )
                cur.execute(
                    "DELETE FROM pending_feedback WHERE feedback_id = %s",
                    (feedback_id,),
                )
            conn.commit()
            return True
        finally:
            conn.close()

    def counts(self) -> tuple[int, int]:
        """Return (thumbs_up, thumbs_down) totals."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS n FROM feedback WHERE rating = 'up'")
                up = cur.fetchone()["n"]
                cur.execute("SELECT COUNT(*) AS n FROM feedback WHERE rating = 'down'")
                down = cur.fetchone()["n"]
            return int(up), int(down)
        finally:
            conn.close()

    def feedback_gaps(self, *, limit: int = 20) -> list[dict]:
        """Return documents with most 👎 feedback, joined with audit citations."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT q.citations_json, f.rating
                    FROM feedback f
                    JOIN queries q ON q.feedback_id = f.feedback_id
                    WHERE q.citations_json IS NOT NULL
                    ORDER BY f.created_at DESC
                    LIMIT 200
                    """
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        import json
        doc_stats: dict[str, dict] = {}
        for row in rows:
            try:
                citations = json.loads(row["citations_json"] or "[]")
            except Exception:
                citations = []
            for cit in citations:
                title = cit.get("title", "")
                url = cit.get("url", "")
                if not title:
                    continue
                key = url or title
                if key not in doc_stats:
                    doc_stats[key] = {"title": title, "url": url, "up": 0, "down": 0}
                if row["rating"] == "up":
                    doc_stats[key]["up"] += 1
                else:
                    doc_stats[key]["down"] += 1

        # Sort by down count descending, include only docs with any down
        result = [v for v in doc_stats.values() if v["down"] > 0]
        result.sort(key=lambda x: x["down"], reverse=True)
        return result[:limit]
