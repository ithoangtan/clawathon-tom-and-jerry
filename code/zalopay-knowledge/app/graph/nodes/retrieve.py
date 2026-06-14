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
    r"|\b(MySQL|PostgreSQL|MariaDB|SQLite|MongoDB|Redis)\b"
    # natural-language technical intent signals (EN + VI)
    r"|\btech[ -]?stack\b"
    r"|\btechnology[ -]?stack\b"
    r"|\b(database|db schema|data model)\b"
    r"|\b(API|endpoint|endpoints)\b"
    r"|\b(architecture|kiến[ -]?trúc|công[ -]?nghệ|kỹ[ -]?thuật)\b"
    r"|\b(framework|library|thư[ -]?viện)\b",
    re.IGNORECASE,
)
_VERSION_RE = re.compile(r"/v\d+")
_BRACE_RE = re.compile(r"[{}]")
_SLASH_SPLIT_RE = re.compile(r"[/\-_]")

# Extra terms appended when the query signals tech-stack / DB / API discovery
# but doesn't name specific values — improves BM25 recall against doc sections
# that use concrete names (MySQL, Spring, /api/v1/...).
_TECHSTACK_BOOST = "MySQL PostgreSQL Spring Java database API endpoint architecture"
_API_BOOST = "POST GET endpoint /api/ spin campaign"
_TECHSTACK_INTENT_RE = re.compile(
    r"\b(tech[ -]?stack|technology|kiến[ -]?trúc|công[ -]?nghệ|architecture|framework)\b",
    re.IGNORECASE,
)
_DB_INTENT_RE = re.compile(
    r"\b(database|db|MySQL|PostgreSQL|MariaDB|SQLite|MongoDB|Redis|data[ -]?model|schema)\b",
    re.IGNORECASE,
)
_API_INTENT_RE = re.compile(
    r"\b(API|endpoint|endpoints|spin|tích[ -]?hợp|integration)\b",
    re.IGNORECASE,
)


def _expand_technical_query(query: str) -> str | None:
    """Return an enriched alternative query for technical API/DB/stack questions.

    For URL-like queries (containing slashes, HTTP verbs, etc.) extracts natural
    tokens as before.  For natural-language tech discovery questions (e.g. "tech
    stack gì", "database là gì", "API endpoint nào") appends domain-specific boost
    terms so BM25 can surface chunks that name concrete values like MySQL or /api/.
    """
    if not _TECHNICAL_RE.search(query):
        return None

    # URL/code-like query: extract natural tokens from path segments
    if "/api/" in query.lower() or re.search(r"\b(GET|POST|PUT|PATCH|DELETE)\b", query, re.I):
        tokens: list[str] = []
        for part in _SLASH_SPLIT_RE.split(_VERSION_RE.sub("", query)):
            part = _BRACE_RE.sub("", part).strip()
            if part and not re.fullmatch(r"v?\d+", part):
                tokens.append(part)
        natural = " ".join(dict.fromkeys(tokens))
        return natural if natural and natural.lower() != query.lower() else None

    # Natural-language discovery query: boost with domain terms
    boosts: list[str] = []
    if _TECHSTACK_INTENT_RE.search(query) or _DB_INTENT_RE.search(query):
        boosts.append(_TECHSTACK_BOOST)
    if _API_INTENT_RE.search(query):
        boosts.append(_API_BOOST)
    if not boosts:
        return None
    expanded = f"{query} {' '.join(boosts)}"
    return expanded


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
