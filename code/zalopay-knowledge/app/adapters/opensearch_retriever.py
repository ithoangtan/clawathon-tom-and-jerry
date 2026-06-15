from __future__ import annotations

"""OpenSearchRetriever — RetrieverPort implementation backed by GreenNode vector OpenSearch.

Replaces FaissRetriever when VECTOR_STORE=opensearch.  Vectors and metadata are
stored together in one OpenSearch document per chunk, so no separate SQLite meta
lookup is needed at query time.

Search flow for one department branch:

1. encode the query locally with the E5 ``"query: "`` prefix (zero MaaS tokens),
2. knn_vector search against ``{prefix}_{department}`` index for k+buffer results,
3. filter out ``sunset`` chunks in Python,
4. return top-k :class:`RetrievedChunk` sorted by descending score.
"""

import logging

from app.adapters.embeddings import Embedder
from app.config import Settings, get_settings
from app.ports.errors import RetrieverUnavailable
from app.ports.types import RetrievedChunk

logger = logging.getLogger(__name__)

_SUNSET_OVERFETCH = 15


def _build_filter_clauses(filters: dict[str, list[str]] | None) -> list[dict]:
    """Translate a ``RetrieverPort`` filter dict into OpenSearch query clauses.

    See ``RetrieverPort.search`` for the semantics. ``labels`` is stored as a
    single JSON string per chunk (e.g. ``["domain:risk","status:active"]``), so
    each requested label is matched with a wildcard against that encoding and all
    requested labels must be present (AND). Other fields use ``terms`` (OR).
    """
    if not filters:
        return []
    clauses: list[dict] = []
    for field, values in filters.items():
        vals = [v for v in (values or []) if v]
        if not vals:
            continue
        if field == "labels":
            # AND: the chunk must carry every requested label.
            for label in vals:
                clauses.append({"wildcard": {"labels": f'*"{label}"*'}})
        else:
            clauses.append({"terms": {field: vals}})
    return clauses


class OpenSearchRetriever:
    """Department-partitioned retriever backed by GreenNode managed vector OpenSearch."""

    def __init__(self, settings: Settings | None = None) -> None:
        from pathlib import Path

        from app.adapters.openai_credentials import resolve_openai_api_key

        self._cfg = settings or get_settings()
        self._embedder = Embedder(
            self._cfg.embedding_model,
            api_key=resolve_openai_api_key(self._cfg),
        )
        self._client = self._build_client()
        self._prefix = self._cfg.opensearch_index_prefix

    def _build_client(self):
        from opensearchpy import OpenSearch

        return OpenSearch(
            hosts=[{"host": self._cfg.opensearch_host, "port": self._cfg.opensearch_port}],
            http_auth=(self._cfg.opensearch_user, self._cfg.opensearch_password),
            use_ssl=self._cfg.opensearch_use_ssl,
            verify_certs=self._cfg.opensearch_verify_certs,
            ssl_show_warn=False,
        )

    def _index_name(self, department: str) -> str:
        return f"{self._prefix}_{department}"

    # ── RetrieverPort ─────────────────────────────────────────────────────────

    def search(
        self,
        *,
        department: str,
        query: str,
        k: int = 8,
        language: str = "en",
        filters: dict[str, list[str]] | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve the top-k non-sunset chunks for *query* from *department*."""
        if not query.strip():
            return []

        index = self._index_name(department)
        if not self._index_has_docs(index):
            raise RetrieverUnavailable(department)

        fetch = k + _SUNSET_OVERFETCH
        qvec = self._embedder.encode_query(query).tolist()

        knn = {"knn": {"embedding": {"vector": qvec, "k": fetch}}}
        filter_clauses = _build_filter_clauses(filters)
        if filter_clauses:
            query_block = {"bool": {"must": [knn], "filter": filter_clauses}}
        else:
            query_block = knn

        body = {
            "size": fetch,
            "query": query_block,
            "_source": {"excludes": ["embedding"]},
        }

        try:
            resp = self._client.search(index=index, body=body)
        except Exception as exc:
            logger.error("OpenSearch search failed for %s: %s", department, exc)
            raise RetrieverUnavailable(department) from exc

        hits = resp.get("hits", {}).get("hits", [])
        results: list[RetrievedChunk] = []
        for hit in hits:
            src = hit.get("_source", {})
            if src.get("lifecycle_state") == "sunset":
                continue
            score = float(hit.get("_score") or 0.0)
            results.append(self._to_chunk(src, department, score))
            if len(results) >= k:
                break

        logger.info(
            "OpenSearch search[%s]: %d/%d returned (lang=%s)",
            department,
            len(results),
            len(hits),
            language,
        )
        return results

    def get_page_chunks(
        self,
        *,
        department: str,
        page_id: str,
    ) -> list[RetrievedChunk]:
        """Return all non-sunset chunks of one page (source==page_id), in page order."""
        if not page_id:
            return []

        index = self._index_name(department)
        if not self._index_has_docs(index):
            raise RetrieverUnavailable(department)

        body = {
            "size": 1000,
            "query": {"term": {"source": page_id}},
            # ``seq`` is stamped by the indexer in document order; "unmapped_type"
            # keeps this resilient for indices built before the field existed.
            "sort": [{"seq": {"order": "asc", "unmapped_type": "integer"}}],
            "_source": {"excludes": ["embedding"]},
        }

        try:
            resp = self._client.search(index=index, body=body)
        except Exception as exc:
            logger.error("OpenSearch get_page_chunks failed for %s/%s: %s", department, page_id, exc)
            raise RetrieverUnavailable(department) from exc

        hits = resp.get("hits", {}).get("hits", [])
        results: list[RetrievedChunk] = []
        for hit in hits:
            src = hit.get("_source", {})
            if src.get("lifecycle_state") == "sunset":
                continue
            results.append(self._to_chunk(src, department, 1.0))

        logger.info("OpenSearch get_page_chunks[%s/%s]: %d chunks", department, page_id, len(results))
        return results

    def is_ready(self) -> bool:
        """True when ≥1 department index exists with documents."""
        try:
            from app.common.departments import iter_keys

            for dept in iter_keys():
                if self._index_has_docs(self._index_name(dept)):
                    return True
            return False
        except Exception:  # noqa: BLE001
            return False

    def reload(self) -> None:
        """No-op — OpenSearch is always live; no in-memory partitions to reload."""

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _index_has_docs(self, index: str) -> bool:
        try:
            if not self._client.indices.exists(index=index):
                return False
            count = self._client.count(index=index).get("count", 0)
            return count > 0
        except Exception:  # noqa: BLE001
            return False

    @staticmethod
    def _to_chunk(src: dict, department: str, raw_score: float) -> RetrievedChunk:
        """Build a RetrievedChunk from an OpenSearch hit source dict."""
        page = src.get("page")
        return RetrievedChunk(
            chunk_id=src.get("chunk_id") or src.get("_id") or "",
            department=src.get("department") or department,
            doc_type=src.get("doc_type") or "",
            title=src.get("title") or "",
            url=src.get("url") or "",
            section=src.get("section"),
            source=src.get("source"),
            anchor=src.get("anchor"),
            space=src.get("space"),
            labels=src.get("labels"),
            author=src.get("author"),
            acl=src.get("acl"),
            last_modified=src.get("last_modified"),
            lifecycle_state=src.get("lifecycle_state") or "active",
            source_type=src.get("source_type") or "confluence",
            page=int(page) if page is not None else None,
            text=src.get("text") or "",
            score=max(0.0, min(1.0, raw_score)),
        )
