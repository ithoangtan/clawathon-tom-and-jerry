from __future__ import annotations

from app.ingestion.sync_hash import page_content_hash, resolve_document_chunks
from app.store.meta import MetaStore

from tests.unit.store.helpers import make_chunk_row


def test_page_content_hash_normalizes_whitespace() -> None:
    assert page_content_hash("  hello world  ") == page_content_hash("hello world")


def test_resolve_document_chunks_reuses_when_hash_matches(meta_store: MetaStore) -> None:
    url = "https://example.com/policy"
    text = "Stable policy body for hash skip."
    digest = page_content_hash(text)
    rows = [
        make_chunk_row(chunk_id="c0", vec_pos=0, url=url, text="chunk one"),
        make_chunk_row(chunk_id="c1", vec_pos=1, url=url, text="chunk two"),
    ]
    meta_store.upsert_chunks(rows)
    meta_store.record_source_hashes(
        "risk",
        [{"url": url, "source_id": "1", "content_hash": digest, "last_modified": None}],
    )

    called = {"count": 0}

    def builder() -> list[dict]:
        called["count"] += 1
        return [{"chunk_id": "new"}]

    chunks, skipped = resolve_document_chunks(
        department="risk",
        url=url,
        text=text,
        meta=meta_store,
        chunk_builder=builder,
    )

    assert skipped is True
    assert called["count"] == 0
    assert len(chunks) == 2
    assert chunks[0]["chunk_id"] == "c0"


def test_resolve_document_chunks_rechunks_when_hash_differs(meta_store: MetaStore) -> None:
    url = "https://example.com/policy"
    meta_store.record_source_hashes(
        "risk",
        [
            {
                "url": url,
                "source_id": "1",
                "content_hash": page_content_hash("old body"),
                "last_modified": None,
            }
        ],
    )

    new_chunks = [{"chunk_id": "fresh", "url": url, "text": "updated"}]
    chunks, skipped = resolve_document_chunks(
        department="risk",
        url=url,
        text="updated body",
        meta=meta_store,
        chunk_builder=lambda: new_chunks,
    )

    assert skipped is False
    assert chunks == new_chunks
