"""Grade node tests — threshold gate and refusal downstream paths."""

from __future__ import annotations

from app.config import Settings
from app.graph.nodes.grade import make_grade_node
from app.graph.nodes.synthesize import CANNOT_ANSWER, make_synthesize_node
from app.graph.state import Chunk
from app.ports.errors import LLMUnavailable

from tests.unit.graph.conftest import StubLLM


def _grade_and_synthesize(
    chunks: list[Chunk],
    *,
    settings: Settings,
    llm_text: str | None = None,
    llm_error: Exception | None = None,
    deadline_ts: float | None = None,
) -> dict:
    grade_llm = StubLLM(
        llm_text or '{"scores": [{"id": 0, "score": 0.9}, {"id": 1, "score": 0.2}]}',
        side_effect=llm_error,
    )
    grade_node = make_grade_node(grade_llm, settings=settings)
    state = {"department": "risk", "question": "q", "chunks": chunks}
    if deadline_ts is not None:
        state["deadline_ts"] = deadline_ts
    graded = grade_node(state)

    synth_node = make_synthesize_node(StubLLM("ignored"), settings=settings)
    synth_state = {
        "department": "risk",
        "question": "q",
        "role": "engineer",
        "request_language": "en",
        "graded_chunks": graded["graded_chunks"],
    }
    if deadline_ts is not None:
        synth_state["deadline_ts"] = deadline_ts
    synth = synth_node(synth_state)
    return {**graded, **synth}


def test_grade_filters_below_threshold(test_settings: Settings, sample_chunk: Chunk):
    low = dict(sample_chunk)
    low["chunk_id"] = "b"
    low["text"] = "low relevance"
    out = _grade_and_synthesize([sample_chunk, low], settings=test_settings)
    assert len(out["graded_chunks"]) == 1
    assert out["graded_chunks"][0]["chunk_id"] == sample_chunk["chunk_id"]
    assert out["draft_answer"] != CANNOT_ANSWER


def test_grade_empty_chunks_short_circuits(test_settings: Settings):
    node = make_grade_node(StubLLM(), settings=test_settings)
    out = node({"department": "risk", "question": "q", "chunks": []})
    assert out["graded_chunks"] == []
    assert out["evidence"] == {"risk": []}


def test_grade_refuse_path_when_all_below_threshold(test_settings: Settings, sample_chunk: Chunk):
    llm = StubLLM('{"scores": [{"id": 0, "score": 0.1}]}')
    node = make_grade_node(llm, settings=test_settings)
    out = node({"department": "risk", "question": "q", "chunks": [sample_chunk]})
    assert out["graded_chunks"] == []

    synth = make_synthesize_node(StubLLM(), settings=test_settings)
    synth_out = synth(
        {
            "department": "risk",
            "question": "q",
            "graded_chunks": out["graded_chunks"],
            "request_language": "en",
        }
    )
    assert synth_out["draft_answer"] == CANNOT_ANSWER
    assert synth_out["draft_citations"] == []


def test_grade_fallback_to_retriever_scores_on_llm_failure(
    test_settings: Settings, sample_chunk: Chunk
):
    high = dict(sample_chunk)
    high["score"] = 0.9
    low = dict(sample_chunk)
    low["chunk_id"] = "low"
    low["score"] = 0.3

    node = make_grade_node(StubLLM(side_effect=LLMUnavailable()), settings=test_settings)
    out = node({"department": "risk", "question": "q", "chunks": [high, low]})
    assert len(out["graded_chunks"]) == 1
    assert out["graded_chunks"][0]["chunk_id"] == high["chunk_id"]


def test_grade_budget_exceeded_uses_retriever_scores(
    test_settings: Settings, sample_chunk: Chunk, past_deadline: float
):
    low = dict(sample_chunk)
    low["chunk_id"] = "low"
    low["score"] = 0.3
    high = dict(sample_chunk)
    high["score"] = 0.9

    node = make_grade_node(StubLLM(), settings=test_settings)
    out = node(
        {
            "department": "risk",
            "question": "q",
            "chunks": [high, low],
            "deadline_ts": past_deadline,
        }
    )
    assert len(out["graded_chunks"]) == 1
    assert out["graded_chunks"][0]["chunk_id"] == high["chunk_id"]


def test_grade_keeps_chunk_at_exact_threshold(test_settings: Settings, sample_chunk: Chunk):
    llm = StubLLM('{"scores": [{"id": 0, "score": 0.5}]}')
    node = make_grade_node(llm, settings=test_settings)
    out = node({"department": "risk", "question": "q", "chunks": [sample_chunk]})
    assert len(out["graded_chunks"]) == 1
    assert out["graded_chunks"][0]["score"] == 0.5


def test_grade_drops_chunk_just_below_threshold(test_settings: Settings, sample_chunk: Chunk):
    llm = StubLLM('{"scores": [{"id": 0, "score": 0.49}]}')
    node = make_grade_node(llm, settings=test_settings)
    out = node({"department": "risk", "question": "q", "chunks": [sample_chunk]})
    assert out["graded_chunks"] == []
