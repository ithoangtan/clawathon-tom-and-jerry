from __future__ import annotations

"""``synthesize`` node — grounded answer generation (one per branch).

Third node of a department subgraph.  Uses the MAIN tier with
``synthesize.v1.yaml`` to write an answer grounded entirely in the graded
chunks, with inline ``[n]`` citation markers (1-indexed against
``graded_chunks``).  Produces ``draft_answer`` + ``draft_citations`` for the
``verify`` node to check.

If there are no graded chunks, it short-circuits to the
``CANNOT_ANSWER_FROM_SOURCES`` sentinel without an LLM call.
"""

import logging
from typing import Callable

from app.config import Settings, get_settings
from app.graph.nodes._helpers import (
    budget_exceeded,
    chunk_to_citation,
    render_chunks,
    role_style_for,
)
from app.graph.state import Chunk, Citation, DeptState
from app.ports.errors import LLMUnavailable
from app.ports.llm import LLMPort
from app.ports.types import ModelTier
from app.prompts import load_prompt

logger = logging.getLogger(__name__)

CANNOT_ANSWER = "CANNOT_ANSWER_FROM_SOURCES"


def make_synthesize_node(
    llm: LLMPort,
    *,
    settings: Settings | None = None,
) -> Callable[[DeptState], dict]:
    """Build the ``synthesize`` node bound to the LLM adapter."""
    cfg = settings or get_settings()
    prompt = load_prompt("synthesize")

    def synthesize(state: DeptState) -> dict:
        department = state["department"]
        graded: list[Chunk] = list(state.get("graded_chunks") or [])

        # No evidence passed the grade gate → refuse without an LLM call.
        if not graded:
            return {"draft_answer": CANNOT_ANSWER, "draft_citations": []}

        # Citations are 1:1 with the [n] markers the model will emit.
        citations: list[Citation] = [chunk_to_citation(c) for c in graded]

        if budget_exceeded(state.get("deadline_ts")):
            logger.warning("synthesize[%s]: budget exhausted, refusing", department)
            return {"draft_answer": CANNOT_ANSWER, "draft_citations": []}

        rendered = prompt.render(
            question=state.get("question", ""),
            chunks=render_chunks(graded, start=1),
            role_style=role_style_for(state.get("role")),
            language=state.get("request_language", "en"),
            recalled_preferences=state.get("recalled_preferences") or "(none)",
            conversation_history=state.get("conversation_history") or "(none)",
        )
        messages = [
            {"role": "system", "content": rendered["system"]},
            {"role": "user", "content": rendered["user"]},
        ]

        try:
            result = llm.complete(
                tier=ModelTier.MAIN,
                messages=messages,
                temperature=0.0,
                response_format="text",
                timeout_s=cfg.branch_timeout_s,
            )
        except LLMUnavailable as exc:
            logger.warning("synthesize[%s]: LLM unavailable: %s", department, exc)
            return {"draft_answer": CANNOT_ANSWER, "draft_citations": []}

        answer = (result.text or "").strip()
        if not answer:
            answer = CANNOT_ANSWER

        logger.info("synthesize[%s]: %d chars, %d citations model=%s", department, len(answer), len(citations), result.model_used)
        return {"draft_answer": answer, "draft_citations": citations, "model_used": result.model_used}

    return synthesize
