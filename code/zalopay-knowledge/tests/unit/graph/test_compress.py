"""Tests for compress node and related helpers."""
from __future__ import annotations

from app.graph.nodes._helpers import render_chunks
from app.graph.state import Chunk


def _make_chunk(text: str, compressed_text: str | None = None, title: str = "Doc") -> Chunk:
    c = Chunk(
        chunk_id="c1",
        department="risk",
        doc_type="policy",
        title=title,
        url="https://example.com",
        section=None,
        last_modified=None,
        lifecycle_state="active",
        source_type="confluence",
        page=None,
        text=text,
        score=0.9,
    )
    if compressed_text is not None:
        c["compressed_text"] = compressed_text
    return c


def test_render_chunks_uses_compressed_text_when_present():
    chunk = _make_chunk(
        text="Long original text with many sentences that go on and on.",
        compressed_text="Key sentence only.",
    )
    rendered = render_chunks([chunk], start=1)
    assert "Key sentence only." in rendered
    assert "Long original text" not in rendered


def test_render_chunks_falls_back_to_text_when_no_compressed():
    chunk = _make_chunk(text="Original text here.", compressed_text=None)
    rendered = render_chunks([chunk], start=1)
    assert "Original text here." in rendered
