"""Retrieve node tests — top-k retrieval with mock retriever."""

from __future__ import annotations

from app.config import Settings
from app.graph.nodes.retrieve import make_retrieve_node
from app.ports.errors import RetrieverUnavailable
from app.ports.types import RetrievedChunk

from tests.unit.graph.conftest import StubRetriever
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def test_retrieve_requests_candidate_pool_when_pipeline_enabled(
    test_settings: Settings, sample_retrieved_chunk: RetrievedChunk
):
    """Hybrid/rerank pipeline fetches retrieve_pool candidates before trimming."""
    settings = Settings(
        grade_threshold=test_settings.grade_threshold,
        route_confidence_min=test_settings.route_confidence_min,
        topk=2,
        retrieve_pool=10,
        hybrid_search_enabled=True,
        reranker_enabled=False,
    )
    chunks = [
        RetrievedChunk(
            **{
                **sample_retrieved_chunk.__dict__,
                "chunk_id": f"c{i}",
                "url": f"https://example.com/doc-{i}",
                "score": 1.0 - i * 0.05,
            }
        )
        for i in range(6)
    ]
    retriever = StubRetriever(chunks=chunks)
    node = make_retrieve_node(retriever, settings=settings)
    out = node(
        {
            "department": RISK,
            "question": "escalation policy",
            "request_language": "en",
        }
    )
    assert retriever.search_calls[0]["k"] == 10
    assert len(out["chunks"]) == 2


def test_retrieve_returns_top_k_chunks(
    test_settings: Settings, sample_retrieved_chunk: RetrievedChunk
):
    chunks = [
        RetrievedChunk(
            **{**sample_retrieved_chunk.__dict__, "chunk_id": f"c{i}", "score": 1.0 - i * 0.1}
        )
        for i in range(5)
    ]
    retriever = StubRetriever(chunks=chunks)
    node = make_retrieve_node(retriever, settings=test_settings)
    out = node(
        {
            "department": RISK,
            "question": "escalation policy",
            "request_language": "en",
        }
    )
    assert len(out["chunks"]) == 5
    assert retriever.search_calls[0]["k"] == test_settings.topk
    assert retriever.search_calls[0]["department"] == RISK
    assert retriever.search_calls[0]["query"] == "escalation policy"


def test_retrieve_maps_retrieved_chunk_fields(
    test_settings: Settings, sample_retrieved_chunk: RetrievedChunk
):
    retriever = StubRetriever(chunks=[sample_retrieved_chunk])
    node = make_retrieve_node(retriever, settings=test_settings)
    out = node(
        {
            "department": RISK,
            "question": "q",
            "request_language": "en",
        }
    )
    chunk = out["chunks"][0]
    assert chunk["chunk_id"] == sample_retrieved_chunk.chunk_id
    assert chunk["title"] == sample_retrieved_chunk.title
    assert chunk["text"] == sample_retrieved_chunk.text
    assert chunk["score"] == sample_retrieved_chunk.score
    assert chunk["department"] == RISK


def test_retrieve_empty_on_retriever_unavailable(test_settings: Settings):
    retriever = StubRetriever(search_raises=RetrieverUnavailable("risk"))
    node = make_retrieve_node(retriever, settings=test_settings)
    out = node(
        {
            "department": RISK,
            "question": "q",
            "request_language": "en",
        }
    )
    assert out["chunks"] == []


def test_retrieve_prefers_retrieval_query_over_question(
    test_settings: Settings, sample_retrieved_chunk: RetrievedChunk
):
    """FR-1.3: follow-up retrieval uses expanded query from ingest_context."""
    retriever = StubRetriever(chunks=[sample_retrieved_chunk])
    node = make_retrieve_node(retriever, settings=test_settings)
    follow_up_query = (
        "Follow-up question: And what's the SLA for that?\n"
        "Prior context:\nUser: Settlement reconciliation?\nAssistant: Runs nightly."
    )
    node(
        {
            "department": RISK,
            "question": "And what's the SLA for that?",
            "retrieval_query": follow_up_query,
            "request_language": "en",
        }
    )
    assert retriever.search_calls[0]["query"] == follow_up_query


def test_retrieve_empty_on_budget_exceeded(test_settings: Settings, past_deadline: float):
    retriever = StubRetriever(
        chunks=[
            RetrievedChunk(
                chunk_id="c1",
                department=RISK,
                doc_type="policy",
                title="T",
                url="u",
                section=None,
                last_modified=None,
                lifecycle_state="active",
                source_type="confluence",
                page=None,
                text="body",
                score=0.9,
            )
        ]
    )
    node = make_retrieve_node(retriever, settings=test_settings)
    out = node(
        {
            "department": RISK,
            "question": "q",
            "request_language": "en",
            "deadline_ts": past_deadline,
        }
    )
    assert out["chunks"] == []
    assert retriever.search_calls == []
