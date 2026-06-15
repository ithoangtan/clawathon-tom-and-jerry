"""Unit tests for handle_jira_event (S2) — all ports mocked."""

from __future__ import annotations

import json
from typing import Any

from app.config import Settings
from app.integrations.jira_events import normalize_jira_event
from app.integrations.jira_handler import handle_jira_event
from app.ports.types import LLMResult, RetrievedChunk

SETTINGS = Settings(_env_file=None)

# Parsed workflow with a Triggers section (status APPROVED → update Confluence).
_PARSED = {
    "name": "Risk: Campaign Review — Lucky Wheel",
    "definition_status": "ACTIVE",
    "steps": [],
    "triggers": [
        {"event_type": "status_changed", "from_status": "*", "to_status": "APPROVED",
         "action": "Post tổng kết review lên Confluence page"},
        {"event_type": "comment_added", "comment_contains": "@agent recheck",
         "action": "Chạy lại kiểm tra policy"},
    ],
}


class StubLLM:
    def complete(self, **kwargs: Any) -> LLMResult:
        msgs = kwargs.get("messages", [])
        blob = " ".join(m.get("content", "") for m in msgs)
        if "convert a Zalopay workflow" in blob:
            return LLMResult(text=json.dumps(_PARSED), raw={}, usage={})
        return LLMResult(text="Tổng kết: campaign đạt yêu cầu rủi ro.", raw={}, usage={})


class StubRetriever:
    def get_page_chunks(self, **kwargs: Any) -> list[RetrievedChunk]:
        return [_chunk("# page text with triggers")]

    def search(self, **kwargs: Any) -> list[RetrievedChunk]:
        return [_chunk("VietQR policy", title="Payment Policy")]


def _chunk(text: str, title: str = "WF") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c1", department="workflow", doc_type="Operation", title=title,
        url="https://c/1", section=None, last_modified=None, lifecycle_state="active",
        source_type="confluence", page=None, text=text, score=1.0, source="1048659",
    )


class RecordingJira:
    def __init__(self, labels: list[str]) -> None:
        self._labels = labels
        self.comments: list[dict] = []

    def get_issue(self, key: str) -> dict:
        return {"key": key, "url": f"https://j/{key}", "summary": "Lucky Wheel",
                "status": "APPROVED", "fields": {"labels": self._labels}}

    def add_comment(self, *, key: str, body: str, code_block=None, code_language="json") -> dict:
        self.comments.append({"key": key, "body": body, "code_block": code_block, "code_language": code_language})
        return {"key": key, "url": f"https://j/{key}", "dry_run": False}

    def add_labels(self, **kw: Any) -> dict:
        return {"dry_run": False}

    def is_ready(self) -> bool:
        return True


class RecordingConfluence:
    def __init__(self) -> None:
        self.appends: list[dict] = []

    def append_to_page(self, *, page_id: str, html_fragment: str) -> dict:
        self.appends.append({"page_id": page_id, "html": html_fragment})
        return {"id": page_id, "version": 2}

    def create_page(self, **kw): ...
    def update_page(self, **kw): ...
    def add_labels(self, **kw): ...
    def is_ready(self) -> bool: return True


def _ev_status(to="APPROVED"):
    return normalize_jira_event({"event_type": "status_changed", "issue_key": "KAN-1",
                                 "status_from": "UNDER REVIEW", "status_to": to, "actor": "human"})


def _call(jira, cw):
    return handle_jira_event(
        _ev_status(), llm=StubLLM(), retriever=StubRetriever(), jira=jira,
        confluence_writer=cw, settings=SETTINGS,
    )


def test_acts_and_posts_comment_and_updates_confluence():
    jira = RecordingJira(labels=["wf-risk-campaign-review-lucky-wheel"])
    cw = RecordingConfluence()
    out = _call(jira, cw)
    assert out["status"] == "acted"
    assert out["workflow"] == "Risk: Campaign Review — Lucky Wheel"
    assert jira.comments and jira.comments[0]["key"] == "KAN-1"
    # action mentions "Confluence" → page appended
    assert out["confluence_updated"] is True
    assert cw.appends and cw.appends[0]["page_id"] == "1048659"


def test_no_workflow_label_ignored():
    out = _call(RecordingJira(labels=["something-else"]), RecordingConfluence())
    assert out["status"] == "ignored"
    assert out["reason"] == "no_workflow_label"


def test_testing_label_echoes_payload_as_json_codeblock():
    jira = RecordingJira(labels=["testing"])
    ev = normalize_jira_event({"event_type": "status_changed", "issue_key": "KAN-1",
                               "status_from": "TO DO", "status_to": "RISK REVIEW", "actor": "human"})
    out = handle_jira_event(ev, llm=StubLLM(), retriever=StubRetriever(), jira=jira,
                            confluence_writer=RecordingConfluence(), settings=SETTINGS)
    assert out["status"] == "acted" and out["mode"] == "testing"
    # one comment, with a JSON code block carrying the payload
    c = jira.comments[0]
    assert c["code_language"] == "json"
    import json as _json
    parsed = _json.loads(c["code_block"])
    assert parsed["issue_key"] == "KAN-1" and parsed["status_to"] == "RISK REVIEW"


def test_testing_label_takes_priority_over_workflow():
    # has BOTH testing and a wf- label → testing wins, no workflow parse/run
    jira = RecordingJira(labels=["testing", "wf-risk-campaign-review-lucky-wheel"])
    ev = normalize_jira_event({"event_type": "status_changed", "issue_key": "KAN-1",
                               "status_to": "APPROVED", "actor": "human"})
    out = handle_jira_event(ev, llm=StubLLM(), retriever=StubRetriever(), jira=jira,
                            confluence_writer=RecordingConfluence(), settings=SETTINGS)
    assert out["mode"] == "testing"


def test_no_trigger_matched():
    # status_to that no trigger matches (triggers only fire on APPROVED)
    jira = RecordingJira(labels=["wf-risk-campaign-review-lucky-wheel"])
    cw = RecordingConfluence()
    out = handle_jira_event(
        normalize_jira_event({"event_type": "status_changed", "issue_key": "KAN-1",
                              "status_to": "REJECTED", "actor": "human"}),
        llm=StubLLM(), retriever=StubRetriever(), jira=jira, confluence_writer=cw, settings=SETTINGS,
    )
    assert out["status"] == "no_trigger_matched"
    assert jira.comments == []


def test_comment_trigger_no_confluence_hint_skips_confluence():
    jira = RecordingJira(labels=["wf-risk-campaign-review-lucky-wheel"])
    cw = RecordingConfluence()
    out = handle_jira_event(
        normalize_jira_event({"event_type": "comment_added", "issue_key": "KAN-1",
                              "comment": "@agent recheck please", "actor": "human"}),
        llm=StubLLM(), retriever=StubRetriever(), jira=jira, confluence_writer=cw, settings=SETTINGS,
    )
    assert out["status"] == "acted"
    assert jira.comments  # comment posted
    assert out["confluence_updated"] is False  # action text has no confluence hint
    assert cw.appends == []
