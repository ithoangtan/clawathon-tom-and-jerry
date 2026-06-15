"""Unit tests for the workflow executor node (Phase 5) edge paths."""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.graph.nodes.workflow_executor import make_execute_workflow_node
from app.ports.errors import JiraUnavailable
from app.ports.types import LLMResult

SETTINGS = Settings(_env_file=None)


class _LLM:
    def complete(self, **kwargs: Any) -> LLMResult:
        return LLMResult(text="{}", raw={}, usage={})


class _Retriever:
    def get_page_chunks(self, **kwargs: Any):
        return []

    def search(self, **kwargs: Any):
        return []


class _Jira:
    def get_issue(self, key: str) -> dict:
        raise JiraUnavailable()

    def create_issue(self, **kwargs: Any) -> dict:
        raise JiraUnavailable()

    def add_comment(self, **kwargs: Any) -> dict:
        raise JiraUnavailable()

    def is_ready(self) -> bool:
        return False


def test_no_workflow_found_is_graceful():
    node = make_execute_workflow_node(_LLM(), _Retriever(), _Jira(), settings=SETTINGS)
    out = node({"workflow_page_id": None, "workflow_discovery_note": "nothing matched", "request_language": "en"})
    assert out["status"] == "refused"
    assert out["answer"] == "nothing matched"
    assert out["citations"] == []


def test_empty_page_is_graceful():
    node = make_execute_workflow_node(_LLM(), _Retriever(), _Jira(), settings=SETTINGS)
    out = node({"workflow_page_id": "111", "request_language": "en"})
    # get_page_chunks returns [] → empty page reply, never raises
    assert out["status"] == "refused"
    assert out["answer"]
