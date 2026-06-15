"""Unit tests for workflow identity slug labels."""

from __future__ import annotations

from app.workflow.labels import slugify, workflow_label


def test_slugify_basic():
    assert slugify("Risk: Campaign Review — Lucky Wheel") == "risk-campaign-review-lucky-wheel"


def test_slugify_strips_vietnamese_diacritics():
    assert slugify("Đối soát Thanh Toán") == "doi-soat-thanh-toan"


def test_slugify_collapses_separators():
    assert slugify("  A / B  &  C  ") == "a-b-c"


def test_workflow_label_prefix():
    assert workflow_label("Risk: Campaign Review") == "wf-risk-campaign-review"


def test_workflow_label_empty_fallback():
    assert workflow_label("!!!") == "wf-unknown"


def test_label_is_jira_safe():
    label = workflow_label("Ops: Merchant Onboarding — Enterprise")
    assert " " not in label and ":" not in label
    assert label == "wf-ops-merchant-onboarding-enterprise"
