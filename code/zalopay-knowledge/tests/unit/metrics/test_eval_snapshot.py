"""Unit tests for eval snapshot loading."""

from __future__ import annotations

import json
from pathlib import Path

from app.metrics.eval_snapshot import load_eval_snapshot


def test_load_eval_snapshot_empty_when_missing(tmp_path: Path) -> None:
    snap = load_eval_snapshot(tmp_path / "missing.json")
    assert snap["eval_golden_total"] == 0
    assert snap["eval_faithfulness"] == 0.0


def test_load_eval_snapshot_parses_report(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "total": 44,
                "faithfulness": 0.88,
                "answer_relevance": 0.92,
                "refusal_precision": 1.0,
                "refusal_recall": 0.875,
                "context_recall_at_k": {"5": 0.75},
                "context_precision_at_k": {"5": 0.6},
                "generated_at": "2026-06-13T00:00:00Z",
                "mode": "stub",
            }
        )
    )
    snap = load_eval_snapshot(report)
    assert snap["eval_golden_total"] == 44
    assert snap["eval_faithfulness"] == 0.88
    assert snap["eval_context_recall_at_5"] == 0.75
    assert snap["eval_last_run_at"] == "2026-06-13T00:00:00Z"
