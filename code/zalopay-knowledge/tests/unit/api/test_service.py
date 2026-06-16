from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.api.context import UserContext
from app.api.schemas import ChatRequest, ChatResponse, CitationModel
from app.api.service import record_chat_outcome, state_to_response, stream_chat
from app.graph.state import Citation, Conflict, ConflictSide
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def test_state_to_response_maps_conflicts() -> None:
    state = {
        "answer": "Conflicting info [1][2]",
        "status": "partial",
        "confidence": 0.6,
        "feedback_id": "fb-123",
        "source_departments": [RISK, BANK],
        "citations": [
            CitationModel(title="Risk Policy", url="https://example.com/risk"),
            CitationModel(title="Bank Policy", url="https://example.com/bank"),
        ],
        "conflicts": [
            {
                "topic": "transaction limit",
                "sides": [
                    {
                        "department": RISK,
                        "statement": "Limit is 10M VND",
                        "citation": {"title": "Risk Policy", "url": "https://example.com/risk"},
                    },
                    {
                        "department": BANK,
                        "statement": "Limit is 5M VND",
                        "citation": {"title": "Bank Policy", "url": "https://example.com/bank"},
                    },
                ],
            }
        ],
        "request_language": "en",
    }

    response = state_to_response(state)

    assert response.status == "partial"
    assert response.conflicts is not None
    assert len(response.conflicts) == 1
    conflict = response.conflicts[0]
    assert conflict.topic == "transaction limit"
    assert len(conflict.sides) == 2
    assert conflict.sides[0].department == RISK
    assert conflict.sides[0].citation.url == "https://example.com/risk"


def test_state_to_response_preserves_citation_doc_type() -> None:
    response = state_to_response(
        {
            "answer": "Policy detail [1].",
            "status": "answered",
            "confidence": 0.9,
            "feedback_id": "fb-doc-type",
            "source_departments": [RISK],
            "citations": [
                {
                    "title": "Risk Policy",
                    "url": "https://example.com/risk",
                    "doc_type": "Risk",
                    "last_modified": "2024-06-01T00:00:00Z",
                }
            ],
            "request_language": "en",
        }
    )
    assert response.citations[0].doc_type == "Risk"


def test_state_to_response_maps_out_of_scope_refusal_reason() -> None:
    response = state_to_response(
        {
            "status": "refused",
            "answer": "This question is outside indexed documentation.",
            "intent": "status_or_data",
            "citations": [],
            "source_departments": [],
            "confidence": 0.0,
            "feedback_id": "fb-oos",
        }
    )
    assert response.refusal_reason == "out_of_scope"


def test_state_to_response_maps_partial_refusals() -> None:
    response = state_to_response(
        {
            "answer": "Grow path only [1].",
            "status": "partial",
            "confidence": 0.7,
            "feedback_id": "fb-partial",
            "source_departments": [GROW],
            "citations": [{"title": "Grow Doc", "url": "https://example.com/grow"}],
            "refusals": [RISK],
            "request_language": "en",
        }
    )
    assert response.status == "partial"
    assert response.refusals == [RISK]


def test_stream_chat_emits_sse_friendly_events() -> None:
    """FR-6.2: stream_chat yields start, node, pipeline, and done events."""
    ctx = UserContext(
        user_id="u1",
        session_id="s1",
        role="engineer",
        home_department=RISK,
    )
    request = ChatRequest(question="What is escalation?")
    sample = ChatResponse(
        answer="Escalation starts at level 1 [1].",
        citations=[],
        source_departments=[RISK],
        confidence=0.8,
        feedback_id="fb-stream",
        status="answered",
    )

    def fake_stream(_state, _config, stream_mode=None):
        modes = stream_mode if isinstance(stream_mode, list) else [stream_mode]
        assert modes == ["updates", "custom"]
        yield (
            "updates",
            {"router": {"intent": "policy_lookup", "target_departments": [RISK]}},
        )
        yield (
            "updates",
            {"respond": {"answer": sample.answer, "status": "answered", "feedback_id": "fb-stream"}},
        )

    mock_graph = MagicMock()
    mock_graph.stream.side_effect = fake_stream

    with patch("app.api.service.get_compiled_graph", return_value=mock_graph):
        events = list(stream_chat(ctx, request))

    assert events[0] == {"event": "start", "data": {"question": request.question}}
    assert events[1]["event"] == "node"
    assert events[1]["data"]["node"] == "router"
    assert events[1]["data"]["step_key"] == "router"
    assert "step_label" in events[1]["data"]
    assert "elapsed_ms" in events[1]["data"]
    pipeline = [e for e in events if e["event"] == "pipeline"]
    assert len(pipeline) >= 2
    assert pipeline[0]["data"]["phase"] == "start"
    assert pipeline[0]["data"]["step_key"] == "router"
    assert pipeline[-1]["data"]["phase"] == "end"
    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["status"] == "answered"
    assert events[-1]["data"]["feedback_id"] == "fb-stream"


def test_record_chat_outcome_registers_feedback_and_audit(requires_mysql) -> None:
    _ = requires_mysql
    ctx = UserContext(
        user_id="audit-user",
        session_id="audit-session",
        role="engineer",
        home_department=RISK,
    )
    request = ChatRequest(question="What is the refund policy?")
    response = ChatResponse(
        answer="Refunds take 7 days [1].",
        citations=[{"title": "Refund Policy", "url": "https://example.com/refund"}],
        source_departments=[RISK],
        confidence=0.75,
        feedback_id="fb-audit-record",
        status="answered",
    )

    from app.api.service import get_audit_store, get_feedback_store

    record_chat_outcome(ctx, request, response, latency_ms=321)

    up, down = get_feedback_store().counts()
    assert up == 0 and down == 0  # pending registration only

    metrics = get_audit_store().dashboard_metrics()
    assert metrics["query_count"] >= 1
    latest = metrics["history"][0]
    assert latest["status"] == "answered"
    assert latest["latency_ms"] == 321
