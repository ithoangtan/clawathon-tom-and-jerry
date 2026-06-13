"""Verify node tests — refusal on unsupported claims."""

from __future__ import annotations

from app.config import Settings
from app.graph.nodes.synthesize import CANNOT_ANSWER
from app.graph.nodes.verify import make_verify_node
from app.graph.state import Chunk, Citation

from tests.unit.graph.conftest import StubLLM


def _verify(
    *,
    settings: Settings,
    answer: str,
    graded: list[Chunk],
    citations: list[Citation],
    verdicts_json: str,
    future_deadline: float,
) -> dict:
    node = make_verify_node(StubLLM(verdicts_json), settings=settings)
    return node(
        {
            "department": "risk",
            "draft_answer": answer,
            "draft_citations": citations,
            "graded_chunks": graded,
            "request_language": "en",
            "deadline_ts": future_deadline,
        }
    )


def test_verify_refuses_on_cannot_answer_sentinel(
    test_settings: Settings, sample_chunk, future_deadline: float
):
    out = _verify(
        settings=test_settings,
        answer=CANNOT_ANSWER,
        graded=[sample_chunk],
        citations=[],
        verdicts_json="{}",
        future_deadline=future_deadline,
    )
    result = out["dept_results"][0]
    assert result["status"] == "refused"
    assert result["answer"] == ""
    assert "no_supporting_sources" in result["warnings"]


def test_verify_refuses_without_graded_chunks(test_settings: Settings, future_deadline: float):
    out = _verify(
        settings=test_settings,
        answer="Some answer [1].",
        graded=[],
        citations=[],
        verdicts_json='{"verdicts": [{"id": 0, "supported": true}]}',
        future_deadline=future_deadline,
    )
    assert out["dept_results"][0]["status"] == "refused"


def test_verify_refuses_when_no_citation_markers(
    test_settings: Settings, sample_chunk, sample_citation, future_deadline: float
):
    out = _verify(
        settings=test_settings,
        answer="Ungrounded answer with no markers.",
        graded=[sample_chunk],
        citations=[sample_citation],
        verdicts_json="{}",
        future_deadline=future_deadline,
    )
    assert out["dept_results"][0]["status"] == "refused"


def test_verify_refuses_when_zero_claims_supported(
    test_settings: Settings, sample_chunk, sample_citation, future_deadline: float
):
    out = _verify(
        settings=test_settings,
        answer="Escalation needs approval [1].",
        graded=[sample_chunk],
        citations=[sample_citation],
        verdicts_json='{"verdicts": [{"id": 0, "supported": false}]}',
        future_deadline=future_deadline,
    )
    result = out["dept_results"][0]
    assert result["status"] == "refused"
    assert result["confidence"] == 0.0


def test_verify_answers_when_all_claims_supported(
    test_settings: Settings, sample_chunk, sample_citation, future_deadline: float
):
    out = _verify(
        settings=test_settings,
        answer="Escalation needs approval [1].",
        graded=[sample_chunk],
        citations=[sample_citation],
        verdicts_json='{"verdicts": [{"id": 0, "supported": true}]}',
        future_deadline=future_deadline,
    )
    result = out["dept_results"][0]
    assert result["status"] == "answered"
    assert result["answer"] == "Escalation needs approval [1]."
    assert result["citations"] == [sample_citation]
    assert result["confidence"] > 0


def test_verify_partial_support_adds_warning(
    test_settings: Settings, sample_chunk, sample_citation, future_deadline: float
):
    second = dict(sample_chunk)
    second["chunk_id"] = "c2"
    second["text"] = "Secondary policy detail."
    out = _verify(
        settings=test_settings,
        answer="First claim [1]. Second claim [2].",
        graded=[sample_chunk, second],
        citations=[sample_citation, sample_citation],
        verdicts_json=(
            '{"verdicts": [{"id": 0, "supported": true}, {"id": 1, "supported": false}]}'
        ),
        future_deadline=future_deadline,
    )
    result = out["dept_results"][0]
    assert result["status"] == "answered"
    assert any("unverified_claims" in w for w in result["warnings"])


def test_verify_deprecation_warning_for_deprecated_chunk(
    test_settings: Settings, sample_citation, future_deadline: float
):
    deprecated = Chunk(
        chunk_id="d1",
        department="risk",
        doc_type="policy",
        title="Old Policy",
        url="https://example.com/old",
        lifecycle_state="deprecated",
        source_type="confluence",
        text="Deprecated guidance.",
        score=0.8,
    )
    out = _verify(
        settings=test_settings,
        answer="Follow the old rule [1].",
        graded=[deprecated],
        citations=[sample_citation],
        verdicts_json='{"verdicts": [{"id": 0, "supported": true}]}',
        future_deadline=future_deadline,
    )
    assert "cites_deprecated_source" in out["dept_results"][0]["warnings"]


def test_verify_citation_list_matches_graded_chunks(
    test_settings: Settings, sample_chunk, sample_citation, future_deadline: float
):
    """Synthesize→verify path should preserve FR-2.3 citation fields."""
    from app.graph.nodes.synthesize import make_synthesize_node

    synth = make_synthesize_node(
        StubLLM("Escalation needs approval [1]."),
        settings=test_settings,
    )
    synth_out = synth(
        {
            "department": "risk",
            "question": "How do we escalate?",
            "role": "engineer",
            "request_language": "en",
            "graded_chunks": [sample_chunk],
            "deadline_ts": future_deadline,
        }
    )

    out = _verify(
        settings=test_settings,
        answer=synth_out["draft_answer"],
        graded=[sample_chunk],
        citations=synth_out["draft_citations"],
        verdicts_json='{"verdicts": [{"id": 0, "supported": true}]}',
        future_deadline=future_deadline,
    )
    result = out["dept_results"][0]
    cite = result["citations"][0]

    assert result["status"] == "answered"
    assert cite["title"] == sample_citation["title"]
    assert cite["url"] == sample_citation["url"]
    assert cite["section"] == sample_citation["section"]
    assert cite["last_modified"] == sample_citation["last_modified"]
