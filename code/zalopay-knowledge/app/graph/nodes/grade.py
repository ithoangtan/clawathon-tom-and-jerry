from __future__ import annotations

"""``grade`` node — LLM relevance grading + the grade gate.

Second node of a department subgraph.  Scores each retrieved chunk for
relevance to the question (SMALL tier, ``grade.v1.yaml``), then keeps only the
chunks whose score meets ``GRADE_THRESHOLD``.  The surviving chunks (re-scored
with the LLM relevance score and re-sorted) become ``graded_chunks`` and are
also published to the parent's ``evidence`` map for audit.

Degradation: if the grader LLM is unavailable or returns unparsable JSON, we
fall back to the retriever's own cosine score for gating so the branch can
still produce an answer.
"""

import logging
from typing import Callable

from app.config import Settings, get_settings
from app.graph.nodes._helpers import (
    budget_exceeded,
    parse_json_response,
    render_chunks,
)
from app.graph.state import Chunk, DeptState
from app.ports.errors import LLMUnavailable
from app.ports.llm import LLMPort
from app.ports.types import ModelTier
from app.prompts import load_prompt

logger = logging.getLogger(__name__)


def make_grade_node(
    llm: LLMPort,
    *,
    settings: Settings | None = None,
) -> Callable[[DeptState], dict]:
    """Build the ``grade`` node bound to the LLM adapter."""
    cfg = settings or get_settings()
    prompt = load_prompt("grade")

    def grade(state: DeptState) -> dict:
        department = state["department"]
        chunks: list[Chunk] = list(state.get("chunks") or [])

        # Nothing to grade — short-circuit, no LLM call.
        if not chunks:
            return {"graded_chunks": [], "evidence": {department: []}}

        if budget_exceeded(state.get("deadline_ts")):
            logger.warning("grade[%s]: budget exhausted, using retriever scores", department)
            graded = _gate_by_retriever_score(chunks, cfg.grade_threshold)
            return {"graded_chunks": graded, "evidence": {department: graded}}

        # grade.v1.yaml uses 0-indexed chunk ids.
        rendered = prompt.render(
            question=state.get("question", ""),
            chunks=render_chunks(chunks, start=0),
        )
        messages = [
            {"role": "system", "content": rendered["system"]},
            {"role": "user", "content": rendered["user"]},
        ]

        try:
            result = llm.complete(
                tier=ModelTier.SMALL,
                messages=messages,
                temperature=0.0,
                response_format="json",
                timeout_s=cfg.branch_timeout_s,
            )
            scores = _parse_scores(result.text, n=len(chunks))
        except (LLMUnavailable, ValueError) as exc:
            logger.warning("grade[%s]: grader failed (%s); using retriever scores", department, exc)
            graded = _gate_by_retriever_score(chunks, cfg.grade_threshold)
            return {"graded_chunks": graded, "evidence": {department: graded}}

        # Apply LLM scores, gate, and re-sort.
        graded: list[Chunk] = []
        for idx, ch in enumerate(chunks):
            llm_score = scores.get(idx)
            if llm_score is None:
                continue
            if llm_score >= cfg.grade_threshold:
                scored = dict(ch)
                scored["score"] = llm_score
                graded.append(scored)  # type: ignore[arg-type]
        graded.sort(key=lambda c: c.get("score", 0.0), reverse=True)

        logger.info("grade[%s]: %d/%d chunks passed", department, len(graded), len(chunks))
        return {"graded_chunks": graded, "evidence": {department: graded}}

    return grade


# ── Internals ───────────────────────────────────────────────────────────────────

def _parse_scores(text: str, *, n: int) -> dict[int, float]:
    """Parse the grader JSON into ``{chunk_index: score}``."""
    data = parse_json_response(text)
    scores: dict[int, float] = {}
    for entry in data.get("scores", []) if isinstance(data, dict) else []:
        try:
            idx = int(entry["id"])
            score = float(entry["score"])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= idx < n:
            scores[idx] = max(0.0, min(1.0, score))
    return scores


def _gate_by_retriever_score(chunks: list[Chunk], threshold: float) -> list[Chunk]:
    """Fallback gate using the retriever's cosine score when grading fails."""
    kept = [c for c in chunks if c.get("score", 0.0) >= threshold]
    kept.sort(key=lambda c: c.get("score", 0.0), reverse=True)
    return kept
