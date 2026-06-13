from __future__ import annotations

from app.ingestion.metadata import serialize_acl, serialize_labels
from app.store.meta import CHUNK_COLUMNS


def make_chunk_row(**overrides: object) -> dict:
    """Build a chunk dict with all CHUNK_COLUMNS keys."""
    row: dict = {
        "chunk_id": "chunk-1",
        "department": "risk",
        "vec_pos": 0,
        "doc_type": "Risk",
        "title": "Test Policy",
        "source": "12345",
        "url": "https://example.com/policy",
        "anchor": "intro",
        "section": "intro",
        "space": "RISK",
        "labels": serialize_labels(["policy"]),
        "last_modified": "2024-01-01",
        "author": "risk.owner@zalopay.vn",
        "acl": serialize_acl(None),
        "lifecycle_state": "active",
        "source_type": "confluence",
        "page": None,
        "text": "Some chunk text about escalation.",
    }
    row.update(overrides)
    if "labels" in overrides and not isinstance(row["labels"], str):
        row["labels"] = serialize_labels(row["labels"])  # type: ignore[arg-type]
    if "acl" in overrides and not isinstance(row["acl"], str):
        row["acl"] = serialize_acl(row["acl"])  # type: ignore[arg-type]
    assert set(row.keys()) == set(CHUNK_COLUMNS)
    return row
