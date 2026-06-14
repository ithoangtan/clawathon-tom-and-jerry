from __future__ import annotations

"""``suggest`` node — generate proactive follow-up questions.

Runs AFTER the respond node, using the ROUTING (small/fast) LLM tier.
Returns up to 3 concise follow-up questions derived from the Q&A context and
retrieved source titles.  Failures are silently swallowed — suggestions are
a UX enhancement, never a correctness requirement.
"""

import json
import logging
import re
from typing import Callable

from app.config import Settings, get_settings
from app.graph.state import Citation, GraphState
from app.ports.llm import LLMPort
from app.ports.types import ModelTier
from app.prompts import load_prompt

logger = logging.getLogger(__name__)

_JSON_ARRAY_RE = re.compile(r"\[.*?\]", re.DOTALL)


def _extract_questions(raw: str) -> list[str]:
    """Parse the LLM output — a JSON array — into a list of question strings."""
    try:
        parsed = json.loads(raw.strip())
        if isinstance(parsed, list):
            return [str(q).strip() for q in parsed if isinstance(q, str) and q.strip()][:3]
    except json.JSONDecodeError:
        pass
    # Fallback: extract array anywhere in the output
    m = _JSON_ARRAY_RE.search(raw)
    if m:
        try:
            parsed = json.loads(m.group())
            if isinstance(parsed, list):
                return [str(q).strip() for q in parsed if isinstance(q, str) and q.strip()][:3]
        except json.JSONDecodeError:
            pass
    return []


def _source_titles(citations: list[Citation]) -> str:
    titles = list(dict.fromkeys(c.get("title", "") for c in citations if c.get("title")))
    if not titles:
        return "(no specific sources)"
    return "\n".join(f"- {t}" for t in titles[:5])


def make_suggest_node(
    llm: LLMPort,
    *,
    settings: Settings | None = None,
) -> Callable[[GraphState], dict]:
    """Build the ``suggest`` node bound to the LLM adapter."""
    cfg = settings or get_settings()
    prompt = load_prompt("suggest")

    def suggest(state: GraphState) -> dict:
        # Only generate suggestions for answered/partial responses — skip refused
        status = state.get("status", "refused")
        if status not in ("answered", "partial"):
            return {"suggested_questions": []}

        answer = state.get("answer", "")
        question = state.get("question", "")
        lang = state.get("request_language", "en")
        citations: list[Citation] = list(state.get("citations") or [])

        if not answer or not question:
            return {"suggested_questions": []}

        try:
            rendered = prompt.render(
                question=question,
                answer=answer[:800],  # truncate for token efficiency
                source_titles=_source_titles(citations),
                language="Vietnamese" if lang == "vi" else "English",
            )
            messages = [
                {"role": "system", "content": rendered["system"]},
                {"role": "user", "content": rendered["user"]},
            ]
            result = llm.complete(
                tier=ModelTier.ROUTING,
                messages=messages,
                temperature=0.3,
                response_format="text",
                timeout_s=min(cfg.branch_timeout_s, 20),  # fast timeout — UX only
            )
            questions = _extract_questions(result.content)
            logger.info("suggest: generated %d follow-up questions", len(questions))
            return {"suggested_questions": questions}
        except Exception as exc:  # noqa: BLE001 — never fail the request
            logger.warning("suggest: failed to generate suggestions: %s", exc)
            return {"suggested_questions": []}

    return suggest
