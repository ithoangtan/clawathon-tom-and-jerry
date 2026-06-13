"""Router node tests — department routing, pins, filters, canned intents."""

from __future__ import annotations

import json

import pytest

from app.config import Settings
from app.graph.nodes.router import make_router_node
from app.ports.errors import LLMUnavailable

from tests.unit.graph.conftest import StubLLM


def test_router_out_of_scope_status_or_data(test_settings: Settings):
    payload = json.dumps(
        {"intent": "status_or_data", "target_departments": [], "confidence": 0.95}
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "What is today's transaction volume?",
            "allowed_departments": ["risk"],
            "request_language": "en",
        }
    )
    assert out["intent"] == "status_or_data"
    assert out["target_departments"] == []


def test_respond_out_of_scope_refusal(test_settings: Settings):
    from app.graph.nodes.respond import make_respond_node

    respond = make_respond_node(settings=test_settings)
    out = respond(
        {
            "intent": "status_or_data",
            "request_language": "en",
            "dept_results": [],
        }
    )
    assert out["status"] == "refused"
    assert out["citations"] == []
    assert "outside indexed documentation" in out["answer"].lower()


def test_router_honours_pinned_departments(test_settings: Settings):
    node = make_router_node(StubLLM(), settings=test_settings)
    out = node(
        {
            "question": "test",
            "allowed_departments": ["risk", "grow_enablement"],
            "pinned": ["risk"],
            "request_language": "en",
        }
    )
    assert out["target_departments"] == ["risk"]
    assert out["intent"] == "pinned"
    assert out["routing_confidence"] == 1.0
    assert out["clarify_question"] is None


def test_router_filters_pinned_by_allowed_departments(test_settings: Settings):
    node = make_router_node(StubLLM(), settings=test_settings)
    out = node(
        {
            "question": "test",
            "allowed_departments": ["risk"],
            "pinned": ["risk", "bank_partnerships"],
            "request_language": "en",
        }
    )
    assert out["target_departments"] == ["risk"]


def test_router_short_circuit_greeting(test_settings: Settings):
    payload = json.dumps(
        {"intent": "greeting", "target_departments": ["risk"], "confidence": 0.99}
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "hello",
            "allowed_departments": ["risk"],
            "request_language": "en",
        }
    )
    assert out["target_departments"] == []
    assert out["intent"] == "greeting"
    assert out["clarify_question"] is None


@pytest.mark.parametrize("intent", ["capability_query", "action_request"])
def test_router_short_circuit_canned_intents(intent: str, test_settings: Settings):
    payload = json.dumps(
        {"intent": intent, "target_departments": ["risk"], "confidence": 0.9}
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "what can you do?",
            "allowed_departments": ["risk", "grow_enablement"],
            "request_language": "en",
        }
    )
    assert out["intent"] == intent
    assert out["target_departments"] == []


def test_router_filters_targets_by_allowed_departments(test_settings: Settings):
    payload = json.dumps(
        {
            "intent": "policy_lookup",
            "target_departments": ["risk", "bank_partnerships"],
            "confidence": 0.9,
        }
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "policy?",
            "allowed_departments": ["risk"],
            "request_language": "en",
        }
    )
    assert out["target_departments"] == ["risk"]


def test_router_filters_invalid_department_keys(test_settings: Settings):
    payload = json.dumps(
        {
            "intent": "policy_lookup",
            "target_departments": ["risk", "unknown_dept"],
            "confidence": 0.9,
        }
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "policy?",
            "allowed_departments": ["risk", "grow_enablement", "bank_partnerships"],
            "request_language": "en",
        }
    )
    assert out["target_departments"] == ["risk"]


def test_router_clarify_on_low_confidence(test_settings: Settings):
    payload = json.dumps(
        {
            "intent": "unclear",
            "target_departments": ["risk"],
            "confidence": 0.2,
        }
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "ambiguous",
            "allowed_departments": ["risk"],
            "request_language": "en",
        }
    )
    assert out["target_departments"] == []
    assert out["clarify_question"] is not None
    assert "prompt" in out["clarify_question"]
    assert "options" in out["clarify_question"]


def test_router_clarify_when_no_usable_targets(test_settings: Settings):
    payload = json.dumps(
        {"intent": "policy_lookup", "target_departments": [], "confidence": 0.9}
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "policy?",
            "allowed_departments": ["risk"],
            "request_language": "en",
        }
    )
    assert out["target_departments"] == []
    assert out["clarify_question"] is not None


def test_router_normal_fan_out(test_settings: Settings):
    payload = json.dumps(
        {
            "intent": "policy_lookup",
            "target_departments": ["risk", "grow_enablement"],
            "confidence": 0.85,
        }
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "What is the refund policy?",
            "allowed_departments": ["risk", "grow_enablement", "bank_partnerships"],
            "request_language": "en",
        }
    )
    assert out["target_departments"] == ["risk", "grow_enablement"]
    assert out["routing_confidence"] == pytest.approx(0.85)
    assert out["clarify_question"] is None


def test_router_fallback_on_llm_unavailable(test_settings: Settings):
    node = make_router_node(
        StubLLM(side_effect=LLMUnavailable("down")),
        settings=test_settings,
    )
    out = node(
        {
            "question": "test",
            "allowed_departments": ["risk", "grow_enablement"],
            "request_language": "en",
        }
    )
    assert set(out["target_departments"]) == {"risk", "grow_enablement"}
    assert out["routing_confidence"] == 0.0
    assert "router_unavailable" in out.get("errors", [])


def test_router_access_denied_when_only_denied_targets(test_settings: Settings):
    payload = json.dumps(
        {
            "intent": "policy_lookup",
            "target_departments": ["risk"],
            "confidence": 0.9,
        }
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "What is the fraud threshold?",
            "allowed_departments": ["grow_enablement", "bank_partnerships"],
            "request_language": "en",
        }
    )
    assert out["target_departments"] == []
    assert out["status"] == "refused"
    assert "access_denied" in out.get("errors", [])
    assert "permission" in out["answer"].lower()


def test_router_clarify_options_respect_allowed_departments(test_settings: Settings):
    payload = json.dumps(
        {"intent": "unclear", "target_departments": [], "confidence": 0.2}
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "ambiguous",
            "allowed_departments": ["grow_enablement"],
            "request_language": "en",
        }
    )
    assert out["clarify_question"]["options"] == ["grow_enablement"]


def test_router_fallback_on_budget_exceeded(test_settings: Settings, past_deadline: float):
    node = make_router_node(StubLLM(), settings=test_settings)
    out = node(
        {
            "question": "test",
            "allowed_departments": ["risk"],
            "request_language": "en",
            "deadline_ts": past_deadline,
        }
    )
    assert out["target_departments"] == ["risk"]
    assert "budget_exceeded" in out.get("errors", [])


def test_router_clarify_prompt_vietnamese(test_settings: Settings):
    payload = json.dumps(
        {"intent": "unclear", "target_departments": [], "confidence": 0.2}
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "mơ hồ",
            "allowed_departments": ["risk"],
            "request_language": "vi",
        }
    )
    assert out["clarify_question"] is not None
    assert "bộ phận" in out["clarify_question"]["prompt"].lower()


def test_router_passes_conversation_history_to_llm(test_settings: Settings):
    payload = json.dumps(
        {
            "intent": "policy_lookup",
            "target_departments": ["risk"],
            "confidence": 0.9,
        }
    )
    llm = StubLLM(payload)
    node = make_router_node(llm, settings=test_settings)
    node(
        {
            "question": "And the SLA?",
            "allowed_departments": ["risk"],
            "request_language": "en",
            "conversation_history": "User: What is escalation?\nAssistant: Level 1 first.",
        }
    )
    assert llm.calls
    user_content = llm.calls[0]["messages"][1]["content"]
    assert "What is escalation?" in user_content
    assert "And the SLA?" in user_content


def test_router_never_returns_answer_text(test_settings: Settings):
    """Router output keys are routing-only — synthesis happens in dept subgraph."""
    payload = json.dumps(
        {
            "intent": "greeting",
            "target_departments": [],
            "confidence": 0.99,
        }
    )
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node(
        {
            "question": "hello",
            "allowed_departments": ["risk"],
            "request_language": "en",
        }
    )
    assert "answer" not in out
    assert set(out.keys()) <= {
        "intent",
        "target_departments",
        "routing_confidence",
        "clarify_question",
        "errors",
    }
