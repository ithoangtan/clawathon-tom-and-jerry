from __future__ import annotations

"""Load the latest golden-set eval report for dashboard surfacing."""

import json
from pathlib import Path
from typing import Any

DEFAULT_REPORT_PATH = Path(__file__).resolve().parents[2] / "evals" / "last_eval_report.json"


def load_eval_snapshot(path: Path | None = None) -> dict[str, Any]:
    """Return eval fields for ``GET /api/dashboard``, or empty defaults."""
    report_path = path or DEFAULT_REPORT_PATH
    if not report_path.is_file():
        return _empty_snapshot()

    try:
        raw = json.loads(report_path.read_text())
    except (OSError, json.JSONDecodeError):
        return _empty_snapshot()

    return {
        "eval_golden_total": int(raw.get("total") or raw.get("cases") or 0),
        "eval_faithfulness": float(raw.get("faithfulness") or 0.0),
        "eval_answer_relevance": float(raw.get("answer_relevance") or 0.0),
        "eval_refusal_precision": float(raw.get("refusal_precision") or 0.0),
        "eval_refusal_recall": float(raw.get("refusal_recall") or 0.0),
        "eval_context_recall_at_5": float(
            (raw.get("context_recall_at_k") or {}).get("5") or 0.0
        ),
        "eval_context_precision_at_5": float(
            (raw.get("context_precision_at_k") or {}).get("5") or 0.0
        ),
        "eval_last_run_at": raw.get("generated_at"),
        "eval_mode": raw.get("mode"),
    }


def _empty_snapshot() -> dict[str, Any]:
    return {
        "eval_golden_total": 0,
        "eval_faithfulness": 0.0,
        "eval_answer_relevance": 0.0,
        "eval_refusal_precision": 0.0,
        "eval_refusal_recall": 0.0,
        "eval_context_recall_at_5": 0.0,
        "eval_context_precision_at_5": 0.0,
        "eval_last_run_at": None,
        "eval_mode": None,
    }
