from __future__ import annotations

"""Platform tests for department subgraph graceful degradation."""

from unittest.mock import patch

from app.graph.build import _make_dept_branch, build_dept_subgraph

from tests.unit.graph.conftest import GraphDeps, StubLLM, StubRetriever
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


def test_dept_branch_degrades_to_timeout_on_subgraph_failure(graph_deps: GraphDeps):
    """One failed branch must not kill the parent graph — reconcile gets a timeout row."""
    graph_deps.retriever = StubRetriever(ready=True)
    graph_deps.llm = StubLLM('{"scores": [{"id": 0, "score": 0.9}]}')
    subgraph = build_dept_subgraph(graph_deps)
    branch = _make_dept_branch(subgraph)

    with (
        patch.object(subgraph, "stream", side_effect=RuntimeError("simulated branch crash")),
        patch("app.graph.build.get_stream_writer", return_value=lambda _payload: None),
    ):
        result = branch(
            {
                "department": RISK,
                "question": "What is the SLA?",
                "retrieval_query": "What is the SLA?",
                "role": "engineer",
                "request_language": "en",
                "deadline_ts": 9_999_999_999.0,
            }
        )

    assert len(result["dept_results"]) == 1
    row = result["dept_results"][0]
    assert row["department"] == RISK
    assert row["status"] == "timeout"
    assert row["citations"] == []
    assert "branch_error" in row["warnings"]
