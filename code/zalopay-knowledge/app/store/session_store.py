from __future__ import annotations

"""Shared session thread store — persists chat history in MySQL.

All browsers hitting the same backend see the same session list.
"""

import json
import logging
from typing import Any

from app.store.db import get_connection, ensure_index

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id        VARCHAR(36)   NOT NULL,
    title             VARCHAR(500),
    messages_json     MEDIUMTEXT    NOT NULL,
    target_departments_json TEXT    NOT NULL DEFAULT '[]',
    target_auto_route TINYINT(1)    NOT NULL DEFAULT 1,
    created_at        VARCHAR(50)   NOT NULL,
    updated_at        VARCHAR(50)   NOT NULL,
    PRIMARY KEY (session_id)
) CHARACTER SET utf8mb4
"""


class SessionStore:
    """MySQL-backed store for shared chat session threads."""

    def __init__(self) -> None:
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(_CREATE_TABLE)
            ensure_index(conn, "chat_sessions", "idx_sessions_updated_at", "updated_at DESC")
            conn.commit()
        except Exception:
            logger.exception("SessionStore schema init failed")
        finally:
            conn.close()

    def upsert(self, thread: dict[str, Any]) -> None:
        """Insert or replace a session thread record."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_sessions
                        (session_id, title, messages_json, target_departments_json,
                         target_auto_route, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        messages_json = VALUES(messages_json),
                        target_departments_json = VALUES(target_departments_json),
                        target_auto_route = VALUES(target_auto_route),
                        updated_at = VALUES(updated_at)
                    """,
                    (
                        thread["sessionId"],
                        thread.get("title"),
                        json.dumps(thread.get("messages", []), ensure_ascii=False),
                        json.dumps(thread.get("targetDepartments", []), ensure_ascii=False),
                        1 if thread.get("targetAutoRoute", True) else 0,
                        thread.get("createdAt", ""),
                        thread.get("updatedAt", ""),
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def delete(self, session_id: str) -> None:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))
            conn.commit()
        finally:
            conn.close()

    def list_all(self) -> list[dict[str, Any]]:
        """Return all threads ordered by updated_at DESC."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM chat_sessions ORDER BY updated_at DESC"
                )
                rows = cur.fetchall()
            return [self._row_to_thread(r) for r in rows]
        finally:
            conn.close()

    def _row_to_thread(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "sessionId": row["session_id"],
            "title": row["title"],
            "messages": json.loads(row["messages_json"] or "[]"),
            "targetDepartments": json.loads(row["target_departments_json"] or "[]"),
            "targetAutoRoute": bool(row["target_auto_route"]),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }
