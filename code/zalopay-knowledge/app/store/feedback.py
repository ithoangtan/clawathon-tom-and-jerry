from __future__ import annotations

"""Feedback store — correlates thumbs up/down with audit feedback_ids."""

import logging
import sqlite3
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class FeedbackStore:
    """SQLite store at ``{index_dir}/feedback.db``."""

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
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    user_id TEXT,
                    rating TEXT NOT NULL,
                    comment TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def register_pending(self, feedback_id: str) -> None:
        """Record a feedback_id issued by the respond node."""
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO pending_feedback (feedback_id, created_at) VALUES (?, ?)",
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
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM pending_feedback WHERE feedback_id = ?",
                (feedback_id,),
            ).fetchone()
            if not row:
                return False
            conn.execute(
                """
                INSERT OR REPLACE INTO feedback (feedback_id, created_at, user_id, rating, comment)
                VALUES (?, ?, ?, ?, ?)
                """,
                (feedback_id, time.time(), user_id, rating, comment),
            )
            conn.execute("DELETE FROM pending_feedback WHERE feedback_id = ?", (feedback_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    def counts(self) -> tuple[int, int]:
        """Return (thumbs_up, thumbs_down) totals."""
        conn = self._connect()
        try:
            up = conn.execute(
                "SELECT COUNT(*) AS n FROM feedback WHERE rating = 'up'"
            ).fetchone()["n"]
            down = conn.execute(
                "SELECT COUNT(*) AS n FROM feedback WHERE rating = 'down'"
            ).fetchone()["n"]
            return int(up), int(down)
        finally:
            conn.close()
