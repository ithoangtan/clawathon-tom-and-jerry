from __future__ import annotations

from app.api.context import parse_context_from_headers, require_user_context
from app.common.pii import mask_pii
from app.ingestion.chunker import chunk_text


def test_mask_pii_email():
    assert "[email]" in mask_pii("Contact alice@example.com please")


def test_chunk_text_produces_rows():
    chunks = chunk_text(
        "Introduction\n\nThis is a policy document about risk escalation.",
        department="risk",
        doc_type="policy",
        title="Escalation Policy",
        url="https://example.com/policy",
    )
    assert len(chunks) >= 1
    assert chunks[0]["department"] == "risk"
    assert chunks[0]["text"]


def test_parse_context_from_headers():
    ctx = parse_context_from_headers(
        {
            "X-GreenNode-AgentBase-User-Id": "u1",
            "X-GreenNode-AgentBase-Session-Id": "s1",
            "X-GreenNode-AgentBase-Role": "engineer",
        }
    )
    assert ctx.user_id == "u1"
    assert ctx.role == "engineer"
