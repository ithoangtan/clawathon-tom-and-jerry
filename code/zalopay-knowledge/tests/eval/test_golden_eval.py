"""Pytest for YAML golden set + ``run_golden`` metrics (Eval MUST 🟢)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from evals.metrics import (
    context_precision_at_k,
    context_recall_at_k,
    faithfulness_score,
    refusal_counts,
)
from tests.eval.run_golden import DEFAULT_YAML, load_golden_yaml, run_stub, yaml_to_eval_cases
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def yaml_cases() -> list[dict]:
    return load_golden_yaml(DEFAULT_YAML)


def test_golden_yaml_size_and_departments(yaml_cases: list[dict]) -> None:
    assert len(yaml_cases) >= 35
    dept_cases = [c for c in yaml_cases if c.get("department")]
    assert len(dept_cases) >= 36
    risk = sum(1 for c in dept_cases if c["department"] == RISK)
    grow = sum(1 for c in dept_cases if c["department"] == GROW)
    bank = sum(1 for c in dept_cases if c["department"] == BANK)
    assert risk >= 10
    assert grow >= 10
    assert bank >= 10


def test_golden_yaml_required_fields(yaml_cases: list[dict]) -> None:
    for case in yaml_cases:
        assert case.get("id")
        assert case.get("question")
        assert case.get("expected_behavior") in ("answer", "refuse")
        assert "expected_citation_url" in case
        if case["expected_behavior"] == "refuse":
            assert case["expected_citation_url"] == "none"
        else:
            assert isinstance(case["expected_citation_url"], str)
            assert len(case["expected_citation_url"]) > 8


def test_recall_precision_faithfulness_refusal_helpers() -> None:
    retrieved = ["a", "b", "c"]
    relevant = {"a", "b", "x"}
    assert context_recall_at_k(retrieved, relevant, 3) == pytest.approx(2 / 3)
    assert context_precision_at_k(retrieved, relevant, 3) == pytest.approx(2 / 3)
    assert faithfulness_score(
        "Escalation requires manager approval within 24 hours.",
        ["Risk escalation requires manager approval within 24 hours."],
    ) >= 0.5
    counts = refusal_counts(
        [{"id": "1", "expect": {"must_refuse": True}}, {"id": "2", "expect": {"must_refuse": False}}],
        {"1": "refused", "2": "answered"},
    )
    assert counts.precision == 1.0
    assert counts.recall == 1.0


def test_run_golden_stub_perfect_scores(yaml_cases: list[dict]) -> None:
    _, report = run_stub(yaml_cases)
    assert report["cases"] == len(yaml_cases)
    assert report["status_pass"] == len(yaml_cases)
    assert report["refusal_precision"] == 1.0
    assert report["refusal_recall"] == 1.0
    assert "context_recall_at_k" in report
    assert "context_precision_at_k" in report
    assert "faithfulness" in report


def test_yaml_maps_to_eval_cases(yaml_cases: list[dict]) -> None:
    mapped = yaml_to_eval_cases(yaml_cases)
    assert len(mapped) == len(yaml_cases)
    for row, case in zip(yaml_cases, mapped, strict=True):
        if row["expected_behavior"] == "refuse":
            assert case["expect"]["must_refuse"] is True
            assert case["expect"]["status"] == "refused"
        else:
            assert case["expect"]["must_refuse"] is False
            assert case["expect"]["status"] == "answered"


def test_run_golden_cli_stub(tmp_path: Path) -> None:
    report_path = tmp_path / "golden_report.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tests" / "eval" / "run_golden.py"), "--stub", "--output", str(report_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    body = json.loads(report_path.read_text())
    assert body["cases"] >= 35
    assert body["mode"] == "stub"


def test_golden_yaml_parses() -> None:
    doc = yaml.safe_load(DEFAULT_YAML.read_text())
    assert doc["version"] == 1
    assert len(doc["cases"]) >= 35
