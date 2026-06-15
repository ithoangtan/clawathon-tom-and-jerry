"""ingest_context node tests — index readiness and context population."""

from __future__ import annotations

from app.config import Settings
from app.graph.nodes.ingest_context import make_ingest_context_node

from tests.unit.graph.conftest import StubRetriever


def test_ingest_context_sets_allowed_departments_to_all():
    settings = Settings(_env_file=None)
    node = make_ingest_context_node(StubRetriever(ready=True), settings=settings)
    out = node(
        {
            "question": "hello",
            "role": "business",
            "pinned": [],
            "request_language": "en",
        }
    )
    # Knowledge is open — all routable Q&A departments always allowed regardless of
    # role (the non-routable ``workflow`` registry is never a Q&A target).
    from app.common.departments import routable_keys
    assert set(out["allowed_departments"]) == set(routable_keys())


def test_ingest_detects_vietnamese_question():
    settings = Settings(_env_file=None)
    node = make_ingest_context_node(StubRetriever(ready=True), settings=settings)
    out = node({"question": "Quy trình đối soát thanh toán như thế nào?", "role": "engineer"})
    assert out["request_language"] == "vi"


def test_ingest_defaults_english_for_ascii_question():
    settings = Settings(_env_file=None)
    node = make_ingest_context_node(StubRetriever(ready=True), settings=settings)
    out = node({"question": "What is the refund policy?", "role": "engineer"})
    assert out["request_language"] == "en"


def test_ingest_refuses_when_index_not_ready():
    settings = Settings(_env_file=None)
    node = make_ingest_context_node(StubRetriever(ready=False), settings=settings)
    out = node({"question": "test", "request_language": "en", "role": "engineer"})
    assert out["status"] == "refused"
    assert out["answer"]
    assert "retriever_not_ready" in out.get("errors", [])


def test_ingest_refusal_message_localised_vietnamese():
    settings = Settings(_env_file=None)
    node = make_ingest_context_node(StubRetriever(ready=False), settings=settings)
    out = node({"question": "test", "request_language": "vi", "role": "engineer"})
    assert "chưa sẵn sàng" in out["answer"].lower()


def test_ingest_recall_populates_preferences():
    settings = Settings(_env_file=None)

    def recall(user_id: str, session_id: str) -> str | None:
        assert user_id == "u1"
        assert session_id == "s1"
        return "prefers concise answers"

    node = make_ingest_context_node(
        StubRetriever(ready=True),
        recall=recall,
        settings=settings,
    )
    out = node(
        {
            "question": "test",
            "user_id": "u1",
            "session_id": "s1",
            "role": "engineer",
        }
    )
    assert out["recalled_preferences"] == "prefers concise answers"
    assert out["memory_degraded"] is False


def test_ingest_builds_stm_fields_from_messages():
    """FR-1.3: conversation_history and retrieval_query for follow-ups."""
    from langchain_core.messages import AIMessage, HumanMessage

    settings = Settings(_env_file=None)
    node = make_ingest_context_node(StubRetriever(ready=True), settings=settings)
    messages = [
        HumanMessage(content="What is the escalation process?"),
        AIMessage(content="Escalation starts at level 1."),
        HumanMessage(content="And what's the SLA for that?"),
    ]
    out = node(
        {
            "question": "And what's the SLA for that?",
            "messages": messages,
            "role": "engineer",
        }
    )
    assert "escalation process" in out["conversation_history"].lower()
    assert "SLA" not in out["conversation_history"]
    assert "Follow-up question: And what's the SLA for that?" in out["retrieval_query"]
    assert "level 1" in out["retrieval_query"].lower()


def test_ingest_recall_failure_degrades_gracefully():
    settings = Settings(_env_file=None)

    def recall(_user_id: str, _session_id: str) -> str | None:
        raise RuntimeError("stm down")

    node = make_ingest_context_node(
        StubRetriever(ready=True),
        recall=recall,
        settings=settings,
    )
    out = node(
        {
            "question": "test",
            "user_id": "u1",
            "session_id": "s1",
            "role": "engineer",
        }
    )
    assert out["recalled_preferences"] is None
    assert out["memory_degraded"] is True
