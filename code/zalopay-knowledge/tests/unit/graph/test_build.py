"""Graph build tests — topology compiles and routes correctly."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.adapters.sqlite_checkpointer import SqliteCheckpointer

from app.graph.build import (
    DEPT_SUBGRAPH,
    GraphDeps,
    _branch_deadline,
    _make_route_after_router,
    _route_after_ingest,
    build_dept_subgraph,
    build_graph,
)
from langgraph.graph import END, START

try:
    from langgraph.types import Send
except ImportError:
    from langgraph.constants import Send  # type: ignore

from tests.unit.graph.conftest import StubLLM, StubRetriever


def test_dept_subgraph_compiles(graph_deps: GraphDeps):
    compiled = build_dept_subgraph(graph_deps)
    assert compiled is not None
    assert hasattr(compiled, "invoke")


def test_full_graph_compiles(graph_deps: GraphDeps):
    compiled = build_graph(graph_deps)
    assert compiled is not None
    assert hasattr(compiled, "invoke")


def test_full_graph_has_expected_nodes(graph_deps: GraphDeps):
    compiled = build_graph(graph_deps)
    nodes = set(compiled.get_graph().nodes)
    expected = {"ingest_context", "router", DEPT_SUBGRAPH, "reconcile", "respond"}
    assert expected.issubset(nodes)


def test_dept_subgraph_topology(graph_deps: GraphDeps):
    g = build_dept_subgraph(graph_deps).get_graph()
    nodes = set(g.nodes)
    assert {"retrieve", "grade", "synthesize", "verify"}.issubset(nodes)
    assert g.edges  # non-empty edge set


def test_route_after_ingest_to_router():
    assert _route_after_ingest({"status": "answered"}) == "router"
    assert _route_after_ingest({}) == "router"


def test_route_after_ingest_to_respond_on_refusal():
    assert _route_after_ingest({"status": "refused", "answer": "nope"}) == "respond"


def test_route_after_router_clarify_goes_to_respond(test_settings):
    route = _make_route_after_router(test_settings)
    assert route({"target_departments": [], "clarify_question": {"prompt": "?"}}) == "respond"


def test_route_after_router_fans_out_with_send(test_settings):
    route = _make_route_after_router(test_settings)
    graph_deadline = time.time() + 60
    result = route(
        {
            "target_departments": ["risk", "grow_enablement"],
            "question": "q",
            "role": "engineer",
            "home_department": "risk",
            "request_language": "en",
            "deadline_ts": graph_deadline,
        }
    )
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(s, Send) for s in result)
    payloads = [s.arg for s in result]
    assert {p["department"] for p in payloads} == {"risk", "grow_enablement"}
    assert all(p["question"] == "q" for p in payloads)
    assert all(p["role"] == "engineer" for p in payloads)
    assert all(p["home_department"] == "risk" for p in payloads)
    # Per-branch deadline is min(graph budget, now + branch_timeout_s).
    expected_branch_deadline = min(
        graph_deadline, time.time() + test_settings.branch_timeout_s
    )
    assert all(
        p["deadline_ts"] == pytest.approx(expected_branch_deadline, abs=1.0)
        for p in payloads
    )


def test_branch_deadline_caps_at_tighter_graph_budget():
    graph_deadline = time.time() + 5.0
    result = _branch_deadline(graph_deadline, 20.0)
    assert result == pytest.approx(graph_deadline, abs=0.1)


def test_branch_deadline_uses_branch_timeout_without_graph_cap():
    before = time.time()
    result = _branch_deadline(None, 20.0)
    assert result == pytest.approx(before + 20.0, abs=1.0)


def test_graph_invoke_end_to_end_greeting(graph_deps: GraphDeps):
    """Smoke test: greeting short-circuits without retrieval."""
    graph_deps.retriever = StubRetriever(ready=True)
    graph_deps.llm = StubLLM(
        '{"intent": "greeting", "target_departments": [], "confidence": 0.99}'
    )
    app = build_graph(graph_deps)
    result = app.invoke(
        {
            "question": "hello",
            "user_id": "u1",
            "session_id": "s1",
            "role": "engineer",
            "home_department": "risk",
            "pinned": [],
        }
    )
    assert result.get("status") == "answered"
    assert "feedback_id" in result
    assert result.get("intent") == "greeting"


def test_graph_stm_accumulates_messages_across_turns(
    graph_deps: GraphDeps, tmp_path: Path
):
    """FR-1.3: checkpointer persists conversation for follow-up routing."""
    graph_deps.retriever = StubRetriever(ready=True)
    graph_deps.checkpointer = SqliteCheckpointer(tmp_path / "checkpoints.db")

    greeting_payload = (
        '{"intent": "greeting", "target_departments": [], "confidence": 0.99}'
    )
    follow_up_payload = (
        '{"intent": "policy_lookup", "target_departments": ["risk"], "confidence": 0.9}'
    )
    llm = StubLLM(greeting_payload)
    graph_deps.llm = llm
    app = build_graph(graph_deps)
    config = {"configurable": {"thread_id": "stm-session-1"}}

    app.invoke(
        {
            "question": "hello",
            "user_id": "u1",
            "session_id": "stm-session-1",
            "role": "engineer",
            "home_department": "risk",
            "pinned": [],
            "messages": [HumanMessage(content="hello")],
        },
        config,
    )

    llm._text = follow_up_payload
    result = app.invoke(
        {
            "question": "And what's the SLA for that?",
            "user_id": "u1",
            "session_id": "stm-session-1",
            "role": "engineer",
            "home_department": "risk",
            "pinned": [],
            "messages": [HumanMessage(content="And what's the SLA for that?")],
        },
        config,
    )

    history = result.get("conversation_history") or ""
    assert "hello" in history.lower() or "zalopay" in history.lower()
    assert "SLA" not in history
    assert "Follow-up question" in (result.get("retrieval_query") or "")

    messages = result.get("messages") or []
    assert len(messages) >= 3
    assert isinstance(messages[0], HumanMessage)
    assert isinstance(messages[-1], (HumanMessage, AIMessage))


def test_dept_subgraph_refuses_when_branch_budget_exceeded(
    graph_deps: GraphDeps, sample_retrieved_chunk, past_deadline: float
):
    """FR-3.1: expired per-branch deadline skips retrieval and refuses cleanly."""
    graph_deps.retriever = StubRetriever(chunks=[sample_retrieved_chunk])
    graph_deps.llm = StubLLM('{"scores": [{"id": 0, "score": 0.9}]}')
    subgraph = build_dept_subgraph(graph_deps)
    result = subgraph.invoke(
        {
            "department": "risk",
            "question": "What is the SLA?",
            "role": "engineer",
            "request_language": "en",
            "deadline_ts": past_deadline,
        }
    )
    assert graph_deps.retriever.search_calls == []
    assert result["dept_results"][0]["status"] == "refused"
    assert result["dept_results"][0]["citations"] == []
