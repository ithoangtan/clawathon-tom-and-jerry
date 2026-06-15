from __future__ import annotations

"""``discover_workflow`` node — find the workflow definition to run.

Two paths (SOLUTION §Tầng 2):

* **Explicit name** — the user named a workflow ("Chạy workflow *Campaign Risk
  Review* …") → search the ``workflow`` corpus for that title and take the best
  title match.
* **Semantic** — no name → semantic search over the ``workflow`` corpus filtered
  to ``zalopay-workflow`` + ``status:active`` and rank the matching pages.

Either way it groups chunk hits by ``source`` (the Confluence page id), ranks
pages by their best chunk score, and writes the chosen page + alternatives to
state for the executor (Phase 5).  One pass — no confirmation round-trip.
"""

import json
import logging
from typing import Callable

from app.common.departments import DepartmentKey
from app.config import Settings, get_settings
from app.graph.nodes._helpers import budget_exceeded, parse_json_response
from app.graph.state import GraphState
from app.ports.errors import LLMUnavailable, RetrieverUnavailable
from app.ports.llm import LLMPort
from app.ports.retriever import RetrieverPort
from app.ports.types import ModelTier, RetrievedChunk
from app.prompts import load_prompt

logger = logging.getLogger(__name__)

_WORKFLOW_DEPT = DepartmentKey.WORKFLOW.value
# Labels every executable workflow page must carry (definition-lifecycle gate).
# NB: Confluence labels cannot contain ``:`` — the taxonomy uses a hyphen
# (``status-active``, not ``status:active``). The parser's ``is_executable`` gate
# is the authoritative ACTIVE check; this label filter just keeps non-active
# workflows out of discovery.
_WORKFLOW_LABELS = ["zalopay-workflow", "status-active"]
# Minimum best-chunk score a page must clear to count as a match.
_MIN_SCORE = 0.30


def make_discover_workflow_node(
    retriever: RetrieverPort,
    llm: LLMPort,
    *,
    settings: Settings | None = None,
) -> Callable[[GraphState], dict]:
    """Build the ``discover_workflow`` node bound to its ports."""
    cfg = settings or get_settings()
    prompt = load_prompt("workflow_discovery")

    def discover_workflow(state: GraphState) -> dict:
        question = state.get("question", "")
        lang = state.get("request_language", "en")

        if budget_exceeded(state.get("deadline_ts")):
            return _no_match(_note("budget_exceeded", lang))

        # 1. Extract explicit_name / jira_key / search_query.
        explicit_name, jira_key, search_query = _extract(prompt, llm, question, cfg)

        # 2. Search the workflow corpus (always label-filtered to ACTIVE).
        query = explicit_name or search_query or question
        try:
            chunks = retriever.search(
                department=_WORKFLOW_DEPT,
                query=query,
                k=8,
                language=lang,
                filters={"labels": _WORKFLOW_LABELS},
            )
        except RetrieverUnavailable:
            logger.warning("Workflow discovery: retriever unavailable")
            return _no_match(_note("retriever_unavailable", lang), jira_key=jira_key)

        # 3. Group hits by source page id; rank pages by their best chunk score.
        pages = _rank_pages(chunks)
        if explicit_name:
            pages = _prefer_title_match(pages, explicit_name)

        if not pages or pages[0]["score"] < _MIN_SCORE:
            logger.info("Workflow discovery: no match for %r (query=%r)", question, query)
            return _no_match(_note("no_match", lang), jira_key=jira_key)

        best = pages[0]
        candidates = [
            {"name": p["name"], "page_id": p["page_id"], "score": round(p["score"], 4)}
            for p in pages[:3]
        ]
        logger.info(
            "Workflow discovery: picked %r (page_id=%s, score=%.3f, %d candidate(s))",
            best["name"],
            best["page_id"],
            best["score"],
            len(candidates),
        )
        return {
            "workflow_mode": True,
            "workflow_page_id": best["page_id"],
            "workflow_name": best["name"],
            "workflow_candidates": candidates,
            "jira_parent_key": jira_key,
            "workflow_discovery_note": None,
        }

    return discover_workflow


# ── Internals ─────────────────────────────────────────────────────────────────

def _extract(
    prompt,
    llm: LLMPort,
    question: str,
    cfg: Settings,
) -> tuple[str | None, str | None, str]:
    """Run the LLM extraction; degrade to using the raw question on failure."""
    rendered = prompt.render(question=question)
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
        data = parse_json_response(result.text)
    except (LLMUnavailable, ValueError) as exc:
        logger.warning("Workflow discovery extraction failed (%s); using raw question", exc)
        return None, None, question

    if not isinstance(data, dict):
        return None, None, question
    explicit = _clean(data.get("explicit_name"))
    jira_key = _clean(data.get("jira_key"))
    if jira_key:
        jira_key = jira_key.upper()
    search_query = _clean(data.get("search_query")) or question
    return explicit, jira_key, search_query


def _clean(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or stripped.lower() in {"null", "none"}:
        return None
    return stripped


def _rank_pages(chunks: list[RetrievedChunk]) -> list[dict]:
    """Collapse scored chunks into pages keyed by ``source`` (page id).

    Each page keeps the best chunk score and the title of that best chunk.
    Returned sorted by score descending.
    """
    by_page: dict[str, dict] = {}
    for ch in chunks:
        page_id = ch.source
        if not page_id:
            continue
        existing = by_page.get(page_id)
        if existing is None or ch.score > existing["score"]:
            by_page[page_id] = {
                "page_id": page_id,
                "name": ch.title or "(untitled workflow)",
                "score": ch.score,
            }
    return sorted(by_page.values(), key=lambda p: p["score"], reverse=True)


def _prefer_title_match(pages: list[dict], name: str) -> list[dict]:
    """Re-rank so pages whose title best matches *name* float to the top.

    A case-insensitive substring match (either direction) is treated as a strong
    signal that beats raw score; otherwise original score order is preserved.
    """
    target = name.casefold().strip()

    def key(p: dict) -> tuple[int, float]:
        title = (p["name"] or "").casefold()
        if title == target:
            rank = 3
        elif target in title or title in target:
            rank = 2
        else:
            rank = 1
        return (rank, p["score"])

    return sorted(pages, key=key, reverse=True)


def _no_match(note: str, *, jira_key: str | None = None) -> dict:
    return {
        "workflow_mode": True,
        "workflow_page_id": None,
        "workflow_name": None,
        "workflow_candidates": [],
        "jira_parent_key": jira_key,
        "workflow_discovery_note": note,
    }


def _note(reason: str, lang: str) -> str:
    vi = lang == "vi"
    if reason == "budget_exceeded":
        return (
            "Hết thời gian xử lý trước khi tìm được workflow."
            if vi
            else "Ran out of time before a workflow could be found."
        )
    if reason == "retriever_unavailable":
        return (
            "Không truy cập được kho workflow lúc này."
            if vi
            else "The workflow registry is not available right now."
        )
    return (
        "Không tìm thấy workflow đang hoạt động (ACTIVE) phù hợp với yêu cầu."
        if vi
        else "No matching active (ACTIVE) workflow was found for this request."
    )
