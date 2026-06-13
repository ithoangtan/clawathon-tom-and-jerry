from __future__ import annotations

"""``compress`` node — query-focused sentence extraction per graded chunk.

Third node of a department subgraph (between ``grade`` and ``synthesize``).
For each graded chunk whose text exceeds MIN_TEXT_LEN characters, calls the
SMALL LLM with the ``compress.v1.yaml`` prompt to extract only the sentences
relevant to the retrieval query.  The extracted text is stored as
``compressed_text`` on the chunk; ``render_chunks`` in ``_helpers.py`` prefers
it over ``text``, so synthesis sees a trimmed context window.

Degradation contract
--------------------
- ``compress_enabled=False`` → no-op (return ``{}``)
- Budget already exhausted → no-op (return ``{}``)
- LLM unavailable or returns unparsable JSON → leave chunk unchanged (no
  ``compressed_text`` key), log a warning, and continue.
- Compressed text longer than original → discard it, leave chunk unchanged.
"""

import logging
import time
from typing import Callable

from app.config import Settings, get_settings
from app.graph.nodes._helpers import budget_exceeded, parse_json_response
from app.graph.state import Chunk, DeptState
from app.ports.errors import LLMUnavailable
from app.ports.llm import LLMPort
from app.ports.types import ModelTier
from app.prompts import load_prompt

logger = logging.getLogger(__name__)

# Chunks shorter than this are not worth compressing — skip the LLM call.
MIN_TEXT_LEN = 150

# Hard ceiling on the per-chunk LLM timeout (compress is best-effort).
_MAX_TIMEOUT_S = 10.0


def make_compress_node(
    llm: LLMPort,
    *,
    settings: Settings | None = None,
) -> Callable[[DeptState], dict]:
    """Build the ``compress`` node bound to the LLM adapter."""
    cfg = settings or get_settings()
    prompt = load_prompt("compress")

    def compress(state: DeptState) -> dict:
        if not cfg.compress_enabled:
            return {}

        deadline_ts = state.get("deadline_ts")
        # budget_exceeded() treats falsy values (including 0.0) as "no deadline".
        # We check explicitly: if deadline_ts is set, compare against wall time so
        # that deadline_ts=0.0 (already expired) is correctly caught.
        if deadline_ts is not None and time.time() >= deadline_ts:
            logger.warning(
                "compress[%s]: budget exhausted, skipping compression",
                state.get("department", "?"),
            )
            return {}

        department = state.get("department", "?")
        query = state.get("retrieval_query") or state.get("question", "")
        chunks: list[Chunk] = list(state.get("graded_chunks") or [])

        if not chunks:
            return {"graded_chunks": []}

        timeout_s = min(cfg.branch_timeout_s, _MAX_TIMEOUT_S)
        result_chunks: list[Chunk] = []

        for ch in chunks:
            text = ch.get("text", "")
            if len(text) < MIN_TEXT_LEN:
                # Short chunk — copy as-is, no compressed_text added.
                result_chunks.append(ch)
                continue

            rendered = prompt.render(query=query, text=text)
            messages = [
                {"role": "system", "content": rendered["system"]},
                {"role": "user", "content": rendered["user"]},
            ]

            try:
                llm_result = llm.complete(
                    tier=ModelTier.SMALL,
                    messages=messages,
                    temperature=0.0,
                    response_format="json",
                    timeout_s=timeout_s,
                )
                data = parse_json_response(llm_result.text)
                compressed = data["compressed"]
            except (LLMUnavailable, ValueError, KeyError, TypeError) as exc:
                logger.warning(
                    "compress[%s]: failed for chunk %r (%s); leaving unchanged",
                    department,
                    ch.get("chunk_id"),
                    exc,
                )
                result_chunks.append(ch)
                continue

            # Only store if compression actually shortened the text.
            if isinstance(compressed, str) and len(compressed) < len(text):
                updated = dict(ch)
                updated["compressed_text"] = compressed
                result_chunks.append(updated)  # type: ignore[arg-type]
            else:
                result_chunks.append(ch)

        logger.info(
            "compress[%s]: processed %d chunks",
            department,
            len(result_chunks),
        )
        return {"graded_chunks": result_chunks}

    return compress
