from __future__ import annotations

"""Semantic chunking for Confluence pages and PDF text."""

import hashlib
import re
import uuid
from typing import Iterator

# Target ~400–600 tokens using a chars heuristic (≈4 chars/token).
_MIN_CHARS = 300
_MAX_CHARS = 3200
_OVERLAP_CHARS = 120

# Rule-based doc-type labels (FR-5.3) — no LLM calls.
_DOC_TYPE_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("prd", "product requirement", "product spec"), "PRD"),
    (("rca", "root cause", "postmortem", "post-mortem"), "RCA"),
    (("security", "soc ", "pentest", "vulnerability"), "Security"),
    (("risk", "compliance", "aml", "kyc", "fraud"), "Risk"),
    (("runbook", "sop", "playbook", "operation", "ops"), "Operation"),
    (("architecture", "technical", "api doc", "design doc"), "Technical"),
    (("org chart", "organization", "team structure"), "Org"),
)

_DEPARTMENT_DOC_TYPE_DEFAULT: dict[str, str] = {
    "risk": "Risk",
    "grow_enablement": "Operation",
    "bank_partnerships": "Technical",
}


def classify_doc_type(
    *,
    title: str,
    url: str = "",
    department: str = "",
    labels: list[str] | None = None,
) -> str:
    """Classify a document by title/path/label rules (zero LLM tokens)."""
    haystack = f"{title} {url} {' '.join(labels or [])}".lower()
    for keywords, doc_type in _DOC_TYPE_KEYWORDS:
        if any(kw in haystack for kw in keywords):
            return doc_type
    return _DEPARTMENT_DOC_TYPE_DEFAULT.get(department, "Operation")


def chunk_text(
    text: str,
    *,
    department: str,
    doc_type: str,
    title: str,
    url: str,
    section: str | None = None,
    last_modified: str | None = None,
    lifecycle_state: str = "active",
    source_type: str = "confluence",
    page: int | None = None,
) -> list[dict]:
    """Split *text* into chunk dicts ready for :class:`MetaStore`."""
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not text:
        return []

    segments = _split_segments(text)
    chunks: list[dict] = []
    for seg in segments:
        for piece in _window(seg):
            chunk_id = _chunk_id(department, url, piece)
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "department": department,
                    "vec_pos": 0,  # assigned by indexer
                    "doc_type": doc_type,
                    "title": title,
                    "url": url,
                    "section": section,
                    "last_modified": last_modified,
                    "lifecycle_state": lifecycle_state,
                    "source_type": source_type,
                    "page": page,
                    "text": piece,
                }
            )
    return chunks


def _split_segments(text: str) -> list[str]:
    """Split on markdown headings / blank lines to respect semantic boundaries."""
    parts = re.split(r"(?m)(?=^#{1,4}\s)|(?<=\n\n)", text)
    merged: list[str] = []
    buf = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(buf) + len(part) + 2 <= _MAX_CHARS:
            buf = f"{buf}\n\n{part}".strip() if buf else part
        else:
            if buf:
                merged.append(buf)
            buf = part
    if buf:
        merged.append(buf)
    return merged or [text]


def _window(segment: str) -> Iterator[str]:
    if len(segment) <= _MAX_CHARS:
        yield segment
        return
    start = 0
    while start < len(segment):
        end = min(start + _MAX_CHARS, len(segment))
        yield segment[start:end]
        if end >= len(segment):
            break
        start = max(end - _OVERLAP_CHARS, start + _MIN_CHARS)


def _chunk_id(department: str, url: str, text: str) -> str:
    digest = hashlib.sha256(f"{department}|{url}|{text[:200]}".encode()).hexdigest()[:16]
    return f"{department}-{digest}-{uuid.uuid4().hex[:8]}"
