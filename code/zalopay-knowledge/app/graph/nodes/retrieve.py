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
import re
from typing import Callable

from app.config import Settings, get_settings
from app.graph.nodes._helpers import budget_exceeded
from app.graph.state import Chunk, DeptState
from app.ports.errors import RetrieverUnavailable
from app.ports.retriever import RetrieverPort
from app.retrieval.pipeline import refine_candidates

logger = logging.getLogger(__name__)

_TECHNICAL_RE = re.compile(
    r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b"
    r"|/api/"
    r"|\b(MySQL|PostgreSQL|MariaDB|SQLite|MongoDB|Redis)\b",
    re.IGNORECASE,
)
_VERSION_RE = re.compile(r"/v\d+")
_BRACE_RE = re.compile(r"[{}]")
_SLASH_SPLIT_RE = re.compile(r"[/\-_]")


def _expand_technical_query(query: str) -> str | None:
    """Return a natural-language alternative for technical API/DB queries, or None."""
    if not _TECHNICAL_RE.search(query):
        return None
    tokens: list[str] = []
    for part in _SLASH_SPLIT_RE.split(_VERSION_RE.sub("", query)):
        part = _BRACE_RE.sub("", part).strip()
        if part and not re.fullmatch(r"v?\d+", part):
            tokens.append(part)
    natural = " ".join(dict.fromkeys(tokens))
    return natural if natural and natural.lower() != query.lower() else None


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
        lang = state.get("request_language", "en")

        try:
            results = retriever.search(
                department=department,
                query=query,
                k=pool_k,
                language=lang,
            )
        except RetrieverUnavailable as exc:
            logger.warning("retrieve[%s]: index unavailable: %s", department, exc)
            return {"chunks": []}

        # Query expansion: for technical queries run a second search and merge
        if cfg.query_expansion_enabled:
            alt_query = _expand_technical_query(query)
            if alt_query:
                try:
                    alt_results = retriever.search(
                        department=department,
                        query=alt_query,
                        k=pool_k,
                        language=lang,
                    )
                    # Merge by chunk_id, keeping max score per chunk
                    merged: dict[str, object] = {r.chunk_id: r for r in results}
                    for r in alt_results:
                        existing = merged.get(r.chunk_id)
                        if existing is None or r.score > existing.score:  # type: ignore[union-attr]
                            merged[r.chunk_id] = r
                    results = sorted(merged.values(), key=lambda r: r.score, reverse=True)  # type: ignore[arg-type,return-value]
                    logger.info("retrieve[%s]: expanded query=%r, merged pool=%d", department, alt_query, len(results))
                except RetrieverUnavailable:
                    pass

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
