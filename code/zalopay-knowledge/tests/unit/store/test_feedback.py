from __future__ import annotations

from app.store.db import get_connection
from app.store.feedback import FeedbackStore


def _count_pending() -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM pending_feedback")
            return cur.fetchone()["n"]
    finally:
        conn.close()


def _fetch_feedback(feedback_id: str) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM feedback WHERE feedback_id = %s", (feedback_id,))
            return cur.fetchone()
    finally:
        conn.close()


def _fetch_pending(feedback_id: str) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS found FROM pending_feedback WHERE feedback_id = %s", (feedback_id,))
            return cur.fetchone()
    finally:
        conn.close()


class TestFeedbackSubmit:
    def test_submit_thumbs_up(self, feedback_store: FeedbackStore) -> None:
        feedback_id = "fb-up-001"
        feedback_store.register_pending(feedback_id)

        ok = feedback_store.submit(
            feedback_id=feedback_id,
            user_id="u1",
            rating="up",
            comment="Helpful answer",
        )
        assert ok is True
        up, down = feedback_store.counts()
        assert up == 1
        assert down == 0

    def test_submit_thumbs_down(self, feedback_store: FeedbackStore) -> None:
        feedback_id = "fb-down-001"
        feedback_store.register_pending(feedback_id)

        ok = feedback_store.submit(
            feedback_id=feedback_id,
            user_id="u2",
            rating="down",
            comment=None,
        )
        assert ok is True
        up, down = feedback_store.counts()
        assert up == 0
        assert down == 1

    def test_submit_unknown_feedback_id_returns_false(
        self, feedback_store: FeedbackStore
    ) -> None:
        ok = feedback_store.submit(
            feedback_id="never-registered",
            user_id="u1",
            rating="up",
            comment=None,
        )
        assert ok is False
        assert feedback_store.counts() == (0, 0)

    def test_submit_removes_pending_entry(self, feedback_store: FeedbackStore) -> None:
        feedback_id = "fb-pending-clear"
        feedback_store.register_pending(feedback_id)
        feedback_store.submit(
            feedback_id=feedback_id,
            user_id="u1",
            rating="up",
            comment=None,
        )

        assert _fetch_pending(feedback_id) is None
        row = _fetch_feedback(feedback_id)
        assert row is not None
        assert row["rating"] == "up"
        assert row["user_id"] == "u1"

    def test_resubmit_updates_rating(self, feedback_store: FeedbackStore) -> None:
        feedback_id = "fb-resubmit"
        feedback_store.register_pending(feedback_id)
        feedback_store.submit(
            feedback_id=feedback_id,
            user_id="u1",
            rating="up",
            comment="first",
        )
        feedback_store.register_pending(feedback_id)
        feedback_store.submit(
            feedback_id=feedback_id,
            user_id="u1",
            rating="down",
            comment="changed mind",
        )
        up, down = feedback_store.counts()
        assert up == 0
        assert down == 1


class TestFeedbackCorrelation:
    def test_register_pending_is_idempotent(self, feedback_store: FeedbackStore) -> None:
        feedback_id = "fb-idempotent"
        feedback_store.register_pending(feedback_id)
        feedback_store.register_pending(feedback_id)

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM pending_feedback WHERE feedback_id = %s",
                    (feedback_id,),
                )
                count = cur.fetchone()["n"]
        finally:
            conn.close()
        assert count == 1

    def test_multiple_feedback_ids_tracked_independently(
        self, feedback_store: FeedbackStore
    ) -> None:
        ids = ["fb-a", "fb-b", "fb-c"]
        for fid in ids:
            feedback_store.register_pending(fid)

        feedback_store.submit(feedback_id="fb-a", user_id="u1", rating="up", comment=None)
        feedback_store.submit(feedback_id="fb-b", user_id="u1", rating="down", comment=None)
        # fb-c remains pending

        up, down = feedback_store.counts()
        assert up == 1
        assert down == 1

        assert _count_pending() == 1
