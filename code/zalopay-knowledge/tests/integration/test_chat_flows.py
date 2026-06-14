"""End-to-end graph flow tests — Product/UX round 1 (PM MUST 🟢).

Covers: answered path, direct dept pin, empty retrieval refusal, out-of-scope,
partial multi-dept, multi-dept reconcile with conflicts, API mapping, and HTTP wire.
"""

from __future__ import annotations

import json
import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.service import state_to_response
from app.config import Settings
from app.graph.build import GraphDeps, build_graph
from app.ports.types import LLMResult, RetrievedChunk
from tests.contract.test_chat_contract import AUTH_HEADERS
from tests.unit.graph.conftest import StubLLM, StubRetriever
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK

# Engineer role — full MVP department access (business role excludes Risk).
FLOW_AUTH_HEADERS = {
    **AUTH_HEADERS,
    "X-GreenNode-AgentBase-Role": "engineer",
    "X-GreenNode-AgentBase-Home-Department": RISK,
}


class QueueLLM:
    """Returns scripted LLM responses in call order (router → grade → synth → verify → reconcile)."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> LLMResult:
        self.calls.append(kwargs)
        text = self._responses.pop(0) if self._responses else "{}"
        return LLMResult(text=text, raw={}, usage={})


def _default_settings(**overrides: Any) -> Settings:
    base = {
        "grade_threshold": 0.5,
        "route_confidence_min": 0.55,
        "branch_timeout_s": 20.0,
        "hybrid_search_enabled": False,
        "reranker_enabled": False,
        "_env_file": None,
    }
    base.update(overrides)
    return Settings(**base)


def _risk_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c-risk-1",
        department=RISK,
        doc_type="Risk",
        title="Risk Alert Escalation Policy",
        url="https://confluence.example.com/risk/escalation",
        section="Level 1",
        last_modified="2024-11-15T09:30:00Z",
        lifecycle_state="active",
        source_type="confluence",
        page=None,
        text="Risk escalation requires manager approval within 24 hours for alerts.",
        score=0.9,
    )


def _graph_state(**kwargs: Any) -> dict[str, Any]:
    base = {
        "question": "What is the escalation process for risk alerts?",
        "user_id": "flow-user",
        "session_id": "flow-session",
        "role": "engineer",
        "home_department": RISK,
        "pinned": [],
        "deadline_ts": time.time() + 120,
    }
    base.update(kwargs)
    return base


def test_full_answered_flow_with_citations_and_disclaimer():
    """chat → router → retrieve → grade → synthesize → verify → reconcile → respond."""
    llm = QueueLLM(
        [
            json.dumps(
                {
                    "intent": "policy_lookup",
                    "target_departments": [RISK],
                    "confidence": 0.92,
                }
            ),
            json.dumps({"scores": [{"id": 0, "score": 0.92}]}),
            "Escalation requires manager approval within 24 hours [1].",
            json.dumps({"verdicts": [{"id": 0, "supported": True}]}),
        ]
    )
    deps = GraphDeps(
        llm=llm,
        retriever=StubRetriever(chunks=[_risk_chunk()], ready=True),
        settings=_default_settings(),
    )
    result = build_graph(deps).invoke(_graph_state())

    assert result["status"] == "answered"
    assert result["source_departments"] == [RISK]
    assert len(result["citations"]) == 1
    assert result["citations"][0]["title"] == "Risk Alert Escalation Policy"
    assert "[1]" in result["answer"]
    assert "Verify with" in result["answer"]
    assert result.get("feedback_id")
    assert deps.retriever.search_calls
    assert deps.retriever.search_calls[0]["department"] == RISK

    api = state_to_response(result)
    assert api.status == "answered"
    assert api.citations[0].last_modified == "2024-11-15T09:30:00Z"


def test_direct_department_pin_bypasses_router_llm():
    """Direct dept chat: pinned target skips router classification."""
    llm = QueueLLM(
        [
            json.dumps({"scores": [{"id": 0, "score": 0.9}]}),
            "Pinned path answer [1].",
            json.dumps({"verdicts": [{"id": 0, "supported": True}]}),
        ]
    )
    deps = GraphDeps(
        llm=llm,
        retriever=StubRetriever(chunks=[_risk_chunk()], ready=True),
        settings=_default_settings(),
    )
    result = build_graph(deps).invoke(_graph_state(pinned=[RISK]))

    assert result["intent"] == "pinned"
    assert result["status"] == "answered"
    assert result["source_departments"] == [RISK]
    assert len(llm.calls) == 3  # grade, synthesize, verify — no router LLM


def test_empty_retrieval_produces_refusal_with_escalation():
    """Empty retrieval → useful refusal with Teams escalation pointer."""
    llm = QueueLLM(
        [
            json.dumps(
                {
                    "intent": "policy_lookup",
                    "target_departments": [RISK],
                    "confidence": 0.9,
                }
            ),
        ]
    )
    deps = GraphDeps(
        llm=llm,
        retriever=StubRetriever(chunks=[], ready=True),
        settings=_default_settings(),
    )
    result = build_graph(deps).invoke(_graph_state(question="What is the moon landing date?"))

    assert result["status"] == "refused"
    assert result["citations"] == []
    assert "not covered in the docs" in result["answer"].lower()
    assert "Next step" in result["answer"] or "human" in result["answer"].lower() or "Risk" in result["answer"]


def test_out_of_scope_intent_refuses_without_retrieval():
    llm = QueueLLM(
        [
            json.dumps(
                {
                    "intent": "status_or_data",
                    "target_departments": [],
                    "confidence": 0.95,
                }
            ),
        ]
    )
    deps = GraphDeps(
        llm=llm,
        retriever=StubRetriever(chunks=[_risk_chunk()], ready=True),
        settings=_default_settings(),
    )
    result = build_graph(deps).invoke(
        _graph_state(question="What is today's transaction volume?")
    )

    assert result["status"] == "refused"
    assert result["intent"] == "status_or_data"
    assert result["citations"] == []
    assert "outside indexed documentation" in result["answer"].lower()
    assert deps.retriever.search_calls == []

    api = state_to_response(result)
    assert api.refusal_reason == "out_of_scope"


def test_partial_when_one_department_refuses():
    grow_chunk = RetrievedChunk(
        chunk_id="c-grow-1",
        department=GROW,
        doc_type="Operation",
        title="Merchant Onboarding",
        url="https://confluence.example.com/grow/onboard",
        section="Steps",
        last_modified="2024-10-01T00:00:00Z",
        lifecycle_state="active",
        source_type="confluence",
        page=None,
        text="Merchants complete KYC before activation.",
        score=0.88,
    )
    llm = QueueLLM(
        [
            json.dumps(
                {
                    "intent": "policy_lookup",
                    "target_departments": [RISK, GROW],
                    "confidence": 0.88,
                }
            ),
            json.dumps({"scores": [{"id": 0, "score": 0.9}]}),
            "Grow onboarding requires KYC [1].",
            json.dumps({"verdicts": [{"id": 0, "supported": True}]}),
        ]
    )

    class DeptAwareRetriever(StubRetriever):
        def search(self, **kwargs: Any) -> list[RetrievedChunk]:
            self.search_calls.append(kwargs)
            if kwargs.get("department") == GROW:
                return [grow_chunk]
            return []

    deps = GraphDeps(
        llm=llm,
        retriever=DeptAwareRetriever(ready=True),
        settings=_default_settings(),
    )
    result = build_graph(deps).invoke(_graph_state(question="How does merchant onboarding work?"))

    assert result["status"] == "partial"
    assert GROW in result["source_departments"]
    assert RISK in (result.get("refusals") or [])
    assert result["citations"]


def test_multi_department_reconcile_surfaces_conflicts():
    risk_chunk = _risk_chunk()
    bank_chunk = RetrievedChunk(
        chunk_id="c-bank-1",
        department=BANK,
        doc_type="Operation",
        title="Partner SLA",
        url="https://confluence.example.com/bank/sla",
        section="Level 2",
        last_modified="2024-09-01T00:00:00Z",
        lifecycle_state="active",
        source_type="confluence",
        page=None,
        text="Level 2 SLA is 8 business hours for partner incidents.",
        score=0.87,
    )

    class TwoDeptRetriever(StubRetriever):
        def search(self, **kwargs: Any) -> list[RetrievedChunk]:
            self.search_calls.append(kwargs)
            dept = kwargs.get("department")
            if dept == RISK:
                return [risk_chunk]
            if dept == BANK:
                return [bank_chunk]
            return []

    merge_payload = json.dumps(
        {
            "merged_answer": "Departments disagree on Level 2 SLA [1][2].",
            "conflicts": [
                {
                    "topic": "Level 2 SLA",
                    "sides": [
                        {
                            "department": RISK,
                            "statement": "4 hours",
                            "citation_index": 1,
                        },
                        {
                            "department": BANK,
                            "statement": "8 business hours",
                            "citation_index": 1,
                        },
                    ],
                }
            ],
        }
    )

    llm = QueueLLM(
        [
            json.dumps(
                {
                    "intent": "policy_lookup",
                    "target_departments": [RISK, BANK],
                    "confidence": 0.9,
                }
            ),
            json.dumps({"scores": [{"id": 0, "score": 0.9}]}),
            "Risk Level 2 is 4 hours [1].",
            json.dumps({"verdicts": [{"id": 0, "supported": True}]}),
            json.dumps({"scores": [{"id": 0, "score": 0.88}]}),
            "Bank Level 2 is 8 business hours [1].",
            json.dumps({"verdicts": [{"id": 0, "supported": True}]}),
            merge_payload,
        ]
    )
    deps = GraphDeps(
        llm=llm,
        retriever=TwoDeptRetriever(ready=True),
        settings=_default_settings(),
    )
    result = build_graph(deps).invoke(_graph_state(question="What is the Level 2 incident SLA?"))

    assert result["status"] == "partial"
    assert len(result.get("conflicts") or []) == 1
    assert result["conflicts"][0]["topic"] == "Level 2 SLA"
    assert len(result["citations"]) == 2
    assert set(result["source_departments"]) == {RISK, BANK}


@pytest.fixture()
def api_client() -> TestClient:
    return TestClient(create_app())


def _wire_graph(monkeypatch: pytest.MonkeyPatch, deps: GraphDeps):
    """Point POST /chat at a stubbed graph + ready retriever."""
    graph = build_graph(deps)
    mock_deps = MagicMock()
    mock_deps.retriever = deps.retriever
    monkeypatch.setattr("app.api.routes.get_deps", lambda: mock_deps)
    monkeypatch.setattr("app.api.service.get_compiled_graph", lambda: graph)
    from app.graph import get_compiled_graph

    get_compiled_graph.cache_clear()
    monkeypatch.setattr("app.graph.get_compiled_graph", lambda: graph)


def test_post_chat_http_answered_with_citations(api_client, monkeypatch):
    """HTTP POST /chat → graph → citations on the wire."""
    llm = QueueLLM(
        [
            json.dumps(
                {
                    "intent": "policy_lookup",
                    "target_departments": [RISK],
                    "confidence": 0.92,
                }
            ),
            json.dumps({"scores": [{"id": 0, "score": 0.92}]}),
            "Escalation requires manager approval within 24 hours [1].",
            json.dumps({"verdicts": [{"id": 0, "supported": True}]}),
        ]
    )
    deps = GraphDeps(
        llm=llm,
        retriever=StubRetriever(chunks=[_risk_chunk()], ready=True),
        settings=_default_settings(),
    )
    _wire_graph(monkeypatch, deps)

    resp = api_client.post(
        "/chat",
        json={"question": "What is the escalation process for risk alerts?"},
        headers=FLOW_AUTH_HEADERS,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "answered"
    assert body["source_departments"] == [RISK]
    assert len(body["citations"]) == 1
    assert body["citations"][0]["title"] == "Risk Alert Escalation Policy"
    assert "[1]" in body["answer"]
    assert body.get("feedback_id")


def test_post_chat_http_partial_includes_refusals(api_client, monkeypatch):
    """Partial ladder: wire exposes refusals for FE PartialGapBanner."""
    grow_chunk = RetrievedChunk(
        chunk_id="c-grow-1",
        department=GROW,
        doc_type="Operation",
        title="Merchant Onboarding",
        url="https://confluence.example.com/grow/onboard",
        section="Steps",
        last_modified="2024-10-01T00:00:00Z",
        lifecycle_state="active",
        source_type="confluence",
        page=None,
        text="Merchants complete KYC before activation.",
        score=0.88,
    )

    class DeptAwareRetriever(StubRetriever):
        def search(self, **kwargs: Any) -> list[RetrievedChunk]:
            self.search_calls.append(kwargs)
            if kwargs.get("department") == GROW:
                return [grow_chunk]
            return []

    llm = QueueLLM(
        [
            json.dumps(
                {
                    "intent": "policy_lookup",
                    "target_departments": [RISK, GROW],
                    "confidence": 0.88,
                }
            ),
            json.dumps({"scores": [{"id": 0, "score": 0.9}]}),
            "Grow onboarding requires KYC [1].",
            json.dumps({"verdicts": [{"id": 0, "supported": True}]}),
        ]
    )
    deps = GraphDeps(
        llm=llm,
        retriever=DeptAwareRetriever(ready=True),
        settings=_default_settings(),
    )
    _wire_graph(monkeypatch, deps)

    resp = api_client.post(
        "/chat",
        json={"question": "How does merchant onboarding work?"},
        headers=FLOW_AUTH_HEADERS,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "partial"
    assert body["refusals"] == [RISK]
    assert body["source_departments"] == [GROW]


def test_full_refusal_includes_escalation_on_api():
    """Empty retrieval refusal surfaces Teams escalation in API response."""
    llm = QueueLLM(
        [
            json.dumps(
                {
                    "intent": "policy_lookup",
                    "target_departments": [RISK],
                    "confidence": 0.9,
                }
            ),
        ]
    )
    deps = GraphDeps(
        llm=llm,
        retriever=StubRetriever(chunks=[], ready=True),
        settings=_default_settings(),
    )
    result = build_graph(deps).invoke(_graph_state(question="Unknown moon topic?"))

    api = state_to_response(result)
    assert api.status == "refused"
    assert api.refusal_reason is None
    assert "not covered" in api.answer.lower() or "Next step" in api.answer


@pytest.mark.parametrize("lang,needle", [("en", "Not covered"), ("vi", "Không có thông tin")])
def test_refusal_body_localized(lang: str, needle: str):
    llm = QueueLLM(
        [
            json.dumps(
                {
                    "intent": "policy_lookup",
                    "target_departments": [RISK],
                    "confidence": 0.9,
                }
            ),
        ]
    )
    deps = GraphDeps(
        llm=llm,
        retriever=StubRetriever(chunks=[], ready=True),
        settings=_default_settings(),
    )
    result = build_graph(deps).invoke(
        _graph_state(question="Unknown topic?", request_language=lang)
    )
    assert result["status"] == "refused"
    assert needle in result["answer"]
