"""Integration tests for FR-7.2 department access control (S-C1)."""

from __future__ import annotations

import json

from app.api.schemas import ChatResponse
from app.api.service import state_to_response
from app.config import Settings
from app.graph.build import GraphDeps, build_graph

from tests.unit.graph.conftest import StubLLM, StubRetriever
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def _business_settings() -> Settings:
    return Settings(
        grade_threshold=0.5,
        route_confidence_min=0.55,
        branch_timeout_s=20.0,
        role_dept_access_json=json.dumps(
            {"business": [GROW, BANK]}
        ),
        _env_file=None,
    )


def test_graph_pinned_risk_denied_for_business_role():
    """Pinned department outside allowlist → polite refusal, zero citations."""
    deps = GraphDeps(
        llm=StubLLM(),
        retriever=StubRetriever(ready=True),
        settings=_business_settings(),
    )
    result = build_graph(deps).invoke(
        {
            "question": "What is the fraud escalation threshold?",
            "user_id": "u1",
            "session_id": "s1",
            "role": "business",
            "home_department": GROW,
            "pinned": [RISK],
        }
    )
    assert result["status"] == "refused"
    assert "access_denied" in result.get("errors", [])
    assert result.get("citations", []) == []
    assert result.get("source_departments", []) == []
    assert "permission" in (result.get("answer") or "").lower()


def test_graph_router_denied_department_without_pin():
    """Auto-routed to a denied department → access refusal, no retrieval."""
    llm_payload = json.dumps(
        {
            "intent": "policy_lookup",
            "target_departments": [RISK],
            "confidence": 0.92,
        }
    )
    deps = GraphDeps(
        llm=StubLLM(llm_payload),
        retriever=StubRetriever(ready=True),
        settings=_business_settings(),
    )
    result = build_graph(deps).invoke(
        {
            "question": "What is the fraud escalation threshold?",
            "user_id": "u1",
            "session_id": "s1",
            "role": "business",
            "home_department": GROW,
            "pinned": [],
        }
    )
    assert result["status"] == "refused"
    assert "access_denied" in result.get("errors", [])
    assert deps.retriever.search_calls == []
    response = state_to_response(result)
    assert response.refusal_reason == "access_denied"
    assert response.status == "refused"
    assert response.citations == []


def test_api_response_maps_access_denied_refusal_reason():
    response = state_to_response(
        {
            "status": "refused",
            "answer": "You do not have permission to access this department's knowledge.",
            "errors": ["access_denied"],
            "citations": [],
            "source_departments": [],
            "confidence": 0.0,
            "feedback_id": "fb-test",
            "request_language": "en",
        }
    )
    assert isinstance(response, ChatResponse)
    assert response.refusal_reason == "access_denied"
