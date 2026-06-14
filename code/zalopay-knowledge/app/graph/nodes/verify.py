from __future__ import annotations

"""``verify`` node — entailment check + DeptResult emission (branch terminal).

Final node of a department subgraph.  Splits ``draft_answer`` into
citation-bearing claims, asks the SMALL tier (``verify.v1.yaml``) whether each
claim is entailed by its cited chunk, and converts the outcome into the single
:class:`DeptResult` this branch contributes to the parent ``dept_results``
list (reduced by ``operator.add``).

Decision table:
* no graded evidence / synthesize refused  → ``status="refused"``
* answer has no citation markers           → ``status="refused"`` (ungrounded)
* zero claims survive verification         → ``status="refused"``
* some claims unsupported                   → ``status="answered"`` + warning,
                                              confidence scaled by support ratio
* all claims supported                      → ``status="answered"``

We do not physically rewrite the markdown to strip unsupported sentences (that
risks corrupting citation numbering); instead we scale confidence and surface a
warning so reconcile/respond and the user can judge.
"""

import logging
from typing import Callable

from app.graph.nodes._helpers import (
    budget_exceeded,
    extract_claims,
    filter_citations_by_markers,
    parse_json_response,
    prune_unsupported_claims,
    render_claims,
)
from app.graph.nodes.synthesize import CANNOT_ANSWER
from app.config import Settings, get_settings
from app.graph.state import Chunk, Citation, DeptResult, DeptState
from app.ports.errors import LLMUnavailable
from app.ports.llm import LLMPort
from app.ports.types import ModelTier
from app.prompts import load_prompt

logger = logging.getLogger(__name__)


def make_verify_node(
    llm: LLMPort,
    *,
    settings: Settings | None = None,
) -> Callable[[DeptState], dict]:
    """Build the ``verify`` node bound to the LLM adapter."""
    cfg = settings or get_settings()
    prompt = load_prompt("verify")

    def verify(state: DeptState) -> dict:
        department = state["department"]
        answer = (state.get("draft_answer") or "").strip()
        citations: list[Citation] = list(state.get("draft_citations") or [])
        graded: list[Chunk] = list(state.get("graded_chunks") or [])
        model_used: str = state.get("model_used") or ""

        # ── Disabled / refusal paths ──────────────────────────────────────────
        if not cfg.verify_enabled:
            if not answer or answer == CANNOT_ANSWER or not graded:
                return _emit(_refused(department, state.get("request_language", "en")))
            logger.info("verify[%s]: skipped (VERIFY_ENABLED=false), passing through", department)
            base_conf = _mean_score(graded)
            return _emit(
                DeptResult(
                    department=department,
                    status="answered",
                    answer=answer,
                    citations=citations,
                    confidence=round(base_conf * 0.8, 3),
                    warnings=["verification_disabled"],
                    model_used=model_used,
                )
            )

        if not answer or answer == CANNOT_ANSWER or not graded:
            return _emit(_refused(department, state.get("request_language", "en")))

        claims = extract_claims(answer, graded)
        if not claims:
            # An answer with no resolvable citations is ungrounded → refuse.
            logger.warning("verify[%s]: answer has no citation markers, refusing", department)
            return _emit(_refused(department, state.get("request_language", "en")))

        warnings: list[str] = _deprecation_warnings(answer, graded)
        base_conf = _mean_score(graded)

        # ── Budget guard: accept unverified but flag it ───────────────────────
        if budget_exceeded(state.get("deadline_ts")):
            logger.warning("verify[%s]: budget exhausted, accepting unverified", department)
            warnings.append("verification_skipped_budget")
            return _emit(
                DeptResult(
                    department=department,
                    status="answered",
                    answer=answer,
                    citations=citations,
                    confidence=round(base_conf * 0.6, 3),
                    warnings=warnings,
                )
            )

        # ── Entailment check ──────────────────────────────────────────────────
        rendered = prompt.render(claims_with_sources=render_claims(claims))
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
            verdicts = _parse_verdicts(result.text, n=len(claims))
        except (LLMUnavailable, ValueError) as exc:
            # Degrade: accept the answer but flag verification as skipped.
            logger.warning("verify[%s]: verifier failed (%s); accepting unverified", department, exc)
            warnings.append("verification_skipped_error")
            return _emit(
                DeptResult(
                    department=department,
                    status="answered",
                    answer=answer,
                    citations=citations,
                    confidence=round(base_conf * 0.6, 3),
                    warnings=warnings,
                )
            )

        supported = sum(1 for v in verdicts.values() if v)
        total = len(claims)
        support_ratio = supported / total if total else 0.0

        if supported == 0:
            logger.warning("verify[%s]: 0/%d claims supported, refusing", department, total)
            return _emit(_refused(department, state.get("request_language", "en")))

        pruned_answer, used_markers, dropped = prune_unsupported_claims(
            answer, claims, verdicts
        )
        if not pruned_answer.strip():
            logger.warning("verify[%s]: all claims pruned, refusing", department)
            return _emit(_refused(department, state.get("request_language", "en")))

        filtered_citations = filter_citations_by_markers(citations, used_markers)
        if not filtered_citations:
            logger.warning("verify[%s]: no citations after prune, refusing", department)
            return _emit(_refused(department, state.get("request_language", "en")))

        if supported < total:
            warnings.append(f"unverified_claims:{total - supported}/{total}")

        confidence = round(base_conf * support_ratio, 3)
        logger.info(
            "verify[%s]: %d/%d claims supported (conf=%.2f), pruned %d",
            department,
            supported,
            total,
            confidence,
            len(dropped),
        )
        return _emit(
            DeptResult(
                department=department,
                status="answered",
                answer=pruned_answer,
                citations=filtered_citations,
                confidence=confidence,
                warnings=warnings,
            )
        )

    return verify


# ── Internals ───────────────────────────────────────────────────────────────────

def _emit(result: DeptResult) -> dict:
    """Wrap a single DeptResult for the ``operator.add`` reducer."""
    return {"dept_results": [result]}


def _refused(department: str, lang: str) -> DeptResult:
    return DeptResult(
        department=department,
        status="refused",
        answer="",
        citations=[],
        confidence=0.0,
        warnings=["no_supporting_sources"],
    )


def _parse_verdicts(text: str, *, n: int) -> dict[int, bool]:
    data = parse_json_response(text)
    out: dict[int, bool] = {}
    for entry in data.get("verdicts", []) if isinstance(data, dict) else []:
        try:
            idx = int(entry["id"])
            supported = bool(entry["supported"])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= idx < n:
            out[idx] = supported
    return out


def _mean_score(chunks: list[Chunk]) -> float:
    if not chunks:
        return 0.0
    return sum(c.get("score", 0.0) for c in chunks) / len(chunks)


def _deprecation_warnings(answer: str, chunks: list[Chunk]) -> list[str]:
    """Flag when any cited chunk is deprecated (mirrors the synthesize rule)."""
    import re

    cited = {int(m) for m in re.findall(r"\[(\d+)\]", answer)}
    for n in cited:
        if 1 <= n <= len(chunks) and (chunks[n - 1].get("lifecycle_state") == "deprecated"):
            return ["cites_deprecated_source"]
    return []
