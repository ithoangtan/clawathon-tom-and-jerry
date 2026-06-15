"""Unit tests for the LLM-based workflow parser (Phase 3)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.config import Settings
from app.ports.errors import LLMUnavailable, WorkflowParseError
from app.ports.types import LLMResult
from app.workflow.models import WorkflowDefinition
from app.workflow.parser import is_executable, parse_workflow


class StubLLM:
    """LLM stub returning canned text (or raising) — records the call."""

    def __init__(self, text: str = "{}", *, raises: Exception | None = None) -> None:
        self._text = text
        self._raises = raises
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> LLMResult:
        self.calls.append(kwargs)
        if self._raises:
            raise self._raises
        return LLMResult(text=self._text, raw={}, usage={})


SETTINGS = Settings(_env_file=None)

# A canned parse result mirroring the SOLUTION template's Campaign Risk Review page.
_PARSED = {
    "name": "Risk: Campaign Review — Lucky Wheel",
    "trigger": "When a new campaign needs risk review",
    "owner": "Risk Team",
    "participants": ["Risk Reviewer", "Biz Creator", "Product Ops"],
    "definition_status": "ACTIVE",
    "jira_source": "existing-ticket",
    "version": "2024-06-15",
    "lifecycle": [
        {"status": "SUBMITTED", "meaning": "Ticket created", "next": ["UNDER REVIEW"]},
        {"status": "DONE", "meaning": "Complete", "next": []},
    ],
    "executable_statuses": ["SUBMITTED", "UNDER REVIEW"],
    "steps": [
        {
            "index": 1,
            "title": "Fetch Jira ticket + campaign page",
            "responsible_role": "Risk Reviewer",
            "responsible_department": "Risk",
            "type": "fetch",
            "input": "Jira key",
            "action": "Pull ticket and campaign page",
            "output": "Raw campaign context",
            "checklist": [],
            "policy_ref": None,
            "condition": None,
        },
        {
            "index": 2,
            "title": "Check payment-method policy",
            "responsible_role": "Risk Reviewer",
            "responsible_department": "Risk",
            "type": "rag",
            "input": "Campaign summary",
            "action": "Look up payment method abuse policy",
            "output": "Findings",
            "checklist": ["VietQR blocked?", "Starter excluded?"],
            "policy_ref": "https://confluence/payment-policy",
            "condition": None,
        },
        {
            "index": 3,
            "title": "Escalation gate",
            "responsible_role": "Risk Reviewer",
            "responsible_department": "Risk",
            "type": "gate",
            "input": None,
            "action": None,
            "output": None,
            "checklist": [],
            "policy_ref": None,
            "condition": "gift value > 1,000,000 → escalate Head of Risk",
        },
    ],
}


def test_parse_workflow_extracts_fields():
    llm = StubLLM(json.dumps(_PARSED))
    defn = parse_workflow("# some page text", llm=llm, settings=SETTINGS)

    assert isinstance(defn, WorkflowDefinition)
    assert defn.name == "Risk: Campaign Review — Lucky Wheel"
    assert defn.definition_status == "ACTIVE"
    assert defn.jira_source == "existing-ticket"
    assert [s.index for s in defn.steps] == [1, 2, 3]
    assert [s.type for s in defn.steps] == ["fetch", "rag", "gate"]
    assert defn.steps[1].checklist == ["VietQR blocked?", "Starter excluded?"]
    assert defn.steps[1].policy_ref == "https://confluence/payment-policy"
    assert defn.steps[2].condition.startswith("gift value")
    assert defn.executable_statuses == ["SUBMITTED", "UNDER REVIEW"]
    # SMALL tier + JSON response format were requested.
    assert llm.calls[0]["response_format"] == "json"


def test_parse_workflow_normalises_legacy_status():
    payload = {**_PARSED, "definition_status": "IN PROCESS"}
    defn = parse_workflow("x", llm=StubLLM(json.dumps(payload)), settings=SETTINGS)
    assert defn.definition_status == "ACTIVE"


def test_parse_workflow_handles_fenced_json():
    fenced = "```json\n" + json.dumps(_PARSED) + "\n```"
    defn = parse_workflow("x", llm=StubLLM(fenced), settings=SETTINGS)
    assert defn.name == _PARSED["name"]


def test_parse_workflow_malformed_json_raises():
    with pytest.raises(WorkflowParseError):
        parse_workflow("x", llm=StubLLM("not json at all"), settings=SETTINGS)


def test_parse_workflow_missing_name_raises():
    payload = {**_PARSED}
    payload.pop("name")
    with pytest.raises(WorkflowParseError):
        parse_workflow("x", llm=StubLLM(json.dumps(payload)), settings=SETTINGS)


def test_parse_workflow_empty_page_raises():
    with pytest.raises(WorkflowParseError):
        parse_workflow("   ", llm=StubLLM("{}"), settings=SETTINGS)


def test_parse_workflow_llm_unavailable_raises_parse_error():
    llm = StubLLM(raises=LLMUnavailable())
    with pytest.raises(WorkflowParseError):
        parse_workflow("x", llm=llm, settings=SETTINGS)


@pytest.mark.parametrize(
    "status,expected_ok",
    [
        ("ACTIVE", True),
        ("DEPRECATED", False),
        ("DRAFT", False),
        ("IN_REVIEW", False),
        ("ARCHIVED", False),
    ],
)
def test_is_executable_gate(status: str, expected_ok: bool):
    defn = WorkflowDefinition(name="W", definition_status=status, steps=[])
    ok, reason = is_executable(defn)
    assert ok is expected_ok
    if not ok:
        assert reason  # a human-readable reason/warning is provided
    else:
        assert reason is None
