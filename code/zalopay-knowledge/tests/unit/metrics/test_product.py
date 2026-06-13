"""Unit tests for app.metrics.product."""

from __future__ import annotations

from app.metrics.product import (
    GUARDRAIL_METRIC,
    NORTH_STAR_METRIC,
    answered_wrong_rate,
    deflection_rate,
    merge_dashboard_metrics,
)


def test_north_star_and_guardrail_metric_names() -> None:
    assert NORTH_STAR_METRIC == "deflection_rate"
    assert GUARDRAIL_METRIC == "answered_wrong_rate"


def test_deflection_rate() -> None:
    assert deflection_rate(answered=7, partial=2, total=10) == 0.9
    assert deflection_rate(answered=0, partial=0, total=0) == 0.0


def test_answered_wrong_rate() -> None:
    assert answered_wrong_rate(feedback_down=2, feedback_total=10) == 0.2
    assert answered_wrong_rate(feedback_down=0, feedback_total=0) == 0.0


def test_merge_dashboard_metrics() -> None:
    merged = merge_dashboard_metrics(
        {"query_count": 5, "deflection_rate": 0.8, "history": []},
        feedback_up=9,
        feedback_down=1,
        eval_snapshot={"eval_golden_total": 44, "eval_faithfulness": 0.91},
    )
    assert merged["feedback_up"] == 9
    assert merged["answered_wrong_rate"] == 0.1
    assert merged["eval_golden_total"] == 44
