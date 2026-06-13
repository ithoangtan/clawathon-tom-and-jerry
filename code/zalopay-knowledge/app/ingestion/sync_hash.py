from __future__ import annotations

"""Content-hash helpers for idempotent sync (G4 / FR-5.6).

Unchanged page bodies skip re-chunking on subsequent sync runs.  The department
partition is still rebuilt atomically so serving never reads a half-written index.
"""

import hashlib
from typing import Callable

from app.store.meta import MetaStore


def page_content_hash(text: str) -> str:
    """Stable SHA-256 hex digest for a normalized page body."""
    normalized = text.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def resolve_document_chunks(
    *,
    department: str,
    url: str,
    text: str,
    meta: MetaStore,
    chunk_builder: Callable[[], list[dict]],
) -> tuple[list[dict], bool]:
    """Return chunks for one document, reusing indexed rows when the hash matches.

    Returns ``(chunks, skipped_rechunk)`` where *skipped_rechunk* is True when
    the stored hash matched and existing active rows were reused.
    """
    if not url:
        return chunk_builder(), False

    digest = page_content_hash(text)
    if meta.get_source_hash(department, url) == digest:
        existing = meta.fetch_chunks_by_url(department, url, active_only=True)
        if existing:
            return existing, True

    return chunk_builder(), False
