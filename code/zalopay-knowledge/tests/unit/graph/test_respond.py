"""Respond node tests — response assembly and feedback_id."""

from __future__ import annotations

import uuid

from app.config import Settings
from app.graph.nodes.respond import make_respond_node
from app.graph.state import Citation, DeptResult

from tests.unit.graph.conftest import answered_dept_result


def test_respond_issues_feedback_id(test_settings: Settings):
    node = make_respond_node(settings=test_settings)
    out = node({"request_language": "en", "intent": "greeting"})
    assert "feedback_id" in out
    uuid.UUID(out["feedback_id"])


def test_respond_passthrough_ingest_refusal(test_settings: Settings):
    node = make_respond_node(settings=test_settings)
    out = node(
        {
            "status": "refused",
            "answer": "Knowledge base not ready.",
            "request_language": "en",
        }
    )
    assert out["status"] == "refused"
    assert out["answer"] == "Knowledge base not ready."
    assert out["citations"] == []
    assert out["source_departments"] == []


def test_respond_clarify_question(test_settings: Settings):
    node = make_respond_node(settings=test_settings)
    clarify = {"prompt": "Which department?", "options": ["risk"]}
    out = node(
        {
            "clarify_question": clarify,
            "routing_confidence": 0.3,
            "request_language": "en",
        }
    )
    assert out["status"] == "refused"
    assert out["answer"] == "Which department?"
    assert out["clarify_question"] == clarify
    assert out["confidence"] == 0.3


def test_respond_short_circuit_greeting(test_settings: Settings):
    node = make_respond_node(settings=test_settings)
    out = node({"intent": "greeting", "request_language": "en"})
    assert out["status"] == "answered"
    assert "Zalopay" in out["answer"]
    assert out["citations"] == []
    assert out["source_departments"] == []
    assert out["confidence"] == 1.0


def test_respond_normal_answer_from_reconcile(
    test_settings: Settings, answered_dept_result: DeptResult
):
    node = make_respond_node(settings=test_settings)
    cite = answered_dept_result["citations"][0]
    out = node(
        {
            "answer": answered_dept_result["answer"],
            "status": "answered",
            "confidence": answered_dept_result["confidence"],
            "citations": [cite],
            "dept_results": [answered_dept_result],
            "request_language": "en",
        }
    )
    assert out["status"] == "answered"
    assert out["answer"] == answered_dept_result["answer"]
    assert out["citations"] == [cite]
    assert out["source_departments"] == ["risk"]
    assert "feedback_id" in out
    assert out["messages"]
    assert getattr(out["messages"][0], "content", "") == answered_dept_result["answer"]


def test_respond_includes_conflicts(test_settings: Settings):
    node = make_respond_node(settings=test_settings)
    conflict = {
        "topic": "limit",
        "sides": [
            {"department": "risk", "statement": "10M", "citation": Citation(title="R", url="u")}
        ],
    }
    out = node(
        {
            "answer": "Conflicting info.",
            "status": "partial",
            "confidence": 0.5,
            "citations": [],
            "conflicts": [conflict],
            "dept_results": [
                DeptResult(
                    department="risk",
                    status="answered",
                    answer="10M",
                    citations=[],
                    confidence=0.5,
                    warnings=[],
                )
            ],
            "request_language": "en",
        }
    )
    assert out["conflicts"] == [conflict]
    assert out["source_departments"] == ["risk"]
