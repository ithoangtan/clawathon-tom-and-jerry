from __future__ import annotations

"""Semantic chunking for Confluence pages and PDF text."""

import hashlib
import re
import uuid
from typing import Iterator

from app.ingestion.metadata import (
    DOC_TYPES,
    chunk_metadata_defaults,
    serialize_acl,
    serialize_labels,
    slugify_heading,
)

# Target ~400–600 tokens using a chars heuristic (≈4 chars/token).
_MIN_CHARS = 300
_MAX_CHARS = 3200
_OVERLAP_CHARS = 120

# Rule-based doc-type labels (FR-5.3 / G6) — no LLM calls.
# Order matters: more specific patterns before broader ones.
_DOC_TYPE_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("prd", "product requirement", "product spec", "product requirements"), "PRD"),
    (("rca", "root cause", "postmortem", "post-mortem", "incident review"), "RCA"),
    (("security", "soc ", "pentest", "vulnerability", "infosec", "cyber"), "Security"),
    (("risk", "compliance", "aml", "kyc", "fraud", "regulatory"), "Risk"),
    (
        ("ops-guidance", "ops guidance", "operational guidance", "how-to guide", "best practice"),
        "Ops-guidance",
    ),
    (("runbook", "sop", "playbook", "operating procedure", "operation manual"), "Operation"),
    (
        ("architecture", "technical", "api doc", "design doc", "engineering spec", "system design"),
        "Technical",
    ),
    (
        ("org chart", "org structure", "org-structure", "organization", "team structure", "reporting line"),
        "Org-structure",
    ),
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
    """Classify a document by title/path/label rules (zero LLM tokens).

    Returns one of :data:`DOC_TYPES`.
    """
    haystack = f"{title} {url} {' '.join(labels or [])}".lower()
    for keywords, doc_type in _DOC_TYPE_KEYWORDS:
        if any(kw in haystack for kw in keywords):
            return doc_type
    default = _DEPARTMENT_DOC_TYPE_DEFAULT.get(department, "Operation")
    assert default in DOC_TYPES
    return default


def chunk_text(
    text: str,
    *,
    department: str,
    doc_type: str,
    title: str,
    url: str,
    source: str | None = None,
    section: str | None = None,
    anchor: str | None = None,
    space: str | None = None,
    labels: list[str] | str | None = None,
    last_modified: str | None = None,
    author: str | None = None,
    acl: list[str] | str | None = None,
    lifecycle_state: str = "active",
    source_type: str = "confluence",
    page: int | None = None,
) -> list[dict]:
    """Split *text* into chunk dicts ready for :class:`MetaStore`."""
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not text:
        return []

    labels_json = labels if isinstance(labels, str) else serialize_labels(labels)
    acl_json = acl if isinstance(acl, str) else serialize_acl(acl if isinstance(acl, list) else None)
    meta_defaults = chunk_metadata_defaults(
        source=source,
        space=space,
        labels=labels_json,
        author=author,
        acl=acl_json,
    )

    segments = _split_segments(text)
    chunks: list[dict] = []
    for seg in segments:
        seg_section, seg_anchor = _segment_heading(seg)
        chunk_section = section if section is not None else seg_section
        if anchor is not None:
            chunk_anchor = anchor
        elif seg_anchor:
            chunk_anchor = seg_anchor
        elif chunk_section:
            chunk_anchor = slugify_heading(chunk_section) or None
        else:
            chunk_anchor = None

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
                    "section": chunk_section,
                    "last_modified": last_modified,
                    "lifecycle_state": lifecycle_state,
                    "source_type": source_type,
                    "page": page,
                    "text": piece,
                    **meta_defaults,
                    "anchor": chunk_anchor,
                }
            )
    return chunks


def _segment_heading(segment: str) -> tuple[str | None, str | None]:
    """Extract the first markdown heading from *segment*, if any."""
    first_line = segment.strip().split("\n", 1)[0]
    match = re.match(r"^#{1,4}\s+(.+)$", first_line.strip())
    if not match:
        return None, None
    heading = match.group(1).strip()
    slug = slugify_heading(heading)
    return heading, slug or None


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
