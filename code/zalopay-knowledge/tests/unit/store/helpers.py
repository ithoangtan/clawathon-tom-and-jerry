from __future__ import annotations

from app.store.meta import CHUNK_COLUMNS


def make_chunk_row(**overrides: object) -> dict:
    """Build a chunk dict with all CHUNK_COLUMNS keys."""
    row: dict = {
        "chunk_id": "chunk-1",
        "department": "risk",
        "vec_pos": 0,
        "doc_type": "policy",
        "title": "Test Policy",
        "url": "https://example.com/policy",
        "section": "intro",
        "last_modified": "2024-01-01",
        "lifecycle_state": "active",
        "source_type": "confluence",
        "page": 1,
        "text": "Some chunk text about escalation.",
    }
    row.update(overrides)
    assert set(row.keys()) == set(CHUNK_COLUMNS)
    return row
