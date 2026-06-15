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

# Domain term mappings for bilingual query expansion.
# VI→EN: appended when query is in Vietnamese so BM25 can match English documents.
# EN→VI: appended when query is in English so BM25 can match Vietnamese documents.
_VI_TO_EN: list[tuple[str, str]] = [
    ("quy trình", "process workflow"),
    ("lưu ý", "note important guideline"),
    ("rủi ro", "risk"),
    ("đối tác", "partner"),
    ("ngân hàng", "bank"),
    ("thanh toán", "payment"),
    ("tích hợp", "integration"),
    ("hợp đồng", "contract"),
    ("khách hàng", "customer client"),
    ("phát triển kinh doanh", "business development"),
    ("tuân thủ", "compliance"),
    ("gian lận", "fraud"),
    ("giới hạn", "limit threshold"),
    ("chính sách", "policy"),
    ("quy định", "regulation rule"),
    ("phê duyệt", "approval"),
    ("báo cáo", "report"),
    ("kiểm tra", "audit check"),
    ("onboard", "onboarding"),
    ("đối soát", "reconciliation"),
    ("hạn mức", "quota limit"),
    ("kết nối", "connection integration"),
]
_EN_TO_VI: list[tuple[str, str]] = [
    ("risk", "rủi ro"),
    ("process", "quy trình"),
    ("workflow", "quy trình"),
    ("policy", "chính sách quy định"),
    ("compliance", "tuân thủ"),
    ("partner", "đối tác"),
    ("bank", "ngân hàng"),
    ("payment", "thanh toán"),
    ("integration", "tích hợp"),
    ("contract", "hợp đồng"),
    ("fraud", "gian lận"),
    ("limit", "giới hạn hạn mức"),
    ("approval", "phê duyệt"),
    ("reconciliation", "đối soát"),
    ("onboarding", "onboard"),
]


def _expand_bilingual_query(query: str, lang: str) -> str | None:
    """Append cross-language domain term equivalents to improve BM25 recall.

    When the query is in Vietnamese, matching English documents via BM25 is hard
    because there is zero token overlap.  bge-m3 handles cross-lingual similarity
    for the dense path, but BM25 in hybrid fusion is purely lexical.  Appending
    known EN equivalents of domain terms found in the VI query (and vice versa)
    gives BM25 the tokens it needs without an LLM call.
    """
    query_lower = query.lower()
    mapping = _VI_TO_EN if lang == "vi" else _EN_TO_VI
    extra: list[str] = []
    for src, tgt in mapping:
        if src in query_lower:
            extra.append(tgt)
    if not extra:
        return None
    return f"{query} {' '.join(extra)}"


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

        def _merge_with_alt(base: list, alt_query: str, label: str) -> list:
            try:
                alt = retriever.search(
                    department=department,
                    query=alt_query,
                    k=pool_k,
                    language=lang,
                )
                merged: dict[str, object] = {r.chunk_id: r for r in base}
                for r in alt:
                    existing = merged.get(r.chunk_id)
                    if existing is None or r.score > existing.score:  # type: ignore[union-attr]
                        merged[r.chunk_id] = r
                combined = sorted(merged.values(), key=lambda r: r.score, reverse=True)  # type: ignore[arg-type,return-value]
                logger.info("retrieve[%s]: %s query=%r, merged pool=%d", department, label, alt_query, len(combined))
                return combined  # type: ignore[return-value]
            except RetrieverUnavailable:
                return base

        # Technical query expansion (HTTP verbs, SQL dialects, API paths)
        if cfg.query_expansion_enabled:
            alt_query = _expand_technical_query(query)
            if alt_query:
                results = _merge_with_alt(results, alt_query, "tech-expanded")

        # Bilingual expansion: append cross-language domain term equivalents so
        # BM25 can match documents written in the other language.
        if cfg.bilingual_expansion_enabled:
            bilingual_query = _expand_bilingual_query(query, lang)
            if bilingual_query:
                results = _merge_with_alt(results, bilingual_query, "bilingual-expanded")

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
