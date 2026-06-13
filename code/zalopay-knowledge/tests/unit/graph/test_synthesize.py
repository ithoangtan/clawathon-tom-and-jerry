"""Synthesize node tests — CANNOT_ANSWER sentinel and citation shape."""

from __future__ import annotations

from app.config import Settings
from app.graph.nodes.synthesize import CANNOT_ANSWER, make_synthesize_node
from app.ports.errors import LLMUnavailable

from tests.unit.graph.conftest import StubLLM
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def test_synthesize_cannot_answer_without_graded_chunks(test_settings: Settings):
    node = make_synthesize_node(StubLLM(), settings=test_settings)
    out = node(
        {
            "department": RISK,
            "question": "q",
            "graded_chunks": [],
            "request_language": "en",
        }
    )
    assert out["draft_answer"] == CANNOT_ANSWER
    assert out["draft_citations"] == []


def test_synthesize_cannot_answer_on_budget_exceeded(
    test_settings: Settings, sample_chunk, past_deadline: float
):
    node = make_synthesize_node(StubLLM("should not be called"), settings=test_settings)
    out = node(
        {
            "department": RISK,
            "question": "q",
            "graded_chunks": [sample_chunk],
            "request_language": "en",
            "deadline_ts": past_deadline,
        }
    )
    assert out["draft_answer"] == CANNOT_ANSWER
    assert out["draft_citations"] == []


def test_synthesize_cannot_answer_on_llm_unavailable(
    test_settings: Settings, sample_chunk
):
    node = make_synthesize_node(
        StubLLM(side_effect=LLMUnavailable()),
        settings=test_settings,
    )
    out = node(
        {
            "department": RISK,
            "question": "q",
            "graded_chunks": [sample_chunk],
            "role": "engineer",
            "request_language": "en",
        }
    )
    assert out["draft_answer"] == CANNOT_ANSWER


def test_synthesize_citation_output_shape(test_settings: Settings, sample_chunk):
    answer_text = "Escalation requires manager approval within 24 hours [1]."
    node = make_synthesize_node(StubLLM(answer_text), settings=test_settings)
    out = node(
        {
            "department": RISK,
            "question": "How do I escalate?",
            "graded_chunks": [sample_chunk],
            "role": "engineer",
            "request_language": "en",
        }
    )
    assert out["draft_answer"] == answer_text
    assert len(out["draft_citations"]) == 1
    cite = out["draft_citations"][0]
    assert cite["title"] == sample_chunk["title"]
    assert cite["url"] == sample_chunk["url"]
    assert cite["section"] == sample_chunk["section"]
    assert cite["lifecycle_state"] == "active"
    assert cite["deprecated"] is False
    assert cite["source_type"] == sample_chunk["source_type"]


def test_synthesize_empty_llm_response_becomes_cannot_answer(
    test_settings: Settings, sample_chunk
):
    node = make_synthesize_node(StubLLM("   "), settings=test_settings)
    out = node(
        {
            "department": RISK,
            "question": "q",
            "graded_chunks": [sample_chunk],
            "request_language": "en",
        }
    )
    assert out["draft_answer"] == CANNOT_ANSWER


def test_synthesize_role_style_reaches_prompt(
    test_settings: Settings, sample_chunk
):
    """AC-4: engineer vs risk roles produce distinct synthesis framing."""
    llm_engineer = StubLLM("Answer [1].")
    llm_risk = StubLLM("Answer [1].")
    base_state = {
        "department": RISK,
        "question": "What is the escalation threshold?",
        "graded_chunks": [sample_chunk],
        "request_language": "en",
    }

    make_synthesize_node(llm_engineer, settings=test_settings)(
        {**base_state, "role": "engineer"}
    )
    make_synthesize_node(llm_risk, settings=test_settings)(
        {**base_state, "role": "risk"}
    )

    engineer_system = llm_engineer.calls[0]["messages"][0]["content"]
    risk_system = llm_risk.calls[0]["messages"][0]["content"]

    assert "Technical and precise" in engineer_system
    assert "Compliance-focused" in risk_system
    assert engineer_system != risk_system


def test_synthesize_includes_conversation_history_in_prompt(
    test_settings: Settings, sample_chunk
):
    """FR-1.3: STM context reaches the synthesis prompt."""
    llm = StubLLM("Answer with context [1].")
    node = make_synthesize_node(llm, settings=test_settings)
    node(
        {
            "department": RISK,
            "question": "And the SLA?",
            "graded_chunks": [sample_chunk],
            "role": "engineer",
            "request_language": "en",
            "conversation_history": "User: What is escalation?\nAssistant: Level 1 first.",
            "recalled_preferences": "prefers bullet points",
        }
    )
    rendered = llm.calls[0]["messages"][0]["content"]
    assert "What is escalation?" in rendered
    assert "prefers bullet points" in rendered


def test_synthesize_emits_citation_per_graded_chunk(
    test_settings: Settings, sample_chunk
):
    """FR-2.3: one citation object per graded chunk (marker alignment)."""
    second = dict(sample_chunk)
    second["chunk_id"] = "c2"
    second["title"] = "SLA Policy"
    second["url"] = "https://example.com/sla"
    llm = StubLLM("First point [1]. Second point [2].")
    node = make_synthesize_node(llm, settings=test_settings)
    out = node(
        {
            "department": RISK,
            "question": "q",
            "graded_chunks": [sample_chunk, second],
            "role": "engineer",
            "request_language": "en",
        }
    )
    assert len(out["draft_citations"]) == 2
    assert out["draft_citations"][0]["title"] == sample_chunk["title"]
    assert out["draft_citations"][1]["title"] == "SLA Policy"
