"""Helper tests — faithfulness pruning and citation filtering."""

from __future__ import annotations

from app.graph.nodes._helpers import (
    filter_citations_by_markers,
    prune_unsupported_claims,
)
from app.graph.state import Citation


def test_prune_unsupported_claims_drops_sentences():
    claims = [
        {"id": 0, "claim": "Supported fact [1].", "cited": [1]},
        {"id": 1, "claim": "Unsupported fact [2].", "cited": [2]},
    ]
    verdicts = {0: True, 1: False}
    pruned, markers, dropped = prune_unsupported_claims(
        "Supported fact [1]. Unsupported fact [2].",
        claims,
        verdicts,
    )
    assert pruned == "Supported fact [1]."
    assert markers == {1}
    assert len(dropped) == 1


def test_filter_citations_by_markers_never_cites_unused():
    citations = [
        Citation(title="A", url="https://a"),
        Citation(title="B", url="https://b"),
    ]
    filtered = filter_citations_by_markers(citations, {1})
    assert len(filtered) == 1
    assert filtered[0]["title"] == "A"
