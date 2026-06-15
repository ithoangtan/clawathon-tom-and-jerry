from __future__ import annotations

"""MySQLCheckpointer — MySQL-backed LangGraph BaseCheckpointSaver.

Replaces SqliteCheckpointer when MySQL credentials are configured so that
conversation state (multi-turn threads) persists across container restarts.

Tables created on first use:
  lg_checkpoints       — one row per (thread_id, checkpoint_ns, checkpoint_id)
  lg_checkpoint_writes — pending channel writes for each checkpoint
"""

import json
import logging
from typing import Any, Iterator, Optional, Sequence

logger = logging.getLogger(__name__)

_CREATE_CHECKPOINTS = """
CREATE TABLE IF NOT EXISTS lg_checkpoints (
    thread_id            VARCHAR(191) NOT NULL,
    checkpoint_ns        VARCHAR(191) NOT NULL DEFAULT '',
    checkpoint_id        VARCHAR(191) NOT NULL,
    parent_checkpoint_id VARCHAR(191),
    type                 VARCHAR(50),
    checkpoint           MEDIUMBLOB   NOT NULL,
    metadata             MEDIUMTEXT,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
) CHARACTER SET utf8mb4
"""

_CREATE_WRITES = """
CREATE TABLE IF NOT EXISTS lg_checkpoint_writes (
    thread_id     VARCHAR(191) NOT NULL,
    checkpoint_ns VARCHAR(191) NOT NULL DEFAULT '',
    checkpoint_id VARCHAR(191) NOT NULL,
    task_id       VARCHAR(191) NOT NULL,
    idx           INT          NOT NULL,
    channel       VARCHAR(255) NOT NULL,
    type          VARCHAR(50),
    value         MEDIUMBLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
) CHARACTER SET utf8mb4
"""


class MySQLCheckpointer:
    """Port wrapper: provides ``get_saver()`` → :class:`_MySQLSaver`.

    Usage is identical to :class:`~app.adapters.sqlite_checkpointer.SqliteCheckpointer`:
    ``deps.py`` calls ``checkpointer.get_saver()`` and passes the result to LangGraph.
    """

    def __init__(self, settings=None) -> None:
        from app.config import get_settings

        self._cfg = settings or get_settings()
        self._saver: _MySQLSaver | None = None

    def get_saver(self) -> "_MySQLSaver":
        if self._saver is None:
            self._saver = _MySQLSaver()
            logger.info("MySQLSaver ready (thread state persists in MySQL)")
        return self._saver

    def healthy(self) -> bool:
        try:
            from app.store.db import get_connection

            conn = get_connection()
            conn.close()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("MySQLCheckpointer unhealthy: %s", exc)
            return False


def _load_metadata(saver, raw: str | None) -> dict:
    """Deserialize metadata stored by _MySQLSaver.put().

    Supports two formats:
    - New: ``"<serde_type>||<hex_bytes>"`` — written by the serde-aware put().
    - Legacy: plain JSON string — written by the old json.dumps() put().
    """
    if not raw:
        return {}
    if "||" in raw:
        mt, mhex = raw.split("||", 1)
        return saver.serde.loads_typed((mt, bytes.fromhex(mhex)))  # type: ignore[attr-defined]
    return json.loads(raw)


# ── Inner saver: BaseCheckpointSaver impl ─────────────────────────────────────


class _MySQLSaver:
    """LangGraph ``BaseCheckpointSaver`` backed by MySQL.

    Inherits from ``BaseCheckpointSaver`` so LangGraph can use it directly as
    a checkpointer.  The ``serde`` attribute (``JsonPlusSerializer``) is inherited
    from the base class and used for checkpoint / write serialisation.
    """

    def __init__(self) -> None:
        try:
            from langgraph.checkpoint.base import BaseCheckpointSaver

            # Dynamically subclass so we get the serde + helper methods
            # without a compile-time import that would fail outside Docker.
            self.__class__ = type(
                "_MySQLSaverLG",
                (self.__class__, BaseCheckpointSaver),
                {},
            )
            BaseCheckpointSaver.__init__(self)  # type: ignore[call-arg]
        except Exception as exc:
            logger.warning("Could not inherit BaseCheckpointSaver: %s", exc)
        self._ensure_schema()

    def _connect(self):
        from app.store.db import get_connection

        return get_connection()

    def _ensure_schema(self) -> None:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(_CREATE_CHECKPOINTS)
                cur.execute(_CREATE_WRITES)
            conn.commit()
        finally:
            conn.close()

    # ── BaseCheckpointSaver interface ─────────────────────────────────────────

    def get_tuple(self, config: dict) -> Optional[Any]:
        from langgraph.checkpoint.base import CheckpointTuple

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                if checkpoint_id:
                    cur.execute(
                        "SELECT thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, "
                        "type, checkpoint, metadata FROM lg_checkpoints "
                        "WHERE thread_id=%s AND checkpoint_ns=%s AND checkpoint_id=%s",
                        (thread_id, checkpoint_ns, checkpoint_id),
                    )
                else:
                    cur.execute(
                        "SELECT thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, "
                        "type, checkpoint, metadata FROM lg_checkpoints "
                        "WHERE thread_id=%s AND checkpoint_ns=%s "
                        "ORDER BY checkpoint_id DESC LIMIT 1",
                        (thread_id, checkpoint_ns),
                    )
                row = cur.fetchone()
                if not row:
                    return None

                cur.execute(
                    "SELECT task_id, channel, type, value FROM lg_checkpoint_writes "
                    "WHERE thread_id=%s AND checkpoint_ns=%s AND checkpoint_id=%s ORDER BY idx",
                    (thread_id, checkpoint_ns, row["checkpoint_id"]),
                )
                write_rows = cur.fetchall()
        finally:
            conn.close()

        cp_data = bytes(row["checkpoint"]) if row["checkpoint"] else b""
        checkpoint = self.serde.loads_typed((row["type"], cp_data))  # type: ignore[attr-defined]
        metadata = _load_metadata(self, row["metadata"])
        pending = [
            (
                wr["task_id"],
                wr["channel"],
                self.serde.loads_typed((wr["type"], bytes(wr["value"]) if wr["value"] else b"")),  # type: ignore[attr-defined]
            )
            for wr in write_rows
        ]
        parent_config = (
            {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": row["parent_checkpoint_id"],
                }
            }
            if row["parent_checkpoint_id"]
            else None
        )
        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": row["checkpoint_id"],
                }
            },
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=parent_config,
            pending_writes=pending or None,
        )

    def list(
        self,
        config: Optional[dict],
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Any]:
        from langgraph.checkpoint.base import CheckpointTuple

        if config is None:
            return
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        limit_clause = f" LIMIT {int(limit)}" if limit else ""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                if before:
                    before_id = before["configurable"]["checkpoint_id"]
                    cur.execute(
                        "SELECT thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, "
                        "type, checkpoint, metadata FROM lg_checkpoints "
                        "WHERE thread_id=%s AND checkpoint_ns=%s AND checkpoint_id < %s "
                        f"ORDER BY checkpoint_id DESC{limit_clause}",
                        (thread_id, checkpoint_ns, before_id),
                    )
                else:
                    cur.execute(
                        "SELECT thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, "
                        "type, checkpoint, metadata FROM lg_checkpoints "
                        "WHERE thread_id=%s AND checkpoint_ns=%s "
                        f"ORDER BY checkpoint_id DESC{limit_clause}",
                        (thread_id, checkpoint_ns),
                    )
                rows = cur.fetchall()
        finally:
            conn.close()

        for row in rows:
            cp_data = bytes(row["checkpoint"]) if row["checkpoint"] else b""
            checkpoint = self.serde.loads_typed((row["type"], cp_data))  # type: ignore[attr-defined]
            metadata = _load_metadata(self, row["metadata"])
            parent_config = (
                {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": row["parent_checkpoint_id"],
                    }
                }
                if row["parent_checkpoint_id"]
                else None
            )
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": row["checkpoint_id"],
                    }
                },
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=parent_config,
                pending_writes=None,
            )

    def put(
        self,
        config: dict,
        checkpoint: dict,
        metadata: dict,
        new_versions: Any = None,
    ) -> dict:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = checkpoint["id"]
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")

        type_, cp_bytes = self.serde.dumps_typed(checkpoint)  # type: ignore[attr-defined]
        # Use serde for metadata too — LangGraph 0.2.x can put LangChain
        # message objects (HumanMessage, etc.) into metadata, which plain
        # json.dumps() cannot handle.
        meta_type, meta_bytes = self.serde.dumps_typed(metadata)  # type: ignore[attr-defined]
        meta_str = meta_type + "||" + meta_bytes.hex()

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO lg_checkpoints
                        (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        parent_checkpoint_id = VALUES(parent_checkpoint_id),
                        type                 = VALUES(type),
                        checkpoint           = VALUES(checkpoint),
                        metadata             = VALUES(metadata)
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type_, cp_bytes, meta_str),
                )
            conn.commit()
        finally:
            conn.close()

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
        self,
        config: dict,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
    ) -> None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                for idx, (channel, value) in enumerate(writes):
                    type_, val_bytes = self.serde.dumps_typed(value)  # type: ignore[attr-defined]
                    cur.execute(
                        """
                        INSERT INTO lg_checkpoint_writes
                            (thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, type, value)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            channel = VALUES(channel),
                            type    = VALUES(type),
                            value   = VALUES(value)
                        """,
                        (thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, type_, val_bytes),
                    )
            conn.commit()
        finally:
            conn.close()

    def setup(self) -> None:
        """Alias for _ensure_schema — called by some LangGraph versions."""
        self._ensure_schema()
