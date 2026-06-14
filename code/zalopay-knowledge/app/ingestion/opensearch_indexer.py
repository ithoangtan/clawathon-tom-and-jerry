from __future__ import annotations

"""OpenSearchIndexBuilder — IndexBuilder equivalent for VECTOR_STORE=opensearch.

Embeds chunks with the local E5 model and bulk-upserts them into GreenNode
managed vector OpenSearch.  One index per department:
``{prefix}_{department}``  (e.g. ``zalopay_risk``).

Index mapping uses ``knn_vector`` (384-dim, HNSW cosine) so that
OpenSearchRetriever can run knn queries directly.

The SQLite MetaStore is kept **only** for the ``sync_sources`` table used by
:func:`~app.ingestion.sync_hash.resolve_document_chunks` to detect unchanged
pages (content-hash dedup).  The ``chunks`` table is not used.
"""

import logging
from pathlib import Path

from app.adapters.embeddings import Embedder
from app.config import Settings, get_settings
from app.store.meta import MetaStore

logger = logging.getLogger(__name__)

_INDEX_MAPPING = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100,
        }
    },
    "mappings": {
        "properties": {
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
            "text":            {"type": "text"},
            "embedding": {
                "type": "knn_vector",
                "dimension": 384,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "lucene",
                },
            },
        }
    },
}

_BULK_CHUNK_SIZE = 200


class OpenSearchIndexBuilder:
    """Embed and index chunks into GreenNode managed vector OpenSearch."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._cfg = settings or get_settings()
        index_dir = Path(self._cfg.index_dir)
        # MetaStore used only for sync_sources table (content-hash dedup).
        self._meta = MetaStore(index_dir / "meta.db")
        self._embedder = Embedder(
            self._cfg.embedding_model,
            cache_dir=index_dir / "hf-cache",
        )
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
        """Create index with knn_vector mapping if it does not exist."""
        index = self._index_name(department)
        if not self._client.indices.exists(index=index):
            self._client.indices.create(index=index, body=_INDEX_MAPPING)
            logger.info("Created OpenSearch index %s", index)

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
        for chunk, vec in zip(chunks, vectors):
            doc = {k: v for k, v in chunk.items() if k != "vec_pos"}
            doc["embedding"] = vec.tolist()
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
