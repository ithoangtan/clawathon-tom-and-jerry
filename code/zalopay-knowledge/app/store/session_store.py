from __future__ import annotations

"""Shared session thread store — persists chat history in MySQL.

All browsers hitting the same backend see the same session list.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.store.db import get_connection, ensure_index

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id        VARCHAR(36)   NOT NULL,
    title             VARCHAR(500),
    messages_json     MEDIUMTEXT    NOT NULL,
    target_departments_json TEXT    NOT NULL,
    target_auto_route TINYINT(1)    NOT NULL DEFAULT 1,
    created_at        VARCHAR(50)   NOT NULL,
    updated_at        VARCHAR(50)   NOT NULL,
    workflow_id       VARCHAR(200)  DEFAULT NULL,
    jira_key          VARCHAR(50)   DEFAULT NULL,
    processing_status VARCHAR(20)   DEFAULT NULL,
    PRIMARY KEY (session_id)
) CHARACTER SET utf8mb4
"""

# Migration: add new columns to tables created before workflow support was added.
_MIGRATION_COLS = [
    ("workflow_id", "ALTER TABLE chat_sessions ADD COLUMN workflow_id VARCHAR(200) DEFAULT NULL"),
    ("jira_key", "ALTER TABLE chat_sessions ADD COLUMN jira_key VARCHAR(50) DEFAULT NULL"),
    ("processing_status", "ALTER TABLE chat_sessions ADD COLUMN processing_status VARCHAR(20) DEFAULT NULL"),
]


class SessionStore:
    """MySQL-backed store for shared chat session threads."""

    def __init__(self) -> None:
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(_CREATE_TABLE)
                # Add missing columns for existing deployments.
                cur.execute("SHOW COLUMNS FROM chat_sessions")
                existing_cols = {row["Field"] for row in cur.fetchall()}
                for col_name, alter_sql in _MIGRATION_COLS:
                    if col_name not in existing_cols:
                        cur.execute(alter_sql)
                        logger.info("SessionStore migration: added column %r", col_name)
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

    def create_processing_session(
        self,
        *,
        session_id: str,
        title: str,
        workflow_id: str,
        jira_key: str,
    ) -> None:
        """Create a session for a webhook-triggered workflow run (processing state).

        The session starts with no messages and ``processing_status='processing'``.
        The sidebar polls for it and shows a "Đang xử lý..." badge until the
        status transitions to ``'done'`` or ``'error'``.
        """
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_sessions
                        (session_id, title, messages_json, target_departments_json,
                         target_auto_route, created_at, updated_at,
                         workflow_id, jira_key, processing_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        workflow_id = VALUES(workflow_id),
                        jira_key = VALUES(jira_key),
                        processing_status = VALUES(processing_status),
                        updated_at = VALUES(updated_at)
                    """,
                    (
                        session_id, title, "[]", "[]", 1, now, now,
                        workflow_id, jira_key, "processing",
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def update_messages(self, session_id: str, messages: list) -> None:
        """Replace messages_json for a session (used for incremental progress updates)."""
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE chat_sessions SET messages_json=%s, updated_at=%s WHERE session_id=%s",
                    (json.dumps(messages, ensure_ascii=False), now, session_id),
                )
            conn.commit()
        finally:
            conn.close()

    def update_processing_status(
        self,
        session_id: str,
        status: str,
    ) -> None:
        """Update ``processing_status`` after a webhook workflow run completes."""
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE chat_sessions SET processing_status=%s, updated_at=%s WHERE session_id=%s",
                    (status, now, session_id),
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
            "workflowId": row.get("workflow_id"),
            "jiraKey": row.get("jira_key"),
            "processingStatus": row.get("processing_status"),
        }
