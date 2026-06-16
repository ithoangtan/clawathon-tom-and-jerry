"""Router node tests — greeting fast-path, fan-out-to-all, pins, canned intents.

Behaviour: no department clarification anymore. Knowledge questions fan out to
ALL accessible departments; greetings/small-talk short-circuit to a friendly
reply (deterministic fast-path, no LLM); only short-circuit/workflow/pinned
intents bypass the fan-out.
"""

from __future__ import annotations

import json

import pytest

from app.config import Settings
from app.graph.nodes.router import make_router_node
from app.ports.errors import LLMUnavailable

from tests.unit.graph.conftest import StubLLM
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, BANK, GROW, RISK  # noqa: F401


# ── Greeting / small-talk ─────────────────────────────────────────────────────

def test_router_short_circuit_greeting(test_settings: Settings):
    payload = json.dumps({"intent": "greeting", "target_departments": [RISK], "confidence": 0.99})
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node({"question": "hello", "allowed_departments": [RISK], "request_language": "en"})
    assert out["intent"] == "greeting"
    assert out["target_departments"] == []
    assert out["clarify_question"] is None


def test_router_greeting_fast_path_vietnamese_skips_llm(test_settings: Settings):
    # Even though the LLM would say policy_lookup, the deterministic greeting
    # fast-path short-circuits "Có ai ở đó không?" without calling the LLM.
    llm = StubLLM(json.dumps({"intent": "policy_lookup", "target_departments": [RISK], "confidence": 0.9}))
    node = make_router_node(llm, settings=test_settings)
    out = node({"question": "Có ai ở đó không?", "allowed_departments": [RISK], "request_language": "vi"})
    assert out["intent"] == "greeting"
    assert out["target_departments"] == []
    assert out["clarify_question"] is None
    assert llm.calls == []  # LLM never invoked for an obvious greeting


@pytest.mark.parametrize("intent", ["capability_query", "action_request"])
def test_router_short_circuit_canned_intents(intent: str, test_settings: Settings):
    payload = json.dumps({"intent": intent, "target_departments": [RISK], "confidence": 0.9})
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node({"question": "what can you do?", "allowed_departments": [RISK, GROW], "request_language": "en"})
    assert out["intent"] == intent
    assert out["target_departments"] == []


# ── Knowledge questions: always fan out to ALL accessible departments ─────────

def test_router_knowledge_fans_out_to_all_allowed(test_settings: Settings):
    # LLM picks only [RISK, GROW] but the router fans out to ALL allowed depts.
    payload = json.dumps({"intent": "policy_lookup", "target_departments": [RISK, GROW], "confidence": 0.85})
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node({"question": "What is the refund policy?", "allowed_departments": ALL_DEPARTMENT_KEYS, "request_language": "en"})
    assert set(out["target_departments"]) == set(ALL_DEPARTMENT_KEYS)
    assert out["routing_confidence"] == pytest.approx(0.85)
    assert out["clarify_question"] is None


def test_router_low_confidence_fans_out_no_clarify(test_settings: Settings):
    payload = json.dumps({"intent": "unclear", "target_departments": [RISK], "confidence": 0.2})
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node({"question": "some ambiguous question", "allowed_departments": [RISK], "request_language": "en"})
    assert out["target_departments"] == [RISK]
    assert out["clarify_question"] is None


def test_router_no_llm_targets_still_fans_out(test_settings: Settings):
    payload = json.dumps({"intent": "policy_lookup", "target_departments": [], "confidence": 0.9})
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node({"question": "a policy question", "allowed_departments": [RISK], "request_language": "en"})
    assert out["target_departments"] == [RISK]
    assert out["clarify_question"] is None


def test_router_ignores_llm_dept_picks_fans_to_allowed(test_settings: Settings):
    # LLM picks are advisory only — fan-out is driven by the role's allowed set.
    payload = json.dumps({"intent": "policy_lookup", "target_departments": ["risk", "unknown_dept"], "confidence": 0.9})
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node({"question": "a policy question", "allowed_departments": ALL_DEPARTMENT_KEYS, "request_language": "en"})
    assert set(out["target_departments"]) == set(ALL_DEPARTMENT_KEYS)


def test_router_fans_out_only_within_allowed(test_settings: Settings):
    payload = json.dumps({"intent": "unclear", "target_departments": [], "confidence": 0.2})
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node({"question": "some ambiguous question", "allowed_departments": [GROW], "request_language": "en"})
    assert out["target_departments"] == [GROW]
    assert out["clarify_question"] is None


def test_router_vietnamese_knowledge_fans_out(test_settings: Settings):
    payload = json.dumps({"intent": "unclear", "target_departments": [], "confidence": 0.2})
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node({"question": "câu hỏi về chính sách hoàn tiền", "allowed_departments": [RISK], "request_language": "vi"})
    assert out["target_departments"] == [RISK]
    assert out["clarify_question"] is None


def test_router_out_of_scope_fans_out_no_short_circuit(test_settings: Settings):
    # Out-of-scope intents now fan out too — the grounded pipeline refuses only
    # if nothing relevant exists (no premature "not in docs").
    payload = json.dumps({"intent": "status_or_data", "target_departments": [], "confidence": 0.95})
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node({"question": "What is today's transaction volume?", "allowed_departments": [RISK], "request_language": "en"})
    assert out["intent"] == "status_or_data"
    assert out["target_departments"] == [RISK]
    assert out["clarify_question"] is None


# ── Pinned departments still honoured ─────────────────────────────────────────

def test_router_honours_pinned_departments(test_settings: Settings):
    node = make_router_node(StubLLM(), settings=test_settings)
    out = node({"question": "test", "allowed_departments": [RISK, GROW], "pinned": [RISK], "request_language": "en"})
    assert out["target_departments"] == [RISK]
    assert out["intent"] == "pinned"
    assert out["routing_confidence"] == 1.0
    assert out["clarify_question"] is None


def test_router_filters_pinned_by_allowed_departments(test_settings: Settings):
    node = make_router_node(StubLLM(), settings=test_settings)
    out = node({"question": "test", "allowed_departments": [RISK], "pinned": [RISK, BANK], "request_language": "en"})
    assert out["target_departments"] == [RISK]


# ── Degradation paths ─────────────────────────────────────────────────────────

def test_router_fallback_on_llm_unavailable(test_settings: Settings):
    node = make_router_node(StubLLM(side_effect=LLMUnavailable("down")), settings=test_settings)
    out = node({"question": "a knowledge question", "allowed_departments": [RISK, GROW], "request_language": "en"})
    assert set(out["target_departments"]) == {RISK, GROW}
    assert out["routing_confidence"] == 0.0
    assert "router_unavailable" in out.get("errors", [])


def test_router_fallback_on_budget_exceeded(test_settings: Settings, past_deadline: float):
    node = make_router_node(StubLLM(), settings=test_settings)
    out = node({"question": "a knowledge question", "allowed_departments": [RISK], "request_language": "en", "deadline_ts": past_deadline})
    assert out["target_departments"] == [RISK]
    assert "budget_exceeded" in out.get("errors", [])


def test_router_passes_conversation_history_to_llm(test_settings: Settings):
    payload = json.dumps({"intent": "policy_lookup", "target_departments": [RISK], "confidence": 0.9})
    llm = StubLLM(payload)
    node = make_router_node(llm, settings=test_settings)
    node({
        "question": "And the SLA?",
        "allowed_departments": [RISK],
        "request_language": "en",
        "conversation_history": "User: What is escalation?\nAssistant: Level 1 first.",
    })
    assert llm.calls
    user_content = llm.calls[0]["messages"][1]["content"]
    assert "What is escalation?" in user_content
    assert "And the SLA?" in user_content


def test_router_never_returns_answer_text(test_settings: Settings):
    """Router output keys are routing-only — synthesis happens in dept subgraph."""
    payload = json.dumps({"intent": "greeting", "target_departments": [], "confidence": 0.99})
    node = make_router_node(StubLLM(payload), settings=test_settings)
    out = node({"question": "hello", "allowed_departments": [RISK], "request_language": "en"})
    assert "answer" not in out
    assert set(out.keys()) <= {
        "intent",
        "target_departments",
        "routing_confidence",
        "clarify_question",
        "errors",
    }
