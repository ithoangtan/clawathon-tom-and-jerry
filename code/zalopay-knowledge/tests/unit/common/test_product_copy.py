"""Product copy helpers — escalation, scope, disclaimer (PM MUST 🟢)."""

from __future__ import annotations

from app.common.product_copy import (
    append_high_stakes_disclaimer_if_needed,
    escalation_hint,
    high_stakes_disclaimer,
    is_high_stakes_chunk,
    is_high_stakes_content,
    maybe_append_high_stakes_disclaimer,
    out_of_scope_notice,
    refusal_body,
)
from tests.department_fixtures import GROW, RISK


def test_out_of_scope_lists_mvp_departments() -> None:
    en = out_of_scope_notice("en")
    assert "Risk" in en
    assert "Growth Enablement" in en
    assert "Bank Partnerships" in en
    assert "No web search" in en


def test_escalation_hint_includes_teams_channel() -> None:
    hint = escalation_hint("en", [RISK])
    assert "Risk Management" in hint
    assert "Lan Nguyen" in hint


def test_refusal_body_includes_escalation_and_scope() -> None:
    body = refusal_body("en", [RISK, GROW])
    assert "Not covered in the docs" in body
    assert "Risk Management" in body
    assert "MVP scope" in body


def test_high_stakes_disclaimer_pattern() -> None:
    line = high_stakes_disclaimer("en", "Risk team", "2024-06-01")
    assert "Verify with Risk team" in line
    assert "2024-06-01" in line


def test_is_high_stakes_content_detects_policy_doc_type() -> None:
    assert is_high_stakes_content(
        citations=[{"doc_type": "Risk", "title": "Notes"}],
        answer="General update.",
    )


def test_maybe_append_high_stakes_disclaimer() -> None:
    answer = maybe_append_high_stakes_disclaimer(
        "The fraud threshold is 10M VND.",
        lang="en",
        citations=[{"doc_type": "Risk", "last_modified": "2024-06-01", "title": "Fraud policy"}],
        departments=[RISK],
    )
    assert "Verify with" in answer
    assert "2024-06-01" in answer


def test_is_high_stakes_chunk_detects_policy_title() -> None:
    assert is_high_stakes_chunk({"title": "Escalation Policy", "doc_type": "Operation"})


def test_append_high_stakes_disclaimer_adds_owner_line() -> None:
    answer = append_high_stakes_disclaimer_if_needed(
        "Limit is 10M [1].",
        "en",
        [
            {
                "title": "Risk limit policy",
                "department": RISK,
                "last_modified": "2024-06-01T00:00:00Z",
            }
        ],
    )
    assert "Verify with Lan Nguyen" in answer
    assert "2024-06-01" in answer


def test_append_high_stakes_disclaimer_skips_when_present() -> None:
    answer = "_Verify with Risk team, as of 2024-01-01._"
    assert (
        append_high_stakes_disclaimer_if_needed(
            answer,
            "en",
            [{"title": "Compliance policy", "department": RISK}],
        )
        == answer
    )
