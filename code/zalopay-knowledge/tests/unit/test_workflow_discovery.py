"""Unit tests for the workflow discovery node (Phase 4)."""

from __future__ import annotations

import json
from typing import Any

from app.config import Settings
from app.graph.nodes.workflow_discovery import make_discover_workflow_node
from app.ports.errors import RetrieverUnavailable
from app.ports.types import LLMResult, RetrievedChunk

SETTINGS = Settings(_env_file=None)


class StubLLM:
    def __init__(self, payload: dict) -> None:
        self._text = json.dumps(payload)
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> LLMResult:
        self.calls.append(kwargs)
        return LLMResult(text=self._text, raw={}, usage={})


class StubRetriever:
    def __init__(self, chunks: list[RetrievedChunk], *, raises: Exception | None = None) -> None:
        self._chunks = chunks
        self._raises = raises
        self.search_calls: list[dict[str, Any]] = []

    def search(self, **kwargs: Any) -> list[RetrievedChunk]:
        self.search_calls.append(kwargs)
        if self._raises:
            raise self._raises
        return list(self._chunks)


def _chunk(page_id: str, title: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"{page_id}-{score}",
        department="workflow",
        doc_type="Operation",
        title=title,
        url=f"https://confluence/{page_id}",
        section=None,
        last_modified=None,
        lifecycle_state="active",
        source_type="confluence",
        page=None,
        text="step text",
        score=score,
        source=page_id,
        labels=json.dumps(["zalopay-workflow", "status-active"]),
    )


def _state(question: str) -> dict:
    return {"question": question, "request_language": "en", "deadline_ts": None}


def test_semantic_discovery_picks_best_page_and_groups_by_source():
    # Two pages, page "111" has multiple chunks (best 0.9); page "222" best 0.6.
    chunks = [
        _chunk("111", "Risk: Campaign Review — Lucky Wheel", 0.9),
        _chunk("111", "Risk: Campaign Review — Lucky Wheel", 0.7),
        _chunk("222", "Risk: Campaign Review — General", 0.6),
    ]
    llm = StubLLM({"explicit_name": None, "jira_key": None, "search_query": "campaign lucky wheel"})
    node = make_discover_workflow_node(StubRetriever(chunks), llm, settings=SETTINGS)

    out = node(_state("Review campaign Lucky Wheel mới"))

    assert out["workflow_page_id"] == "111"
    assert out["workflow_name"] == "Risk: Campaign Review — Lucky Wheel"
    # Grouped: 2 pages, not 3 chunks.
    assert [c["page_id"] for c in out["workflow_candidates"]] == ["111", "222"]
    assert out["workflow_discovery_note"] is None


def test_discovery_applies_active_label_filter():
    chunks = [_chunk("111", "WF", 0.9)]
    retr = StubRetriever(chunks)
    llm = StubLLM({"explicit_name": None, "jira_key": None, "search_query": "x"})
    node = make_discover_workflow_node(retr, llm, settings=SETTINGS)

    node(_state("run something"))

    call = retr.search_calls[0]
    assert call["department"] == "workflow"
    assert call["filters"] == {"labels": ["zalopay-workflow", "status-active"]}


def test_explicit_name_prefers_title_match_over_score():
    # "General" page has a higher raw score, but the user named "Lucky Wheel".
    chunks = [
        _chunk("999", "Risk: Campaign Review — General", 0.95),
        _chunk("111", "Risk: Campaign Review — Lucky Wheel", 0.6),
    ]
    llm = StubLLM(
        {
            "explicit_name": "Campaign Review — Lucky Wheel",
            "jira_key": "ZP-12345",
            "search_query": "campaign review lucky wheel",
        }
    )
    node = make_discover_workflow_node(StubRetriever(chunks), llm, settings=SETTINGS)

    out = node(_state("Chạy workflow Campaign Review — Lucky Wheel cho ticket ZP-12345"))

    assert out["workflow_page_id"] == "111"
    assert out["jira_parent_key"] == "ZP-12345"


def test_jira_key_is_uppercased():
    chunks = [_chunk("111", "WF", 0.9)]
    llm = StubLLM({"explicit_name": None, "jira_key": "zp-77", "search_query": "x"})
    node = make_discover_workflow_node(StubRetriever(chunks), llm, settings=SETTINGS)
    out = node(_state("run workflow for zp-77"))
    assert out["jira_parent_key"] == "ZP-77"


def test_no_match_below_threshold_yields_note():
    chunks = [_chunk("111", "WF", 0.1)]  # below _MIN_SCORE
    llm = StubLLM({"explicit_name": None, "jira_key": None, "search_query": "x"})
    node = make_discover_workflow_node(StubRetriever(chunks), llm, settings=SETTINGS)

    out = node(_state("something unrelated"))

    assert out["workflow_page_id"] is None
    assert out["workflow_candidates"] == []
    assert out["workflow_discovery_note"]


def test_retriever_unavailable_is_graceful():
    llm = StubLLM({"explicit_name": None, "jira_key": "KAN-1", "search_query": "x"})
    node = make_discover_workflow_node(
        StubRetriever([], raises=RetrieverUnavailable()), llm, settings=SETTINGS
    )
    out = node(_state("run workflow KAN-1"))
    assert out["workflow_page_id"] is None
    assert out["jira_parent_key"] == "KAN-1"
    assert out["workflow_discovery_note"]
