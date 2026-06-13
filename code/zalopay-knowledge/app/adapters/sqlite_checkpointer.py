from __future__ import annotations

"""SqliteCheckpointer — the local :class:`CheckpointerPort` implementation.

Wraps LangGraph's ``SqliteSaver`` so the graph can persist conversation state
(STM) to a file under ``INDEX_DIR`` during local / docker-compose development.
On AgentBase this is swapped for :class:`AgentBaseCheckpointer` via deps.py —
graph code never sees the difference because it only touches the port.

The saver is created once and cached: ``SqliteSaver`` holds an open SQLite
connection, and LangGraph reads/writes checkpoints through it across many
requests, so we must not rebuild it per call.  The connection is opened with
``check_same_thread=False`` because LangGraph may touch it from worker threads.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class SqliteCheckpointer:
    """Provides a file-backed ``SqliteSaver`` for local runs."""

    def __init__(self, db_path: str | Path) -> None:
        """Bind to *db_path* (e.g. ``{index_dir}/checkpoints.db``)."""
        self._path = Path(db_path)
        self._saver = None  # lazily built BaseCheckpointSaver

    def get_saver(self):
        """Return a cached LangGraph ``SqliteSaver`` (created on first call)."""
        if self._saver is not None:
            return self._saver

        from langgraph.checkpoint.sqlite import SqliteSaver

        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._path), check_same_thread=False)
        saver = SqliteSaver(conn)
        saver.setup()  # idempotent: creates the checkpoint tables if absent
        self._saver = saver
        logger.info("SqliteSaver ready at %s", self._path)
        return saver

    def healthy(self) -> bool:
        """True when the checkpoint DB is reachable and writable. Never raises."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self._path), check_same_thread=False)
            try:
                conn.execute("SELECT 1")
                return True
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001 — health check must not raise
            logger.warning("SqliteCheckpointer unhealthy: %s", exc)
            return False
