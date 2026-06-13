"""Eval golden set and metrics tests (Eval MUST 🟢)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.metrics import (
    aggregate_eval,
    answer_relevance,
    context_precision_at_k,
    context_recall_at_k,
    faithfulness_score,
    refusal_counts,
)
from evals.run_eval import run_stub

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "evals" / "golden_cases.json"


@pytest.fixture()
def golden_cases() -> list[dict]:
    return json.loads(GOLDEN_PATH.read_text())


def test_golden_set_size_and_departments(golden_cases: list[dict]) -> None:
    assert 30 <= len(golden_cases) <= 50
    dept_cases = [c for c in golden_cases if c.get("department")]
    assert len(dept_cases) >= 36
    risk = sum(1 for c in dept_cases if c["department"] == "risk")
    grow = sum(1 for c in dept_cases if c["department"] == "grow_enablement")
    bank = sum(1 for c in dept_cases if c["department"] == "bank_partnerships")
    assert risk >= 10
    assert grow >= 10
    assert bank >= 10


def test_golden_cases_have_required_fields(golden_cases: list[dict]) -> None:
    for case in golden_cases:
        assert case.get("id")
        assert case.get("question")
        expect = case.get("expect") or {}
        assert "status" in expect
        assert "must_refuse" in expect
        if not expect.get("must_refuse"):
            assert expect.get("answer_keywords"), f"{case['id']} missing answer_keywords"
            assert expect.get("citation_keywords"), f"{case['id']} missing citation_keywords"
            assert case.get("retrieval", {}).get("relevant_chunk_ids"), (
                f"{case['id']} missing retrieval.relevant_chunk_ids"
            )


def test_context_recall_and_precision_at_k() -> None:
    retrieved = ["a", "b", "c", "d", "e"]
    relevant = {"a", "c", "x"}
    assert context_recall_at_k(retrieved, relevant, 5) == pytest.approx(2 / 3)
    assert context_precision_at_k(retrieved, relevant, 5) == pytest.approx(2 / 5)


def test_faithfulness_and_relevance_heuristics() -> None:
    answer = "Escalation requires manager approval within 24 hours."
    sources = ["Risk escalation requires manager approval within 24 hours for alerts."]
    assert faithfulness_score(answer, sources) >= 0.5
    assert answer_relevance(answer, ["escalation", "manager"]) == 1.0


def test_refusal_precision_recall() -> None:
    cases = [
        {"id": "1", "expect": {"must_refuse": True}},
        {"id": "2", "expect": {"must_refuse": True}},
        {"id": "3", "expect": {"must_refuse": False}},
    ]
    actual = {"1": "refused", "2": "answered", "3": "answered"}
    counts = refusal_counts(cases, actual)
    assert counts.true_positive == 1
    assert counts.false_negative == 1
    assert counts.true_negative == 1
    assert counts.false_positive == 0


def test_aggregate_eval_stub_results(golden_cases: list[dict]) -> None:
    results = []
    for case in golden_cases:
        expect = case["expect"]
        results.append(
            {
                "id": case["id"],
                "status": expect["status"],
                "answer": "escalation policy answer",
                "retrieved_chunk_ids": (case.get("retrieval") or {}).get(
                    "relevant_chunk_ids", []
                ),
                "source_texts": ["escalation policy source text"],
            }
        )
    summary = aggregate_eval(golden_cases, results)
    assert summary.total == len(golden_cases)
    assert summary.status_pass == len(golden_cases)
    assert summary.refusal_precision == 1.0
    assert summary.refusal_recall == 1.0


def test_run_eval_stub_runner(golden_cases: list[dict]) -> None:
    _, summary = run_stub(golden_cases)
    assert summary["mode"] == "stub"
    assert summary["status_pass"] == len(golden_cases)
    assert summary["total"] == len(golden_cases)
    assert "context_recall_at_k" in summary
    assert "hallucination_rate" in summary
