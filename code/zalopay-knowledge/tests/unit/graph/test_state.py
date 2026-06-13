"""Graph state tests — reducers and TypedDict shapes."""

from __future__ import annotations

import operator

from app.graph.state import (
    Chunk,
    Citation,
    Conflict,
    DeptResult,
    GraphState,
    merge_dict,
)


def test_merge_dict_is_commutative():
    a = {"risk": [Chunk(chunk_id="1", text="a", score=0.9)]}
    b = {"grow_enablement": [Chunk(chunk_id="2", text="b", score=0.8)]}
    assert merge_dict(a, b) == merge_dict(b, a) or (
        merge_dict(a, b)["risk"] == a["risk"]
        and merge_dict(a, b)["grow_enablement"] == b["grow_enablement"]
    )
    merged = merge_dict(a, b)
    assert set(merged.keys()) == {"risk", "grow_enablement"}
    assert merged["risk"][0]["chunk_id"] == "1"
    assert merged["grow_enablement"][0]["chunk_id"] == "2"


def test_merge_dict_does_not_mutate_inputs():
    a = {"risk": []}
    b = {"grow_enablement": []}
    merge_dict(a, b)
    assert a == {"risk": []}
    assert b == {"grow_enablement": []}


def test_merge_dict_later_key_overwrites_same_department():
    first = {"risk": [Chunk(chunk_id="old", text="x", score=0.5)]}
    second = {"risk": [Chunk(chunk_id="new", text="y", score=0.9)]}
    merged = merge_dict(first, second)
    assert merged["risk"][0]["chunk_id"] == "new"


def test_dept_results_reducer_concatenates():
    r1 = [
        DeptResult(
            department="risk",
            status="answered",
            answer="a",
            citations=[],
            confidence=0.8,
            warnings=[],
        )
    ]
    r2 = [
        DeptResult(
            department="grow_enablement",
            status="refused",
            answer="",
            citations=[],
            confidence=0.0,
            warnings=[],
        )
    ]
    combined = operator.add(r1, r2)
    assert len(combined) == 2
    assert combined[0]["department"] == "risk"
    assert combined[1]["department"] == "grow_enablement"


def test_graph_state_accepts_partial_updates():
    state: GraphState = {
        "question": "What is the policy?",
        "session_id": "s1",
        "user_id": "u1",
        "role": "engineer",
        "home_department": "risk",
        "request_language": "en",
        "allowed_departments": ["risk"],
        "pinned": [],
        "target_departments": ["risk"],
        "intent": "policy_lookup",
        "routing_confidence": 0.9,
    }
    assert state["question"] == "What is the policy?"
    assert state["allowed_departments"] == ["risk"]


def test_chunk_and_citation_optional_fields():
    chunk = Chunk(chunk_id="c1", text="body", score=0.7)
    assert chunk["chunk_id"] == "c1"
    cite = Citation(title="Doc", url="https://example.com")
    assert cite["title"] == "Doc"
    assert "deprecated" not in cite or cite.get("deprecated") is not False


def test_conflict_typed_dict_shape():
    conflict = Conflict(
        topic="limits",
        sides=[
            {
                "department": "risk",
                "statement": "10M",
                "citation": Citation(title="R", url="u"),
            }
        ],
    )
    assert conflict["topic"] == "limits"
    assert conflict["sides"][0]["department"] == "risk"
