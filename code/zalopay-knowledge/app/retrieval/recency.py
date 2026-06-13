from __future__ import annotations

"""Prefer newer document versions by ``last_modified`` when URLs collide."""

from datetime import datetime

from app.ports.types import RetrievedChunk


def _parse_modified(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def prefer_recent_versions(candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Keep the newest chunk per ``url`` (cheap recency tie-break).

    When multiple chunks share the same source URL (e.g. re-indexed versions),
    only the row with the latest ``last_modified`` survives.  Chunks without
    URLs or timestamps are kept as-is.
    """
    if len(candidates) <= 1:
        return list(candidates)

    best_by_url: dict[str, RetrievedChunk] = {}
    no_url: list[RetrievedChunk] = []

    for chunk in candidates:
        url = (chunk.url or "").strip()
        if not url:
            no_url.append(chunk)
            continue
        existing = best_by_url.get(url)
        if existing is None:
            best_by_url[url] = chunk
            continue
        new_ts = _parse_modified(chunk.last_modified)
        old_ts = _parse_modified(existing.last_modified)
        if new_ts and (old_ts is None or new_ts > old_ts):
            best_by_url[url] = chunk
        elif old_ts is None and new_ts is None and chunk.score > existing.score:
            best_by_url[url] = chunk

    merged = list(best_by_url.values()) + no_url
    merged.sort(key=lambda c: c.score, reverse=True)
    return merged
