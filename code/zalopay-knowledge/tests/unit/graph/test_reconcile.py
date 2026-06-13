"""Reconcile node tests — merge paths and conflict detection."""

from __future__ import annotations

import json

from app.config import Settings
from app.graph.nodes.reconcile import make_reconcile_node
from app.graph.nodes.respond import make_respond_node
from app.graph.state import Citation, DeptResult

from tests.unit.graph.conftest import StubLLM


def test_reconcile_all_refused_fast_path(test_settings: Settings):
    node = make_reconcile_node(StubLLM(), settings=test_settings)
    out = node(
        {
            "dept_results": [
                DeptResult(
                    department="risk",
                    status="refused",
                    answer="",
                    citations=[],
                    confidence=0.0,
                    warnings=["no_supporting_sources"],
                )
            ],
            "request_language": "en",
        }
    )
    assert out["status"] == "refused"
    assert out["confidence"] == 0.0
    assert out["citations"] == []
    assert out["conflicts"] == []
    assert "not covered in the docs" in out["answer"].lower()


def test_reconcile_all_refused_vietnamese_message(test_settings: Settings):
    node = make_reconcile_node(StubLLM(), settings=test_settings)
    out = node(
        {
            "dept_results": [
                DeptResult(
                    department="risk",
                    status="refused",
                    answer="",
                    citations=[],
                    confidence=0.0,
                    warnings=["no_supporting_sources"],
                )
            ],
            "request_language": "vi",
        }
    )
    assert out["status"] == "refused"
    assert "Không có thông tin trong tài liệu" in out["answer"]


def test_reconcile_single_department_passthrough(
    test_settings: Settings, answered_dept_result: DeptResult
):
    node = make_reconcile_node(StubLLM(), settings=test_settings)
    out = node(
        {
            "dept_results": [answered_dept_result],
            "request_language": "en",
        }
    )
    assert out["answer"] == answered_dept_result["answer"]
    assert out["citations"] == answered_dept_result["citations"]
    assert out["conflicts"] == []
    assert out["status"] == "answered"
    assert out["confidence"] == answered_dept_result["confidence"]


def test_reconcile_partial_when_some_departments_refused(
    test_settings: Settings, answered_dept_result: DeptResult
):
    node = make_reconcile_node(StubLLM(), settings=test_settings)
    out = node(
        {
            "dept_results": [
                answered_dept_result,
                DeptResult(
                    department="grow_enablement",
                    status="refused",
                    answer="",
                    citations=[],
                    confidence=0.0,
                    warnings=[],
                ),
            ],
            "request_language": "en",
        }
    )
    assert out["status"] == "partial"
    assert out["refusals"] == ["grow_enablement"]


def test_reconcile_detects_conflicts_from_llm_merge(test_settings: Settings):
    risk_cite = Citation(title="Risk Policy", url="https://example.com/risk")
    grow_cite = Citation(title="Grow Policy", url="https://example.com/grow")
    results = [
        DeptResult(
            department="risk",
            status="answered",
            answer="Limit is 10M VND [1].",
            citations=[risk_cite],
            confidence=0.8,
            warnings=[],
        ),
        DeptResult(
            department="grow_enablement",
            status="answered",
            answer="Limit is 5M VND [1].",
            citations=[grow_cite],
            confidence=0.75,
            warnings=[],
        ),
    ]
    merge_payload = json.dumps(
        {
            "merged_answer": "Departments disagree on the limit [1][2].",
            "conflicts": [
                {
                    "topic": "transaction limit",
                    "sides": [
                        {
                            "department": "risk",
                            "statement": "Limit is 10M VND",
                            "citation_index": 1,
                        },
                        {
                            "department": "grow_enablement",
                            "statement": "Limit is 5M VND",
                            "citation_index": 1,
                        },
                    ],
                }
            ],
        }
    )
    node = make_reconcile_node(StubLLM(merge_payload), settings=test_settings)
    out = node({"dept_results": results, "request_language": "en"})

    assert len(out["conflicts"]) == 1
    conflict = out["conflicts"][0]
    assert conflict["topic"] == "transaction limit"
    assert len(conflict["sides"]) == 2
    depts = {s["department"] for s in conflict["sides"]}
    assert depts == {"risk", "grow_enablement"}
    assert out["status"] == "partial"
    assert out["confidence"] < 0.8


def test_reconcile_concatenates_on_llm_failure(test_settings: Settings):
    results = [
        DeptResult(
            department="risk",
            status="answered",
            answer="Risk answer [1].",
            citations=[Citation(title="R", url="https://r")],
            confidence=0.8,
            warnings=[],
        ),
        DeptResult(
            department="grow_enablement",
            status="answered",
            answer="Grow answer [1].",
            citations=[Citation(title="G", url="https://g")],
            confidence=0.7,
            warnings=[],
        ),
    ]
    from app.ports.errors import LLMUnavailable

    node = make_reconcile_node(
        StubLLM(side_effect=LLMUnavailable()),
        settings=test_settings,
    )
    out = node({"dept_results": results, "request_language": "en"})
    assert "Risk answer" in out["answer"]
    assert "Grow answer" in out["answer"]
    assert len(out["citations"]) == 2
    assert out["conflicts"] == []


def test_reconcile_shifts_citation_markers_for_merge(test_settings: Settings):
    results = [
        DeptResult(
            department="risk",
            status="answered",
            answer="Risk limit is 10M [1].",
            citations=[Citation(title="Risk Policy", url="https://example.com/risk")],
            confidence=0.8,
            warnings=[],
        ),
        DeptResult(
            department="bank_partnerships",
            status="answered",
            answer="Partner limit is 5M [1].",
            citations=[Citation(title="Bank Policy", url="https://example.com/bank")],
            confidence=0.75,
            warnings=[],
        ),
    ]
    merge_payload = json.dumps(
        {
            "merged_answer": "Both departments cite different limits [1][2].",
            "conflicts": [],
        }
    )
    node = make_reconcile_node(StubLLM(merge_payload), settings=test_settings)
    out = node({"dept_results": results, "request_language": "en"})

    assert len(out["citations"]) == 2
    assert out["citations"][0]["url"] == "https://example.com/risk"
    assert out["citations"][1]["url"] == "https://example.com/bank"
    assert "[1][2]" in out["answer"]


def test_reconcile_conflict_surfaces_through_respond(test_settings: Settings):
    risk_cite = Citation(title="Risk Policy", url="https://example.com/risk")
    bank_cite = Citation(title="Bank Policy", url="https://example.com/bank")
    results = [
        DeptResult(
            department="risk",
            status="answered",
            answer="Limit is 10M VND [1].",
            citations=[risk_cite],
            confidence=0.8,
            warnings=[],
        ),
        DeptResult(
            department="bank_partnerships",
            status="answered",
            answer="Limit is 5M VND [1].",
            citations=[bank_cite],
            confidence=0.75,
            warnings=[],
        ),
    ]
    merge_payload = json.dumps(
        {
            "merged_answer": "Departments disagree on the limit [1][2].",
            "conflicts": [
                {
                    "topic": "transaction limit",
                    "sides": [
                        {
                            "department": "risk",
                            "statement": "Limit is 10M VND",
                            "citation_index": 1,
                        },
                        {
                            "department": "bank_partnerships",
                            "statement": "Limit is 5M VND",
                            "citation_index": 1,
                        },
                    ],
                }
            ],
        }
    )
    reconcile = make_reconcile_node(StubLLM(merge_payload), settings=test_settings)
    respond = make_respond_node(settings=test_settings)

    merged = reconcile({"dept_results": results, "request_language": "en"})
    final = respond(
        {
            "dept_results": results,
            "request_language": "en",
            **merged,
        }
    )

    assert final["status"] == "partial"
    assert len(final["conflicts"]) == 1
    assert final["conflicts"][0]["topic"] == "transaction limit"
    assert set(final["source_departments"]) == {"risk", "bank_partnerships"}
    assert len(final["citations"]) == 2
