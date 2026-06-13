from __future__ import annotations

"""``retrieve`` node — department-scoped vector search (one per branch).

The first node of a department subgraph.  It calls :class:`RetrieverPort` for
this branch's department and stores the raw chunks.  ``sunset`` chunks are
already excluded by the adapter; ``deprecated`` chunks are returned tagged.

No LLM call.  On :class:`RetrieverUnavailable` it degrades to an empty chunk
list so the downstream ``grade``/``synthesize`` nodes refuse cleanly for this
department only — the other branches are unaffected.
"""

import logging
from typing import Callable

from app.config import Settings, get_settings
from app.graph.nodes._helpers import budget_exceeded
from app.graph.state import Chunk, DeptState
from app.ports.errors import RetrieverUnavailable
from app.ports.retriever import RetrieverPort
from app.retrieval.pipeline import refine_candidates

logger = logging.getLogger(__name__)


def make_retrieve_node(
    retriever: RetrieverPort,
    *,
    settings: Settings | None = None,
) -> Callable[[DeptState], dict]:
    """Build the ``retrieve`` node bound to the retriever adapter."""
    cfg = settings or get_settings()

    def retrieve(state: DeptState) -> dict:
        department = state["department"]

        if budget_exceeded(state.get("deadline_ts")):
            logger.warning("retrieve[%s]: budget exhausted, skipping", department)
            return {"chunks": []}

        query = state.get("retrieval_query") or state.get("question", "")
        pool_k = cfg.retrieve_pool if cfg.hybrid_search_enabled or cfg.reranker_enabled else cfg.topk

        try:
            results = retriever.search(
                department=department,
                query=query,
                k=pool_k,
                language=state.get("request_language", "en"),
            )
        except RetrieverUnavailable as exc:
            logger.warning("retrieve[%s]: index unavailable: %s", department, exc)
            return {"chunks": []}

        if cfg.hybrid_search_enabled or cfg.reranker_enabled:
            results = refine_candidates(query, results, settings=cfg)

        chunks: list[Chunk] = [_to_chunk(r, department) for r in results]
        logger.info("retrieve[%s]: %d chunks", department, len(chunks))
        return {"chunks": chunks}

    return retrieve


def _to_chunk(r, department: str) -> Chunk:
    """Convert a :class:`RetrievedChunk` dataclass into a state ``Chunk`` dict."""
    return Chunk(
        chunk_id=r.chunk_id,
        department=r.department or department,
        doc_type=r.doc_type,
        title=r.title,
        url=r.url,
        section=r.section,
        last_modified=r.last_modified,
        lifecycle_state=r.lifecycle_state,
        source_type=r.source_type,
        page=r.page,
        text=r.text,
        score=r.score,
    )
