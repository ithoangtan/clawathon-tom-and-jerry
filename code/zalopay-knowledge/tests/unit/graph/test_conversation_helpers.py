"""STM conversation helper tests — FR-1.3 follow-up support."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.nodes._helpers import build_retrieval_query, format_conversation_history


def test_format_conversation_history_empty():
    assert format_conversation_history([]) == ""
    assert format_conversation_history(None) == ""


def test_format_conversation_history_excludes_current_turn():
    messages = [
        HumanMessage(content="What is the escalation process?"),
        AIMessage(content="Escalation starts with level 1 alerts."),
        HumanMessage(content="And what's the SLA for that?"),
    ]
    history = format_conversation_history(messages, exclude_last=True)
    assert "escalation process" in history.lower()
    assert "level 1" in history.lower()
    assert "SLA" not in history


def test_build_retrieval_query_includes_prior_turns():
    messages = [
        HumanMessage(content="Settlement reconciliation with banks?"),
        AIMessage(content="Reconciliation runs nightly per the runbook."),
        HumanMessage(content="And what's the SLA for that?"),
    ]
    query = build_retrieval_query("And what's the SLA for that?", messages)
    assert "Follow-up question: And what's the SLA for that?" in query
    assert "reconciliation" in query.lower()


def test_build_retrieval_query_first_turn_unchanged():
    messages = [HumanMessage(content="How does KYC work?")]
    assert build_retrieval_query("How does KYC work?", messages) == "How does KYC work?"
