from __future__ import annotations

"""``reconcile`` node — merge department results into one response.

Runs after all department branches join.  Reads ``dept_results`` and produces
the merged ``answer``, the unified ``citations`` list, detected ``conflicts``,
aggregate ``confidence``, and a preliminary ``status``.

Fast paths avoid the MAIN-tier call when it isn't needed:
* zero answered departments → refusal (no LLM call),
* exactly one answered department → pass-through (no LLM call),
* two or more → MAIN-tier merge with ``reconcile.v1.yaml``.

Cross-department citation numbering is unified by offsetting each department's
``[n]`` markers into a single global list before the merge, so the merged
answer's markers resolve against ``citations``.
"""

import logging
import re
from typing import Callable

from app.common.departments import get_department
from app.config import Settings, get_settings
from app.graph.nodes._helpers import budget_exceeded, parse_json_response
from app.graph.state import (
    Citation,
    Conflict,
    ConflictSide,
    DeptResult,
    GraphState,
)
from app.ports.errors import LLMUnavailable
from app.ports.llm import LLMPort
from app.ports.types import ModelTier
from app.prompts import load_prompt

logger = logging.getLogger(__name__)

_MARKER_RE = re.compile(r"\[(\d+)\]")


def make_reconcile_node(
    llm: LLMPort,
    *,
    settings: Settings | None = None,
) -> Callable[[GraphState], dict]:
    """Build the ``reconcile`` node bound to the LLM adapter."""
    cfg = settings or get_settings()
    prompt = load_prompt("reconcile")

    def reconcile(state: GraphState) -> dict:
        results: list[DeptResult] = list(state.get("dept_results") or [])
        lang = state.get("request_language", "en")

        answered = [r for r in results if r.get("status") == "answered" and r.get("answer")]
        refusals = [r["department"] for r in results if r.get("status") != "answered"]

        # ── Fast path: nobody answered ────────────────────────────────────────
        if not answered:
            return {
                "answer": _all_refused_message(lang),
                "citations": [],
                "conflicts": [],
                "confidence": 0.0,
                "status": "refused",
                "refusals": refusals,
            }

        # ── Fast path: single department, pass through ────────────────────────
        if len(answered) == 1:
            r = answered[0]
            return {
                "answer": r["answer"],
                "citations": list(r.get("citations") or []),
                "conflicts": [],
                "confidence": float(r.get("confidence", 0.0)),
                "status": "partial" if refusals else "answered",
                "refusals": refusals,
            }

        # ── Build a global citation list + per-dept marker offsets ─────────────
        global_citations: list[Citation] = []
        offsets: dict[str, int] = {}
        shifted_blocks: list[str] = []
        for r in answered:
            dept = r["department"]
            offsets[dept] = len(global_citations)
            cites = list(r.get("citations") or [])
            global_citations.extend(cites)
            shifted_blocks.append(_render_dept_block(r, offsets[dept], lang))

        base_conf = sum(float(r.get("confidence", 0.0)) for r in answered) / len(answered)

        # ── Budget guard: concatenate instead of calling the MAIN model ───────
        if budget_exceeded(state.get("deadline_ts")):
            logger.warning("reconcile: budget exhausted, concatenating answers")
            return {
                "answer": "\n\n".join(shifted_blocks),
                "citations": global_citations,
                "conflicts": [],
                "confidence": round(base_conf * 0.8, 3),
                "status": "partial" if refusals else "answered",
                "refusals": refusals,
            }

        # ── MAIN-tier merge ───────────────────────────────────────────────────
        rendered = prompt.render(dept_answers="\n\n".join(shifted_blocks))
        messages = [
            {"role": "system", "content": rendered["system"]},
            {"role": "user", "content": rendered["user"]},
        ]
        try:
            result = llm.complete(
                tier=ModelTier.MAIN,
                messages=messages,
                temperature=0.0,
                response_format="json",
                timeout_s=cfg.branch_timeout_s,
            )
            data = parse_json_response(result.text)
        except (LLMUnavailable, ValueError) as exc:
            logger.warning("reconcile: merge failed (%s); concatenating", exc)
            return {
                "answer": "\n\n".join(shifted_blocks),
                "citations": global_citations,
                "conflicts": [],
                "confidence": round(base_conf * 0.8, 3),
                "status": "partial" if refusals else "answered",
                "refusals": refusals,
            }

        merged = str(data.get("merged_answer") or "\n\n".join(shifted_blocks)).strip()
        conflicts = _parse_conflicts(data.get("conflicts"), answered)

        # A flagged conflict downgrades confidence and the overall status.
        confidence = base_conf * (0.7 if conflicts else 1.0)
        status = "partial" if (refusals or conflicts) else "answered"

        logger.info(
            "reconcile: merged %d depts, %d conflicts, %d citations",
            len(answered),
            len(conflicts),
            len(global_citations),
        )
        return {
            "answer": merged,
            "citations": global_citations,
            "conflicts": conflicts,
            "confidence": round(confidence, 3),
            "status": status,
            "refusals": refusals,
        }

    return reconcile


# ── Internals ───────────────────────────────────────────────────────────────────

def _render_dept_block(result: DeptResult, offset: int, lang: str) -> str:
    """Render one department's answer with markers shifted by *offset*."""
    dept = result["department"]
    name = get_department(dept).display_name(lang)
    answer = _shift_markers(result.get("answer", ""), offset)
    cites = result.get("citations") or []
    cite_lines = [
        f"  [{offset + i + 1}] {c.get('title', '')} {c.get('url', '')}".rstrip()
        for i, c in enumerate(cites)
    ]
    cite_block = "\n".join(cite_lines)
    return f"## [{dept}] {name}\n{answer}\n\nCitations:\n{cite_block}"


def _shift_markers(text: str, offset: int) -> str:
    """Shift every ``[n]`` marker in *text* by *offset* (no-op when offset=0)."""
    if offset == 0:
        return text

    def repl(m: re.Match) -> str:
        return f"[{int(m.group(1)) + offset}]"

    return _MARKER_RE.sub(repl, text)


def _parse_conflicts(raw, answered: list[DeptResult]) -> list[Conflict]:
    """Map the model's conflict JSON into :class:`Conflict` TypedDicts.

    ``citation_index`` from the model is 1-based into that *department's own*
    citation list; we resolve it leniently (fall back to the first citation).
    """
    if not isinstance(raw, list):
        return []

    by_dept = {r["department"]: list(r.get("citations") or []) for r in answered}
    conflicts: list[Conflict] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        sides_raw = entry.get("sides") or []
        sides: list[ConflictSide] = []
        for s in sides_raw:
            if not isinstance(s, dict):
                continue
            dept = s.get("department", "")
            cites = by_dept.get(dept, [])
            citation = _resolve_citation(cites, s.get("citation_index"))
            sides.append(
                ConflictSide(
                    department=dept,
                    statement=str(s.get("statement", "")),
                    citation=citation,
                )
            )
        if sides:
            conflicts.append(Conflict(topic=entry.get("topic"), sides=sides))
    return conflicts


def _resolve_citation(cites: list[Citation], index) -> Citation:
    """Best-effort 1-based lookup into *cites*; empty Citation when unavailable."""
    if cites:
        try:
            i = int(index) - 1
            if 0 <= i < len(cites):
                return cites[i]
        except (TypeError, ValueError):
            pass
        return cites[0]
    return Citation(title="", url="")


def _all_refused_message(lang: str) -> str:
    """FR-2.2 refusal copy when no department passes the grade/verify gate."""
    if lang == "vi":
        return (
            "Không có thông tin trong tài liệu.\n\n"
            "Tôi không tìm thấy nội dung liên quan trong tài liệu nội bộ. "
            "Hãy thử hỏi cụ thể hơn hoặc liên hệ bộ phận sở hữu tài liệu."
        )
    return (
        "Not covered in the docs.\n\n"
        "I couldn't find relevant content in the internal documentation. "
        "Try rephrasing your question or contact the document owner."
    )
