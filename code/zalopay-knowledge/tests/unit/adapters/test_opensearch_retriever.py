from __future__ import annotations

"""OpenSearchRetriever tests — filter-clause construction, search query shaping,
and full-page fetch. The OpenSearch client is faked; no network or cluster needed."""

from unittest.mock import MagicMock

import pytest

from app.adapters.opensearch_retriever import OpenSearchRetriever, _build_filter_clauses
from app.ports.errors import RetrieverUnavailable


def _make_retriever(client: MagicMock) -> OpenSearchRetriever:
    """Build a retriever without running __init__ (skips Embedder/cluster wiring)."""
    r = OpenSearchRetriever.__new__(OpenSearchRetriever)
    r._client = client
    r._prefix = "zalopay"
    embedder = MagicMock()
    embedder.encode_query.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
    r._embedder = embedder
    return r


def _ready_client(hits: list[dict]) -> MagicMock:
    client = MagicMock()
    client.indices.exists.return_value = True
    client.count.return_value = {"count": len(hits) or 1}
    client.search.return_value = {"hits": {"hits": hits}}
    return client


# ── _build_filter_clauses ──────────────────────────────────────────────────────

class TestBuildFilterClauses:
    def test_none_and_empty_return_no_clauses(self) -> None:
        assert _build_filter_clauses(None) == []
        assert _build_filter_clauses({}) == []
        assert _build_filter_clauses({"labels": []}) == []

    def test_labels_become_and_wildcards(self) -> None:
        clauses = _build_filter_clauses({"labels": ["zalopay-workflow", "status:active"]})
        assert clauses == [
            {"wildcard": {"labels": '*"zalopay-workflow"*'}},
            {"wildcard": {"labels": '*"status:active"*'}},
        ]

    def test_non_label_fields_use_terms(self) -> None:
        clauses = _build_filter_clauses({"lifecycle_state": ["active", "deprecated"]})
        assert clauses == [{"terms": {"lifecycle_state": ["active", "deprecated"]}}]

    def test_mixed_fields_combined(self) -> None:
        clauses = _build_filter_clauses({"labels": ["zalopay-workflow"], "space": ["Workflow"]})
        assert {"wildcard": {"labels": '*"zalopay-workflow"*'}} in clauses
        assert {"terms": {"space": ["Workflow"]}} in clauses


# ── search() query shaping ───────────────────────────────────────────────────────

def test_search_without_filters_uses_bare_knn() -> None:
    client = _ready_client([])
    retriever = _make_retriever(client)

    retriever.search(department="workflow", query="lucky wheel")

    body = client.search.call_args.kwargs["body"]
    assert "knn" in body["query"]  # not wrapped in bool


def test_search_with_filters_wraps_knn_in_bool() -> None:
    client = _ready_client([])
    retriever = _make_retriever(client)

    retriever.search(
        department="workflow",
        query="lucky wheel",
        filters={"labels": ["zalopay-workflow", "status:active"]},
    )

    body = client.search.call_args.kwargs["body"]
    bool_q = body["query"]["bool"]
    assert "knn" in bool_q["must"][0]
    assert {"wildcard": {"labels": '*"zalopay-workflow"*'}} in bool_q["filter"]
    assert {"wildcard": {"labels": '*"status:active"*'}} in bool_q["filter"]


def test_search_excludes_sunset_hits() -> None:
    hits = [
        {"_score": 0.9, "_source": {"chunk_id": "a", "lifecycle_state": "active", "text": "x"}},
        {"_score": 0.8, "_source": {"chunk_id": "b", "lifecycle_state": "sunset", "text": "y"}},
    ]
    retriever = _make_retriever(_ready_client(hits))

    results = retriever.search(department="workflow", query="q", k=5)

    assert [r.chunk_id for r in results] == ["a"]


# ── get_page_chunks() ────────────────────────────────────────────────────────────

def test_get_page_chunks_queries_by_source_sorted_by_seq() -> None:
    hits = [
        {"_source": {"chunk_id": "c0", "source": "P1", "seq": 0, "lifecycle_state": "active", "text": "1"}},
        {"_source": {"chunk_id": "c1", "source": "P1", "seq": 1, "lifecycle_state": "active", "text": "2"}},
    ]
    client = _ready_client(hits)
    retriever = _make_retriever(client)

    results = retriever.get_page_chunks(department="workflow", page_id="P1")

    body = client.search.call_args.kwargs["body"]
    assert body["query"] == {"term": {"source": "P1"}}
    assert body["sort"][0]["seq"]["order"] == "asc"
    assert [r.chunk_id for r in results] == ["c0", "c1"]
    assert all(r.score == 1.0 for r in results)


def test_get_page_chunks_excludes_sunset() -> None:
    hits = [
        {"_source": {"chunk_id": "c0", "source": "P1", "seq": 0, "lifecycle_state": "active", "text": "1"}},
        {"_source": {"chunk_id": "c1", "source": "P1", "seq": 1, "lifecycle_state": "sunset", "text": "2"}},
    ]
    retriever = _make_retriever(_ready_client(hits))

    results = retriever.get_page_chunks(department="workflow", page_id="P1")

    assert [r.chunk_id for r in results] == ["c0"]


def test_get_page_chunks_empty_page_id_returns_empty() -> None:
    retriever = _make_retriever(_ready_client([]))
    assert retriever.get_page_chunks(department="workflow", page_id="") == []


def test_get_page_chunks_raises_when_index_missing() -> None:
    client = MagicMock()
    client.indices.exists.return_value = False
    retriever = _make_retriever(client)

    with pytest.raises(RetrieverUnavailable):
        retriever.get_page_chunks(department="workflow", page_id="P1")
