from __future__ import annotations

"""MetaStore — the SQLite metadata DB that backs the FAISS retriever.

The corpus index is two files per ``INDEX_DIR`` (see 03-ARCHITECTURE.md §5):

* ``faiss/{department}.faiss`` — the dense vectors (one IndexFlatIP per department).
* ``meta.db``                  — this store: one ``chunks`` row per indexed chunk.

The **contract** between the two: within a department, a chunk's FAISS row
position equals its ``vec_pos`` column here.  The FAISS adapter searches the
vectors, gets back row positions, and resolves them to chunk metadata through
:meth:`MetaStore.fetch_by_positions`.

This module is read-mostly: the (future) ingestion job calls
:meth:`ensure_schema` and writes rows; the retriever only reads.  We open a
fresh connection per call rather than sharing one, because concurrent
department subgraph branches each query in their own thread and a single
``sqlite3.Connection`` is not safe to share across threads.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# Columns mirror app.ports.types.RetrievedChunk (minus ``score``, which is
# produced at search time).  Order matters: it is reused by row factories.
CHUNK_COLUMNS: tuple[str, ...] = (
    "chunk_id",
    "department",
    "vec_pos",
    "doc_type",
    "title",
    "source",
    "url",
    "anchor",
    "section",
    "space",
    "labels",
    "last_modified",
    "author",
    "acl",
    "lifecycle_state",
    "source_type",
    "page",
    "text",
)

# Added after initial MVP schema; applied idempotently by :meth:`MetaStore.ensure_schema`.
_SCHEMA_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("source", "TEXT"),
    ("anchor", "TEXT"),
    ("space", "TEXT"),
    ("labels", "TEXT"),
    ("author", "TEXT"),
    ("acl", "TEXT"),
)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id        TEXT PRIMARY KEY,
    department      TEXT NOT NULL,
    vec_pos         INTEGER NOT NULL,
    doc_type        TEXT,
    title           TEXT,
    source          TEXT,
    url             TEXT,
    anchor          TEXT,
    section         TEXT,
    space           TEXT,
    labels          TEXT,
    last_modified   TEXT,
    author          TEXT,
    acl             TEXT,
    lifecycle_state TEXT NOT NULL DEFAULT 'active',
    source_type     TEXT,
    page            INTEGER,
    text            TEXT NOT NULL
)
"""

_CREATE_POS_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_chunks_dept_pos ON chunks (department, vec_pos)"
)
_CREATE_LIFECYCLE_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_chunks_dept_lifecycle "
    "ON chunks (department, lifecycle_state)"
)

_CREATE_SYNC_SOURCES = """
CREATE TABLE IF NOT EXISTS sync_sources (
    department      TEXT NOT NULL,
    url             TEXT NOT NULL,
    source_id       TEXT,
    content_hash    TEXT NOT NULL,
    last_modified   TEXT,
    synced_at       TEXT,
    PRIMARY KEY (department, url)
)
"""


class MetaStore:
    """Thin SQLite accessor for chunk metadata at ``{index_dir}/meta.db``."""

    def __init__(self, db_path: str | Path) -> None:
        """Bind the store to *db_path* (the file need not exist yet)."""
        self._path = Path(db_path)

    # ── Connection ──────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        """Open a new read-capable connection (caller closes it).

        We pass ``check_same_thread=False`` defensively, but each connection is
        used and closed within a single call so it never actually crosses
        threads.  ``Row`` factory gives us name-based column access.
        """
        conn = sqlite3.connect(str(self._path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Schema (used by the ingestion job, idempotent) ───────────────────────

    def ensure_schema(self) -> None:
        """Create the ``chunks`` table and its indexes if absent.

        Safe to call on every ingestion run.  Creates the parent directory and
        the DB file if they don't exist.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute(_CREATE_TABLE)
            self._apply_migrations(conn)
            conn.execute(_CREATE_POS_INDEX)
            conn.execute(_CREATE_LIFECYCLE_INDEX)
            conn.execute(_CREATE_SYNC_SOURCES)
            conn.commit()
        finally:
            conn.close()

    def _apply_migrations(self, conn: sqlite3.Connection) -> None:
        """Add columns introduced after the initial schema (idempotent)."""
        existing = {
            row[1]
            for row in conn.execute("PRAGMA table_info(chunks)").fetchall()
        }
        for column, typedef in _SCHEMA_MIGRATIONS:
            if column not in existing:
                conn.execute(f"ALTER TABLE chunks ADD COLUMN {column} {typedef}")

    # ── Reads (used by the retriever) ─────────────────────────────────────────

    def exists(self) -> bool:
        """Return True when the DB file is present and holds at least one chunk.

        Never raises — a missing/corrupt DB is reported as "no data" so the
        retriever can degrade to a clean refusal.
        """
        if not self._path.exists():
            return False
        conn = self._connect()
        try:
            row = conn.execute("SELECT 1 FROM chunks LIMIT 1").fetchone()
            return row is not None
        except sqlite3.Error as exc:
            logger.warning("MetaStore.exists() query failed: %s", exc)
            return False
        finally:
            conn.close()

    def count(self, department: str) -> int:
        """Return the number of chunks indexed for *department* (0 on any error)."""
        if not self._path.exists():
            return 0
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM chunks WHERE department = ?",
                (department,),
            ).fetchone()
            return int(row["n"]) if row else 0
        except sqlite3.Error as exc:
            logger.warning("MetaStore.count(%s) failed: %s", department, exc)
            return 0
        finally:
            conn.close()

    def departments_with_data(self) -> list[str]:
        """Return the distinct department keys that have at least one chunk."""
        if not self._path.exists():
            return []
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT DISTINCT department FROM chunks ORDER BY department"
            ).fetchall()
            return [r["department"] for r in rows]
        except sqlite3.Error as exc:
            logger.warning("MetaStore.departments_with_data() failed: %s", exc)
            return []
        finally:
            conn.close()

    def fetch_by_positions(
        self, department: str, positions: list[int]
    ) -> dict[int, dict]:
        """Resolve FAISS row *positions* to chunk metadata for *department*.

        Args:
            department: Department partition the positions index into.
            positions: FAISS row positions returned by a vector search.

        Returns:
            ``{vec_pos: {column: value, ...}}`` for every position that resolves
            to a row.  Positions with no matching row are simply absent from the
            result (e.g. a stale FAISS index referencing deleted chunks).
        """
        if not positions or not self._path.exists():
            return {}
        # Deduplicate while preserving nothing — order is reapplied by the caller.
        unique = list({int(p) for p in positions if p >= 0})
        if not unique:
            return {}

        placeholders = ",".join("?" for _ in unique)
        sql = (
            f"SELECT {', '.join(CHUNK_COLUMNS)} FROM chunks "
            f"WHERE department = ? AND vec_pos IN ({placeholders})"
        )
        conn = self._connect()
        try:
            rows = conn.execute(sql, (department, *unique)).fetchall()
        except sqlite3.Error as exc:
            logger.warning(
                "MetaStore.fetch_by_positions(%s) failed: %s", department, exc
            )
            return {}
        finally:
            conn.close()

        return {int(r["vec_pos"]): dict(r) for r in rows}

    def fetch_chunks_by_url(
        self, department: str, url: str, *, active_only: bool = False
    ) -> list[dict]:
        """Return chunk rows for a single source URL within *department*."""
        if not url or not self._path.exists():
            return []
        sql = (
            f"SELECT {', '.join(CHUNK_COLUMNS)} FROM chunks "
            "WHERE department = ? AND url = ?"
        )
        params: list[object] = [department, url]
        if active_only:
            sql += " AND lifecycle_state = 'active'"
        sql += " ORDER BY vec_pos"
        conn = self._connect()
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error as exc:
            logger.warning(
                "MetaStore.fetch_chunks_by_url(%s) failed: %s", department, exc
            )
            return []
        finally:
            conn.close()

    def get_source_hash(self, department: str, url: str) -> str | None:
        """Return the last indexed content hash for *url*, or None when unknown."""
        if not url or not self._path.exists():
            return None
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT content_hash FROM sync_sources WHERE department = ? AND url = ?",
                (department, url),
            ).fetchone()
            return str(row["content_hash"]) if row else None
        except sqlite3.Error as exc:
            logger.warning("MetaStore.get_source_hash(%s) failed: %s", department, exc)
            return None
        finally:
            conn.close()

    # ── Writes (used by the ingestion job) ────────────────────────────────────

    def replace_department_chunks(self, department: str, rows: list[dict]) -> int:
        """Replace all chunks for *department* with *rows*.

        Each row must include all :data:`CHUNK_COLUMNS` keys.  Returns the number
        of rows written.
        """
        self.ensure_schema()
        conn = self._connect()
        try:
            conn.execute("DELETE FROM chunks WHERE department = ?", (department,))
            for row in rows:
                conn.execute(
                    f"""
                    INSERT INTO chunks ({', '.join(CHUNK_COLUMNS)})
                    VALUES ({', '.join('?' for _ in CHUNK_COLUMNS)})
                    """,
                    tuple(row[c] for c in CHUNK_COLUMNS),
                )
            conn.commit()
            return len(rows)
        finally:
            conn.close()

    def total_chunks(self) -> int:
        """Return total chunk count across all departments."""
        if not self._path.exists():
            return 0
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()
            return int(row["n"]) if row else 0
        except sqlite3.Error:
            return 0
        finally:
            conn.close()

    # ── Writes (used by the ingestion job) ────────────────────────────────────

    def clear_department(self, department: str) -> None:
        """Remove all chunks for *department* (called before a full re-index)."""
        if not self._path.exists():
            self.ensure_schema()
        conn = self._connect()
        try:
            conn.execute("DELETE FROM chunks WHERE department = ?", (department,))
            conn.commit()
        finally:
            conn.close()

    def upsert_chunks(self, rows: list[dict]) -> None:
        """Insert or replace chunk rows in bulk."""
        if not rows:
            return
        self.ensure_schema()
        conn = self._connect()
        try:
            conn.executemany(
                f"""
                INSERT OR REPLACE INTO chunks (
                    {', '.join(CHUNK_COLUMNS)}
                ) VALUES ({', '.join('?' for _ in CHUNK_COLUMNS)})
                """,
                [
                    tuple(row.get(col) for col in CHUNK_COLUMNS)
                    for row in rows
                ],
            )
            conn.commit()
        finally:
            conn.close()

    def distinct_urls(self, department: str) -> set[str]:
        """Return distinct source URLs indexed for *department*."""
        if not self._path.exists():
            return set()
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT DISTINCT url FROM chunks WHERE department = ? AND url IS NOT NULL",
                (department,),
            ).fetchall()
            return {r["url"] for r in rows if r["url"]}
        except sqlite3.Error as exc:
            logger.warning("MetaStore.distinct_urls(%s) failed: %s", department, exc)
            return set()
        finally:
            conn.close()

    def record_source_hashes(
        self,
        department: str,
        sources: list[dict[str, str | None]],
    ) -> None:
        """Persist content hashes for successfully indexed source URLs."""
        if not sources:
            return
        self.ensure_schema()
        from datetime import datetime, timezone

        synced_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        conn = self._connect()
        try:
            for row in sources:
                url = row.get("url")
                content_hash = row.get("content_hash")
                if not url or not content_hash:
                    continue
                conn.execute(
                    """
                    INSERT INTO sync_sources (
                        department, url, source_id, content_hash, last_modified, synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(department, url) DO UPDATE SET
                        source_id = excluded.source_id,
                        content_hash = excluded.content_hash,
                        last_modified = excluded.last_modified,
                        synced_at = excluded.synced_at
                    """,
                    (
                        department,
                        url,
                        row.get("source_id"),
                        content_hash,
                        row.get("last_modified"),
                        synced_at,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def tombstone_urls(self, department: str, urls: set[str]) -> int:
        """Mark chunks for *urls* as ``sunset`` (soft delete, excluded from search)."""
        if not urls or not self._path.exists():
            return 0
        placeholders = ",".join("?" for _ in urls)
        conn = self._connect()
        try:
            cur = conn.execute(
                f"""
                UPDATE chunks SET lifecycle_state = 'sunset'
                WHERE department = ? AND url IN ({placeholders})
                  AND lifecycle_state != 'sunset'
                """,
                (department, *sorted(urls)),
            )
            conn.execute(
                f"DELETE FROM sync_sources WHERE department = ? AND url IN ({placeholders})",
                (department, *sorted(urls)),
            )
            conn.commit()
            return int(cur.rowcount)
        except sqlite3.Error as exc:
            logger.warning("MetaStore.tombstone_urls(%s) failed: %s", department, exc)
            return 0
        finally:
            conn.close()

    def doc_count(self, department: str | None = None) -> int:
        """Count distinct source documents (by url) optionally filtered by dept."""
        if not self._path.exists():
            return 0
        conn = self._connect()
        try:
            if department:
                row = conn.execute(
                    "SELECT COUNT(DISTINCT url) AS n FROM chunks WHERE department = ?",
                    (department,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(DISTINCT url) AS n FROM chunks"
                ).fetchone()
            return int(row["n"]) if row else 0
        except sqlite3.Error as exc:
            logger.warning("MetaStore.doc_count failed: %s", exc)
            return 0
        finally:
            conn.close()

    def last_synced_at(self, department: str) -> str | None:
        """Return the most recent synced_at timestamp for *department*, or None."""
        if not self._path.exists():
            return None
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT MAX(synced_at) AS ts FROM sync_sources WHERE department = ?",
                (department,),
            ).fetchone()
            return row["ts"] if row and row["ts"] else None
        except sqlite3.Error as exc:
            logger.warning("MetaStore.last_synced_at(%s) failed: %s", department, exc)
            return None
        finally:
            conn.close()
