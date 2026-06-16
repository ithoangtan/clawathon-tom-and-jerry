from __future__ import annotations

"""OpenSearchIndexBuilder — IndexBuilder equivalent for VECTOR_STORE=opensearch.

Embeds chunks with the local E5 model and bulk-upserts them into GreenNode
managed vector OpenSearch.  One index per department:
``{prefix}_{department}``  (e.g. ``zalopay_risk``).

Index mapping uses ``knn_vector`` (HNSW cosine) so that
OpenSearchRetriever can run knn queries directly.  The vector dimension is
read from the actual embedding model at runtime so any model works.

The SQLite MetaStore is kept **only** for the ``sync_sources`` table used by
:func:`~app.ingestion.sync_hash.resolve_document_chunks` to detect unchanged
pages (content-hash dedup).  The ``chunks`` table is not used.
"""

import logging
from pathlib import Path
from typing import Union

from app.adapters.embeddings import Embedder, make_embedder
from app.config import Settings, get_settings
from app.store.meta import MetaStore

logger = logging.getLogger(__name__)

_BASE_MAPPINGS_PROPERTIES = {
    "chunk_id":        {"type": "keyword"},
    "department":      {"type": "keyword"},
    "doc_type":        {"type": "keyword"},
    "title":           {"type": "text"},
    "url":             {"type": "keyword"},
    "section":         {"type": "text"},
    "anchor":          {"type": "keyword"},
    "source":          {"type": "keyword"},
    "space":           {"type": "keyword"},
    "labels":          {"type": "keyword"},
    "last_modified":   {"type": "keyword"},
    "author":          {"type": "keyword"},
    "acl":             {"type": "keyword"},
    "lifecycle_state": {"type": "keyword"},
    "source_type":     {"type": "keyword"},
    "page":            {"type": "integer"},
    "seq":             {"type": "integer"},
    "text":            {"type": "text"},
}


def _build_index_mapping(dimension: int) -> dict:
    props = dict(_BASE_MAPPINGS_PROPERTIES)
    props["embedding"] = {
        "type": "knn_vector",
        "dimension": dimension,
        "method": {
            "name": "hnsw",
            "space_type": "cosinesimil",
            "engine": "lucene",
        },
    }
    return {
        "settings": {"index": {"knn": True, "knn.algo_param.ef_search": 100}},
        "mappings": {"properties": props},
    }

_BULK_CHUNK_SIZE = 200


class OpenSearchIndexBuilder:
    """Embed and index chunks into GreenNode managed vector OpenSearch."""

    def __init__(
        self,
        settings: Settings | None = None,
        meta_store=None,
    ) -> None:
        self._cfg = settings or get_settings()
        if meta_store is not None:
            # Injected store (MySQLSyncStore when online mode is active).
            self._meta = meta_store
        elif self._cfg.db_host and self._cfg.db_user:
            # Online MySQL available — use it so sync state persists across restarts.
            from app.store.mysql_sync_store import MySQLSyncStore
            self._meta = MySQLSyncStore(self._cfg)
        else:
            # Fallback: local SQLite (only used when MySQL not configured).
            index_dir = Path(self._cfg.index_dir)
            self._meta = MetaStore(index_dir / "meta.db")
        self._embedder = make_embedder(self._cfg)
        self._prefix = self._cfg.opensearch_index_prefix
        self._client = self._build_client()

    def _build_client(self):
        from opensearchpy import OpenSearch

        return OpenSearch(
            hosts=[{
                "host": self._cfg.opensearch_host,
                "port": self._cfg.opensearch_port,
            }],
            http_auth=(self._cfg.opensearch_user, self._cfg.opensearch_password),
            use_ssl=self._cfg.opensearch_use_ssl,
            verify_certs=self._cfg.opensearch_verify_certs,
            ssl_show_warn=False,
        )

    def _index_name(self, department: str) -> str:
        return f"{self._prefix}_{department}"

    def _ensure_index(self, department: str) -> None:
        """Create index with knn_vector mapping if it does not exist.

        Recreates the index when the stored dimension doesn't match the current
        embedding model — avoids silent bulk-insert failures on dimension mismatch.
        """
        index = self._index_name(department)
        dim = self._embedder.dimension
        mapping = _build_index_mapping(dim)

        if self._client.indices.exists(index=index):
            # Check if the existing index has the correct dimension.
            try:
                info = self._client.indices.get_mapping(index=index)
                stored_dim = (
                    info.get(index, {})
                    .get("mappings", {})
                    .get("properties", {})
                    .get("embedding", {})
                    .get("dimension")
                )
                if stored_dim is not None and int(stored_dim) != dim:
                    logger.warning(
                        "Index %s has dimension %d but embedder produces %d — recreating",
                        index, stored_dim, dim,
                    )
                    self._client.indices.delete(index=index)
                    self._client.indices.create(index=index, body=mapping)
                    logger.info("Recreated OpenSearch index %s (dim=%d)", index, dim)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not check index mapping for %s: %s", index, exc)
            return

        self._client.indices.create(index=index, body=mapping)
        logger.info("Created OpenSearch index %s (dim=%d)", index, dim)

    # ── Public interface (mirrors IndexBuilder) ───────────────────────────────

    def rebuild_department(self, department: str, chunks: list[dict]) -> int:
        """Embed *chunks* and replace the department's OpenSearch index.

        Full rebuild: deletes all existing docs for *department*, then bulk-upserts
        the new set.  Returns the number of chunks indexed.
        """
        index = self._index_name(department)

        if not chunks:
            if self._client.indices.exists(index=index):
                self._client.delete_by_query(
                    index=index,
                    body={"query": {"term": {"department": department}}},
                    refresh=True,
                )
            logger.info("No chunks for %s — cleared index", department)
            return 0

        self._ensure_index(department)

        texts = [c["text"] for c in chunks]
        vectors = self._embedder.encode_passages(texts)

        # Hard-delete current docs before re-indexing (atomic at department level).
        self._client.delete_by_query(
            index=index,
            body={"query": {"term": {"department": department}}},
            refresh=True,
        )

        actions = []
        for seq, (chunk, vec) in enumerate(zip(chunks, vectors)):
            doc = {k: v for k, v in chunk.items() if k != "vec_pos"}
            doc["embedding"] = vec.tolist()
            # Per-department insertion order. A document's chunks are appended
            # consecutively, so sorting by ``seq`` reconstructs page order in
            # get_page_chunks() (OpenSearch otherwise has no ordering key).
            doc["seq"] = seq
            actions.append({
                "_index": index,
                "_id": chunk["chunk_id"],
                "_source": doc,
            })

        self._bulk_index(actions)
        # Refresh so searches see the new docs immediately.
        self._client.indices.refresh(index=index)
        logger.info("Indexed %d chunks for %s", len(chunks), department)
        return len(chunks)

    def tombstone_removed_urls(
        self, department: str, active_urls: set[str]
    ) -> set[str]:
        """Mark chunks whose URL is absent from *active_urls* as sunset.

        Returns the set of URLs that were tombstoned.
        """
        index = self._index_name(department)
        if not self._client.indices.exists(index=index):
            return set()

        # Collect all distinct URLs currently indexed for this department.
        indexed_urls = self._distinct_urls(department)
        removed = indexed_urls - active_urls
        if not removed:
            return set()

        self._client.update_by_query(
            index=index,
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"department": department}},
                            {"terms": {"url": list(removed)}},
                        ]
                    }
                },
                "script": {
                    "source": "ctx._source.lifecycle_state = 'sunset'",
                    "lang": "painless",
                },
            },
            refresh=True,
        )
        logger.info(
            "Tombstoned %d URL(s) in %s: %s",
            len(removed),
            department,
            list(removed)[:5],
        )
        return removed

    def reload_retriever(self) -> None:
        """Ask the process-wide retriever to reload (best-effort)."""
        try:
            from app.adapters.deps import get_deps

            retriever = get_deps().retriever
            if hasattr(retriever, "reload"):
                retriever.reload()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not reload retriever: %s", exc)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _bulk_index(self, actions: list[dict]) -> None:
        from opensearchpy import helpers

        for i in range(0, len(actions), _BULK_CHUNK_SIZE):
            batch = actions[i : i + _BULK_CHUNK_SIZE]
            ok, errors = helpers.bulk(self._client, batch, raise_on_error=False)
            if errors:
                logger.warning("Bulk index errors (%d/%d): %s", len(errors), len(batch), errors[:3])

    def _distinct_urls(self, department: str) -> set[str]:
        """Return the set of distinct URLs currently indexed for *department*."""
        index = self._index_name(department)
        urls: set[str] = set()
        body = {
            "size": 0,
            "query": {"term": {"department": department}},
            "aggs": {
                "urls": {
                    "terms": {
                        "field": "url",
                        "size": 10_000,
                    }
                }
            },
        }
        try:
            resp = self._client.search(index=index, body=body)
            for bucket in resp.get("aggregations", {}).get("urls", {}).get("buckets", []):
                if bucket.get("key"):
                    urls.add(bucket["key"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not fetch distinct URLs for %s: %s", department, exc)
        return urls
