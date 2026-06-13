"""Shared graph helper tests — citation projection and claim extraction."""

from __future__ import annotations

from app.graph.nodes._helpers import chunk_to_citation, extract_claims
from app.graph.state import Chunk


def test_chunk_to_citation_maps_fr2_fields(sample_chunk: Chunk):
    cite = chunk_to_citation(sample_chunk)

    assert cite["title"] == sample_chunk["title"]
    assert cite["url"] == sample_chunk["url"]
    assert cite["section"] == sample_chunk["section"]
    assert cite["last_modified"] == sample_chunk["last_modified"]
    assert cite["source_type"] == sample_chunk["source_type"]
    assert cite["page"] == sample_chunk["page"]
    assert cite["lifecycle_state"] == "active"
    assert cite["deprecated"] is False
    assert cite["successor_url"] is None
    assert cite["chunk_id"] == sample_chunk["chunk_id"]
    assert cite["excerpt"] == sample_chunk["text"]


def test_chunk_to_citation_truncates_long_excerpt():
    long_text = "word " * 200
    chunk = Chunk(
        chunk_id="long-1",
        department="risk",
        title="Policy",
        url="https://example.com/policy",
        text=long_text,
        score=0.5,
    )
    cite = chunk_to_citation(chunk)

    assert cite["excerpt"] is not None
    assert len(cite["excerpt"]) <= 400 + 1  # ellipsis char
    assert cite["excerpt"].endswith("…")


def test_chunk_to_citation_flags_deprecated_lifecycle():
    chunk = Chunk(
        chunk_id="d1",
        department="risk",
        doc_type="policy",
        title="Old Policy",
        url="https://example.com/old",
        section="Rules",
        last_modified="2023-01-01T00:00:00Z",
        lifecycle_state="deprecated",
        source_type="confluence",
        text="Old guidance.",
        score=0.7,
    )
    cite = chunk_to_citation(chunk)

    assert cite["deprecated"] is True
    assert cite["lifecycle_state"] == "deprecated"


def test_extract_claims_pairs_markers_with_chunk_text(sample_chunk: Chunk):
    claims = extract_claims("Escalation needs approval [1].", [sample_chunk])

    assert len(claims) == 1
    assert claims[0]["claim"] == "Escalation needs approval [1]."
    assert claims[0]["cited"] == [1]
    assert sample_chunk["text"] in claims[0]["source_text"]
