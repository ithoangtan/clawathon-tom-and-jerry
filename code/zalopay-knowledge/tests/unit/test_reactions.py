"""Unit tests for the generic reaction dispatcher (app.workflow.reactions)."""

from __future__ import annotations

from app.ports.errors import JiraUnavailable
from app.workflow.models import WorkflowDefinition, WorkflowReaction
from app.workflow.reactions import apply_reactions, parse_decision

ISSUE = {"key": "KAN-1", "fields": {"reporter": {"accountId": "acc-reporter-123"}}}


def _defn(*reactions: WorkflowReaction) -> WorkflowDefinition:
    return WorkflowDefinition(name="WF", definition_status="ACTIVE", reactions=list(reactions))


class RecordingJira:
    def __init__(self, *, fail: bool = False) -> None:
        self.assigned: list[dict] = []
        self.labeled: list[dict] = []
        self._fail = fail

    def assign_issue(self, *, key: str, account_id: str) -> dict:
        if self._fail:
            raise JiraUnavailable("boom")
        self.assigned.append({"key": key, "account_id": account_id})
        return {"key": key, "account_id": account_id, "dry_run": False}

    def add_labels(self, *, key: str, labels: list[str]) -> dict:
        self.labeled.append({"key": key, "labels": labels})
        return {"key": key, "labels": labels, "dry_run": False}


class RecordingConfluence:
    def __init__(self) -> None:
        self.appends: list[dict] = []

    def append_to_page(self, *, page_id: str, html_fragment: str) -> dict:
        self.appends.append({"page_id": page_id, "html": html_fragment})
        return {"id": page_id}


def _apply(decision, defn, jira, cw=None):
    return apply_reactions(
        decision, defn, issue_key="KAN-1", report_text="report body",
        issue=ISSUE, jira=jira, confluence_writer=cw or RecordingConfluence(), page_id="1048659",
    )


# ── parse_decision ───────────────────────────────────────────────────────────

def test_parse_decision_variants():
    assert parse_decision("blah\nDECISION: PARTIAL_FAIL") == "PARTIAL_FAIL"
    assert parse_decision("DECISION: partial fail") == "PARTIAL_FAIL"
    assert parse_decision("DECISION = FAIL") == "FAIL"
    assert parse_decision("no token here") is None
    assert parse_decision("") is None


# ── apply_reactions ──────────────────────────────────────────────────────────

def test_pass_only_comments_no_side_effects():
    defn = _defn(WorkflowReaction(decision="PASS", verbs=["comment"]))
    jira = RecordingJira()
    out = _apply("PASS", defn, jira)
    assert jira.assigned == [] and jira.labeled == []
    assert out["verbs"] == []  # 'comment' handled by caller


def test_partial_fail_reassigns_reporter_and_labels():
    defn = _defn(WorkflowReaction(
        decision="PARTIAL_FAIL", verbs=["comment", "reassign:reporter", "label:risk-partial-fail"]))
    jira = RecordingJira()
    out = _apply("PARTIAL_FAIL", defn, jira)
    assert jira.assigned == [{"key": "KAN-1", "account_id": "acc-reporter-123"}]
    assert jira.labeled == [{"key": "KAN-1", "labels": ["risk-partial-fail"]}]
    assert "reassign:acc-reporter-123" in out["verbs"]
    assert "label:risk-partial-fail" in out["verbs"]


def test_reassign_explicit_account_id():
    defn = _defn(WorkflowReaction(decision="FAIL", verbs=["reassign:acc-lead-999"]))
    jira = RecordingJira()
    _apply("FAIL", defn, jira)
    assert jira.assigned == [{"key": "KAN-1", "account_id": "acc-lead-999"}]


def test_append_confluence_verb():
    defn = _defn(WorkflowReaction(decision="FAIL", verbs=["append_confluence"]))
    cw = RecordingConfluence()
    out = _apply("FAIL", defn, RecordingJira(), cw)
    assert cw.appends and cw.appends[0]["page_id"] == "1048659"
    assert "FAIL" in cw.appends[0]["html"]
    assert "append_confluence" in out["verbs"]


def test_unknown_decision_is_noop():
    defn = _defn(WorkflowReaction(decision="PASS", verbs=["reassign:reporter"]))
    jira = RecordingJira()
    out = _apply("SOMETHING_ELSE", defn, jira)
    assert jira.assigned == [] and out["verbs"] == []


def test_no_decision_is_noop():
    defn = _defn(WorkflowReaction(decision="FAIL", verbs=["reassign:reporter"]))
    jira = RecordingJira()
    out = _apply(None, defn, jira)
    assert jira.assigned == [] and out["verbs"] == []


def test_verb_error_degrades_not_raises():
    defn = _defn(WorkflowReaction(decision="FAIL", verbs=["reassign:reporter"]))
    jira = RecordingJira(fail=True)
    out = _apply("FAIL", defn, jira)
    assert out.get("errors")  # captured, no exception


def test_unsupported_verb_recorded():
    defn = _defn(WorkflowReaction(decision="FAIL", verbs=["teleport:mars"]))
    out = _apply("FAIL", defn, RecordingJira())
    assert "teleport:unsupported" in out["verbs"]


def test_decision_normalisation_matches_row():
    # row decision stored as "PARTIAL FAIL", incoming normalised token PARTIAL_FAIL
    defn = _defn(WorkflowReaction(decision="PARTIAL FAIL", verbs=["label:x"]))
    jira = RecordingJira()
    _apply("PARTIAL_FAIL", defn, jira)
    assert jira.labeled == [{"key": "KAN-1", "labels": ["x"]}]
