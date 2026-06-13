from __future__ import annotations

"""North-star and guardrail metrics for the MVP dashboard (PM MUST 🟢)."""

from typing import Any

NORTH_STAR_METRIC = "deflection_rate"
"""Share of queries answered (full or partial) without doc refusal."""

GUARDRAIL_METRIC = "answered_wrong_rate"
"""Thumbs-down / total feedback — proxy for answered-wrong rate."""


def deflection_rate(*, answered: int, partial: int, total: int) -> float:
    """Compute north-star deflection rate from query status counts."""
    if total <= 0:
        return 0.0
    return (answered + partial) / total


def answered_wrong_rate(*, feedback_down: int, feedback_total: int) -> float:
    """Compute guardrail answered-wrong rate from feedback counts."""
    if feedback_total <= 0:
        return 0.0
    return feedback_down / feedback_total


def merge_dashboard_metrics(
    audit: dict[str, Any],
    *,
    feedback_up: int,
    feedback_down: int,
    eval_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge audit aggregates, feedback guardrail, and optional eval snapshot."""
    merged = dict(audit)
    feedback_total = feedback_up + feedback_down
    merged["feedback_up"] = feedback_up
    merged["feedback_down"] = feedback_down
    merged[GUARDRAIL_METRIC] = answered_wrong_rate(
        feedback_down=feedback_down,
        feedback_total=feedback_total,
    )
    if eval_snapshot:
        merged.update(eval_snapshot)
    return merged
