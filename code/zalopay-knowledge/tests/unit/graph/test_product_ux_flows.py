"""Product/UX graph integration tests — maps terminal state to API + PM flows."""

from __future__ import annotations

import json
import time

from app.api.service import state_to_response
from app.graph.build import GraphDeps, build_graph
from app.graph.nodes.respond import make_respond_node
from app.graph.nodes.router import make_router_node
from app.ports.types import LLMResult, RetrievedChunk
from tests.unit.graph.conftest import StubLLM, StubRetriever
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


class QueueLLM(StubLLM):
    """Returns scripted LLM responses in call order."""

    def __init__(self, responses: list[str]) -> None:
        super().__init__()
        self._responses = list(responses)

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        text = self._responses.pop(0) if self._responses else "{}"
        return LLMResult(text=text, raw={}, usage={})


def test_partial_multi_dept_exposes_refusals_on_api(test_settings):
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
        def search(self, **kwargs):
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
        settings=test_settings,
    )
    result = build_graph(deps).invoke(
        {
            "question": "How does merchant onboarding work?",
            "user_id": "ux-user",
            "session_id": "ux-session",
            "role": "engineer",
            "home_department": RISK,
            "pinned": [],
            "deadline_ts": time.time() + 120,
        }
    )

    api = state_to_response(result)
    assert api.status == "partial"
    assert api.refusals == [RISK]
    assert api.source_departments == [GROW]
    assert len(api.citations) == 1


def test_out_of_scope_short_circuit_includes_escalation(test_settings):
    deps = GraphDeps(
        llm=StubLLM(
            json.dumps(
                {
                    "intent": "status_or_data",
                    "target_departments": [],
                    "confidence": 0.95,
                }
            )
        ),
        retriever=StubRetriever(chunks=[], ready=True),
        settings=test_settings,
    )
    result = build_graph(deps).invoke(
        {
            "question": "What is today's transaction volume?",
            "user_id": "ux-user",
            "session_id": "ux-session",
            "role": "engineer",
            "home_department": RISK,
            "pinned": [],
            "deadline_ts": time.time() + 120,
        }
    )
    api = state_to_response(result)

    assert api.status == "refused"
    assert api.refusal_reason == "out_of_scope"
    assert "Risk Management" in api.answer
    assert "MVP scope" in api.answer
    assert api.citations == []
