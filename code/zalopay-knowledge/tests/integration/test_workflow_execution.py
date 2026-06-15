"""Phase 5 integration — drive the full graph through the workflow path.

Mocks the LLM (routing → workflow_execution, discovery extraction, page parse,
per-step calls), the retriever (discovery search + ``get_page_chunks`` + rag
search), and Jira, then asserts a step-by-step cited answer and the Jira action.
"""

from __future__ import annotations

import json
import time
from typing import Any

from app.config import Settings
from app.graph.build import GraphDeps, build_graph
from app.ports.types import LLMResult, RetrievedChunk

SETTINGS = Settings(_env_file=None)

# ── Canned parse result: an ACTIVE workflow with fetch / rag / action steps ────
_PARSED = {
    "name": "Risk: Campaign Review — Lucky Wheel",
    "owner": "Risk Team",
    "definition_status": "ACTIVE",
    "jira_source": "existing-ticket",
    "version": "3.1",
    "participants": ["Risk Reviewer"],
    "lifecycle": [],
    "executable_statuses": ["SUBMITTED"],
    "steps": [
        {
            "index": 1, "title": "Fetch ticket", "responsible_role": "Risk Reviewer",
            "responsible_department": "Risk", "type": "fetch",
            "input": "Jira key", "action": "Pull ticket", "output": "context",
            "checklist": [], "policy_ref": None, "condition": None,
        },
        {
            "index": 2, "title": "Check payment policy", "responsible_role": "Risk Reviewer",
            "responsible_department": "Risk", "type": "rag",
            "input": "summary", "action": "look up payment abuse policy", "output": "findings",
            "checklist": [], "policy_ref": "https://confluence/policy", "condition": None,
        },
        {
            "index": 3, "title": "Post assessment", "responsible_role": "Risk Reviewer",
            "responsible_department": "Risk", "type": "action",
            "input": None, "action": "post risk assessment comment", "output": "Jira comment",
            "checklist": [], "policy_ref": None, "condition": None,
        },
    ],
}


class RoutingLLM:
    """Content-aware LLM stub: returns the right canned payload per prompt."""

    def __init__(self, parsed: dict | None = None) -> None:
        self._parsed = parsed if parsed is not None else _PARSED
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> LLMResult:
        self.calls.append(kwargs)
        msgs = kwargs.get("messages", [])
        system = " ".join(m.get("content", "") for m in msgs if m.get("role") == "system")
        user = " ".join(m.get("content", "") for m in msgs if m.get("role") == "user")
        blob = system + " " + user

        if "routing classifier" in system:
            return self._j({"intent": "workflow_execution", "target_departments": [], "confidence": 1.0})
        if "find the right workflow" in system:
            return self._j({
                "explicit_name": "Risk: Campaign Review — Lucky Wheel",
                "jira_key": "KAN-1",
                "search_query": "campaign risk review lucky wheel",
            })
        if "convert a Zalopay workflow" in system:
            return self._j(self._parsed)
        if "Evaluate each checklist item" in blob:
            return self._j([])
        if "Evaluate this branch condition" in blob:
            return self._j({"decision": "proceed", "rationale": "ok"})
        if "You are executing the step" in blob:
            return LLMResult(text="Synthesised step result.", raw={}, usage={})
        # suggest node and anything else
        return LLMResult(text="[]", raw={}, usage={})

    @staticmethod
    def _j(obj: Any) -> LLMResult:
        return LLMResult(text=json.dumps(obj), raw={}, usage={})


class WorkflowRetriever:
    """Retriever stub: discovery search, get_page_chunks, and rag search."""

    def __init__(self) -> None:
        self.search_calls: list[dict[str, Any]] = []
        self.page_calls: list[dict[str, Any]] = []

    def is_ready(self) -> bool:
        return True

    def search(self, **kwargs: Any) -> list[RetrievedChunk]:
        self.search_calls.append(kwargs)
        dept = kwargs.get("department")
        if dept == "workflow":
            return [_wf_chunk(0.92)]
        # rag domain lookup (risk)
        return [_policy_chunk()]

    def get_page_chunks(self, **kwargs: Any) -> list[RetrievedChunk]:
        self.page_calls.append(kwargs)
        return [_wf_chunk(1.0, text="# Risk: Campaign Review — Lucky Wheel\n... full page ...")]


class RecordingJira:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self.comments: list[dict] = []
        self.created: list[dict] = []

    def get_issue(self, key: str) -> dict:
        return {"key": key, "url": f"https://jira/browse/{key}", "summary": "Lucky Wheel campaign", "status": "SUBMITTED"}

    def add_comment(self, *, key: str, body: str) -> dict:
        self.comments.append({"key": key, "body": body})
        return {"key": key, "url": f"https://jira/browse/{key}", "dry_run": self.dry_run}

    def create_issue(self, **kwargs: Any) -> dict:
        self.created.append(kwargs)
        return {"key": "KAN-99", "url": "https://jira/browse/KAN-99", "dry_run": self.dry_run}

    def add_labels(self, *, key: str, labels: list) -> dict:
        self.labelled = {"key": key, "labels": labels}
        return {"key": key, "labels": labels, "dry_run": self.dry_run}

    def is_ready(self) -> bool:
        return True


def _wf_chunk(score: float, text: str = "workflow chunk") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"wf-{score}", department="workflow", doc_type="Operation",
        title="Risk: Campaign Review — Lucky Wheel", url="https://confluence/111",
        section=None, last_modified=None, lifecycle_state="active",
        source_type="confluence", page=None, text=text, score=score, source="111",
        labels=json.dumps(["zalopay-workflow", "status-active"]),
    )


def _policy_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="pol-1", department="risk", doc_type="policy",
        title="Payment Method Abuse Policy", url="https://confluence/policy",
        section="VietQR", last_modified=None, lifecycle_state="active",
        source_type="confluence", page=None,
        text="VietQR must be blocked for starter accounts.", score=0.8, source="policy",
    )


def _deps(llm: RoutingLLM, retriever: WorkflowRetriever, jira: RecordingJira) -> GraphDeps:
    return GraphDeps(llm=llm, retriever=retriever, settings=SETTINGS, jira=jira)


def _invoke(deps: GraphDeps, question: str) -> dict:
    app = build_graph(deps)
    state = {
        "question": question,
        "role": "risk",
        "request_language": "vi",
        "deadline_ts": time.time() + 3600.0,
        "messages": [],
    }
    return app.invoke(state, config={"configurable": {"thread_id": "t1", "actor_id": "u1"}})


def test_workflow_execution_end_to_end_posts_jira_comment():
    llm, retr, jira = RoutingLLM(), WorkflowRetriever(), RecordingJira()
    out = _invoke(_deps(llm, retr, jira), "Chạy workflow Campaign Risk Review cho ticket KAN-1")

    assert out["status"] == "answered"
    answer = out["answer"]
    # Step-by-step structure
    assert "Risk: Campaign Review — Lucky Wheel" in answer
    assert "## Step 1:" in answer and "## Step 2:" in answer and "## Step 3:" in answer
    # rag step produced a citation
    assert any(c.get("title") == "Payment Method Abuse Policy" for c in out["citations"])
    # action step posted a real Jira comment on the supplied ticket
    assert jira.comments and jira.comments[0]["key"] == "KAN-1"
    # discovery applied the ACTIVE label filter and loaded the page
    wf_search = [c for c in retr.search_calls if c.get("department") == "workflow"][0]
    assert wf_search["filters"] == {"labels": ["zalopay-workflow", "status-active"]}
    assert retr.page_calls[0]["page_id"] == "111"
    assert out["source_departments"] == ["workflow"]


def test_workflow_execution_dry_run_marks_action():
    llm, retr, jira = RoutingLLM(), WorkflowRetriever(), RecordingJira(dry_run=True)
    out = _invoke(_deps(llm, retr, jira), "Chạy workflow Campaign Risk Review cho ticket KAN-1")
    assert jira.comments  # still recorded
    assert "dry-run" in out["answer"].lower()


def test_deprecated_workflow_is_not_executed():
    parsed = {**_PARSED, "definition_status": "DEPRECATED"}
    llm, retr, jira = RoutingLLM(parsed=parsed), WorkflowRetriever(), RecordingJira()
    out = _invoke(_deps(llm, retr, jira), "Chạy workflow Campaign Risk Review cho ticket KAN-1")

    assert out["status"] == "refused"
    assert not jira.comments  # no Jira action on a deprecated workflow
    assert "DEPRECATED" in out["answer"]


def test_normal_question_still_uses_department_path():
    """A non-workflow question must NOT enter the workflow path."""

    class NormalLLM(RoutingLLM):
        def complete(self, **kwargs: Any) -> LLMResult:
            msgs = kwargs.get("messages", [])
            system = " ".join(m.get("content", "") for m in msgs if m.get("role") == "system")
            if "routing classifier" in system:
                return self._j({"intent": "policy_lookup", "target_departments": ["risk"], "confidence": 0.9})
            return super().complete(**kwargs)

    llm, retr, jira = NormalLLM(), WorkflowRetriever(), RecordingJira()
    out = _invoke(_deps(llm, retr, jira), "Chính sách hoàn tiền là gì?")
    # No workflow page load happened.
    assert retr.page_calls == []
    assert not jira.comments
    assert out.get("intent") == "policy_lookup"
