from __future__ import annotations

"""MySQLSyncStore — MySQL-backed replacement for MetaStore's sync_sources table.

Used when VECTOR_STORE=opensearch so that content-hash dedup state persists
across container restarts.  Chunk counts / doc counts are resolved live from
OpenSearch (the authoritative store in this mode).

The chunks table from MetaStore is NOT replicated here — all chunk data lives
in OpenSearch when VECTOR_STORE=opensearch.
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_CREATE_SYNC_SOURCES = """
CREATE TABLE IF NOT EXISTS sync_sources (
    department    VARCHAR(255) NOT NULL,
    url           TEXT         NOT NULL,
    source_id     VARCHAR(255),
    content_hash  VARCHAR(64)  NOT NULL,
    last_modified VARCHAR(64),
    synced_at     VARCHAR(64),
    PRIMARY KEY (department, url(512))
) CHARACTER SET utf8mb4
"""


class MySQLSyncStore:
    """MySQL-backed sync metadata store for OpenSearch mode.

    Drop-in replacement for :class:`~app.store.meta.MetaStore` for the subset
    of methods used when *VECTOR_STORE=opensearch*.  Chunk stats are delegated
    to OpenSearch; only content-hash dedup state lives in MySQL.
    """

    def __init__(self, settings=None) -> None:
        from app.config import get_settings

        self._cfg = settings or get_settings()
        self._prefix = self._cfg.opensearch_index_prefix
        self._client = None  # lazy OpenSearch client
        self.ensure_schema()

    # ── Connection helpers ────────────────────────────────────────────────────

    def _connect(self):
        from app.store.db import get_connection

        return get_connection()

    def _os_client(self):
        if self._client is not None:
            return self._client
        from opensearchpy import OpenSearch

        self._client = OpenSearch(
            hosts=[{"host": self._cfg.opensearch_host, "port": self._cfg.opensearch_port}],
            http_auth=(self._cfg.opensearch_user, self._cfg.opensearch_password),
            use_ssl=self._cfg.opensearch_use_ssl,
            verify_certs=self._cfg.opensearch_verify_certs,
            ssl_show_warn=False,
        )
        return self._client

    # ── Schema ────────────────────────────────────────────────────────────────

    def ensure_schema(self) -> None:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(_CREATE_SYNC_SOURCES)
            conn.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("MySQLSyncStore.ensure_schema failed: %s", exc)
        finally:
            conn.close()

    # ── Stats (delegate to OpenSearch) ────────────────────────────────────────

    def _index_name(self, department: str) -> str:
        return f"{self._prefix}_{department}"

    def count(self, department: str) -> int:
        """Return the number of non-sunset chunks indexed for *department*."""
        try:
            client = self._os_client()
            index = self._index_name(department)
            if not client.indices.exists(index=index):
                return 0
            resp = client.count(index=index, body={"query": {"term": {"lifecycle_state": "active"}}})
            return int(resp.get("count", 0))
        except Exception as exc:  # noqa: BLE001
            logger.debug("MySQLSyncStore.count(%s) via OpenSearch failed: %s", department, exc)
            return 0

    def departments_with_data(self) -> list[str]:
        """Return department keys that have at least one chunk in OpenSearch."""
        from app.common.departments import iter_keys

        result: list[str] = []
        for dept in iter_keys():
            try:
                if self.count(dept) > 0:
                    result.append(dept)
            except Exception:  # noqa: BLE001
                pass
        return result

    def doc_count(self, department: str | None = None) -> int:
        """Return distinct document count from OpenSearch."""
        try:
            client = self._os_client()
            if department:
                index = self._index_name(department)
                if not client.indices.exists(index=index):
                    return 0
                resp = client.search(
                    index=index,
                    body={
                        "size": 0,
                        "aggs": {"urls": {"cardinality": {"field": "url"}}},
                    },
                )
                return int(
                    resp.get("aggregations", {}).get("urls", {}).get("value", 0)
                )
            from app.common.departments import iter_keys

            total = 0
            for dept in iter_keys():
                total += self.doc_count(dept)
            return total
        except Exception as exc:  # noqa: BLE001
            logger.debug("MySQLSyncStore.doc_count via OpenSearch failed: %s", exc)
            return 0

    def exists(self) -> bool:
        """True when at least one department has data in OpenSearch."""
        return bool(self.departments_with_data())

    # ── Sync-source reads ─────────────────────────────────────────────────────

    def get_source_hash(self, department: str, url: str) -> str | None:
        """Return the last indexed content hash for *url*, or None when unknown."""
        if not url:
            return None
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT content_hash FROM sync_sources WHERE department=%s AND url=%s",
                    (department, url),
                )
                row = cur.fetchone()
                return str(row["content_hash"]) if row else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("MySQLSyncStore.get_source_hash failed: %s", exc)
            return None
        finally:
            conn.close()

    def last_synced_at(self, department: str) -> str | None:
        """Return the most recent synced_at timestamp for *department*, or None."""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT MAX(synced_at) AS ts FROM sync_sources WHERE department=%s",
                    (department,),
                )
                row = cur.fetchone()
                return row["ts"] if row and row["ts"] else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("MySQLSyncStore.last_synced_at failed: %s", exc)
            return None
        finally:
            conn.close()

    def fetch_chunks_by_url(
        self, department: str, url: str, *, active_only: bool = False
    ) -> list[dict]:
        """Not implemented for OpenSearch mode — chunks live in OpenSearch.

        Returns an empty list so :func:`resolve_document_chunks` falls through
        to re-chunking, which is correct: we never reuse stale chunk dicts from
        a previous local SQLite store.
        """
        return []

    def total_chunks(self) -> int:
        """Total active chunks across all departments (from OpenSearch)."""
        return sum(self.count(d) for d in self.departments_with_data())

    # ── Sync-source writes ────────────────────────────────────────────────────

    def record_source_hashes(
        self,
        department: str,
        sources: list[dict[str, str | None]],
    ) -> None:
        """Persist content hashes for successfully indexed source URLs."""
        if not sources:
            return
        synced_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                for row in sources:
                    url = row.get("url")
                    content_hash = row.get("content_hash")
                    if not url or not content_hash:
                        continue
                    cur.execute(
                        """
                        INSERT INTO sync_sources
                            (department, url, source_id, content_hash, last_modified, synced_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            source_id     = VALUES(source_id),
                            content_hash  = VALUES(content_hash),
                            last_modified = VALUES(last_modified),
                            synced_at     = VALUES(synced_at)
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
        except Exception as exc:  # noqa: BLE001
            logger.warning("MySQLSyncStore.record_source_hashes failed: %s", exc)
        finally:
            conn.close()

    def replace_department_chunks(self, department: str, rows: list[dict]) -> int:
        """No-op for OpenSearch mode — chunks are managed by OpenSearchIndexBuilder."""
        return len(rows)

    def clear_department(self, department: str) -> None:
        """No-op for OpenSearch mode."""

    def upsert_chunks(self, rows: list[dict]) -> None:
        """No-op for OpenSearch mode."""

    def distinct_urls(self, department: str) -> set[str]:
        """Return distinct URLs from the sync_sources table for *department*."""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT url FROM sync_sources WHERE department=%s",
                    (department,),
                )
                return {row["url"] for row in cur.fetchall() if row["url"]}
        except Exception as exc:  # noqa: BLE001
            logger.warning("MySQLSyncStore.distinct_urls failed: %s", exc)
            return set()
        finally:
            conn.close()

    def tombstone_urls(self, department: str, urls: set[str]) -> int:
        """Remove tracked source hashes for *urls* (they will be re-indexed next sync)."""
        if not urls:
            return 0
        placeholders = ",".join(["%s"] * len(urls))
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM sync_sources WHERE department=%s AND url IN ({placeholders})",
                    (department, *sorted(urls)),
                )
                count = cur.rowcount
            conn.commit()
            return int(count)
        except Exception as exc:  # noqa: BLE001
            logger.warning("MySQLSyncStore.tombstone_urls failed: %s", exc)
            return 0
        finally:
            conn.close()
