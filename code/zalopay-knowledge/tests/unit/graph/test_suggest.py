"""Suggest node tests — follow-up generation uses the SMALL tier + result.text.

Regression guard for the bug where ``suggest`` used a non-existent
``ModelTier.ROUTING`` and read ``result.content`` (other nodes use ``.text``),
which made follow-up suggestions silently fail.
"""

from __future__ import annotations

import json

from app.config import Settings
from app.graph.nodes.suggest import make_suggest_node
from app.ports.types import ModelTier

from tests.unit.graph.conftest import StubLLM


def test_suggest_uses_small_tier_and_text(test_settings: Settings):
    llm = StubLLM(json.dumps(["What about X?", "How does Y work?"]))
    node = make_suggest_node(llm, settings=test_settings)
    out = node(
        {
            "status": "answered",
            "answer": "A grounded answer [1].",
            "question": "original question",
            "request_language": "en",
            "citations": [],
        }
    )
    assert out["suggested_questions"] == ["What about X?", "How does Y work?"]
    assert llm.calls and llm.calls[0]["tier"] == ModelTier.SMALL


def test_suggest_skips_refused(test_settings: Settings):
    llm = StubLLM("[]")
    node = make_suggest_node(llm, settings=test_settings)
    out = node({"status": "refused", "answer": "", "question": "q", "request_language": "en"})
    assert out["suggested_questions"] == []
    assert llm.calls == []  # no LLM call when there is nothing to follow up on
