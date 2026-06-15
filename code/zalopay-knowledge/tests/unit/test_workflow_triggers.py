"""Unit tests for the event→trigger matcher (S2)."""

from __future__ import annotations

from app.integrations.jira_events import normalize_jira_event
from app.workflow.models import WorkflowDefinition, WorkflowTrigger
from app.workflow.triggers import match_trigger


def _defn(*triggers: WorkflowTrigger) -> WorkflowDefinition:
    return WorkflowDefinition(name="W", definition_status="ACTIVE", triggers=list(triggers))


def _ev(**kw) -> object:
    return normalize_jira_event(kw)


def test_status_exact_match():
    defn = _defn(WorkflowTrigger(event_type="status_changed", from_status="SUBMITTED",
                                 to_status="UNDER REVIEW", action="run review"))
    ev = _ev(event_type="status_changed", issue_key="K-1", status_from="SUBMITTED", status_to="UNDER REVIEW")
    assert match_trigger(ev, defn).action == "run review"


def test_status_wildcard_from():
    defn = _defn(WorkflowTrigger(event_type="status_changed", from_status="*",
                                 to_status="APPROVED", action="post summary"))
    ev = _ev(event_type="status_changed", issue_key="K-1", status_from="ANYTHING", status_to="APPROVED")
    assert match_trigger(ev, defn).action == "post summary"


def test_status_no_match_wrong_target():
    defn = _defn(WorkflowTrigger(event_type="status_changed", to_status="DONE", action="x"))
    ev = _ev(event_type="status_changed", issue_key="K-1", status_to="UNDER REVIEW")
    assert match_trigger(ev, defn) is None


def test_case_insensitive_status():
    defn = _defn(WorkflowTrigger(event_type="status_changed", to_status="approved", action="ok"))
    ev = _ev(event_type="status_changed", issue_key="K-1", status_to="APPROVED")
    assert match_trigger(ev, defn) is not None


def test_comment_contains():
    defn = _defn(WorkflowTrigger(event_type="comment_added", comment_contains="@agent recheck", action="rerun"))
    hit = _ev(event_type="comment_added", issue_key="K-1", comment="please @agent recheck the policy")
    miss = _ev(event_type="comment_added", issue_key="K-1", comment="lgtm")
    assert match_trigger(hit, defn).action == "rerun"
    assert match_trigger(miss, defn) is None


def test_field_changed_match():
    defn = _defn(WorkflowTrigger(event_type="field_changed", field="priority", field_to="High", action="escalate"))
    hit = _ev(event_type="field_changed", issue_key="K-1", field="priority", to="High")
    miss = _ev(event_type="field_changed", issue_key="K-1", field="priority", to="Low")
    assert match_trigger(hit, defn).action == "escalate"
    assert match_trigger(miss, defn) is None


def test_first_match_wins_document_order():
    defn = _defn(
        WorkflowTrigger(event_type="status_changed", to_status="DONE", action="first"),
        WorkflowTrigger(event_type="status_changed", to_status="DONE", action="second"),
    )
    ev = _ev(event_type="status_changed", issue_key="K-1", status_to="DONE")
    assert match_trigger(ev, defn).action == "first"


def test_event_type_must_match():
    defn = _defn(WorkflowTrigger(event_type="comment_added", action="x"))
    ev = _ev(event_type="status_changed", issue_key="K-1", status_to="DONE")
    assert match_trigger(ev, defn) is None
