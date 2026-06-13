"""Tests for compress node and related helpers."""
from __future__ import annotations

from unittest.mock import MagicMock

from app.config import Settings
from app.graph.nodes._helpers import render_chunks
from app.graph.state import Chunk
from app.ports.errors import LLMUnavailable
from app.ports.types import LLMResult, ModelTier


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


# ── Node tests ────────────────────────────────────────────────────────────────

def _settings(compress_enabled: bool = True, branch_timeout_s: float = 20.0) -> Settings:
    return Settings(
        compress_enabled=compress_enabled,
        branch_timeout_s=branch_timeout_s,
        llm_base_url="https://unused.example.com",
        llm_api_key="test-key",
        small_model="test-small",
        main_model="test-main",
    )


def _stub_llm(compressed: str) -> MagicMock:
    llm = MagicMock()
    llm.complete.return_value = LLMResult(
        text=f'{{"compressed": "{compressed}"}}',
        raw={},
        usage={},
    )
    return llm


def _long_chunk(text: str = None, chunk_id: str = "c1") -> Chunk:
    if text is None:
        text = (
            "The KYC process requires three steps. "
            "First, the merchant submits identity documents. "
            "Second, the compliance team reviews within 48 hours. "
            "Third, a risk score is calculated based on transaction history. "
            "Merchants with a score below 30 are auto-approved. "
            "All records are stored for 7 years per regulation."
        )
    return _make_chunk(text=text, title="KYC Policy", compressed_text=None)


def test_compress_node_adds_compressed_text_to_long_chunks():
    from app.graph.nodes.compress import make_compress_node
    llm = _stub_llm("The KYC process requires three steps.")
    node = make_compress_node(llm, settings=_settings())
    state = {
        "department": "risk",
        "question": "How many steps does KYC have?",
        "retrieval_query": "KYC steps",
        "graded_chunks": [_long_chunk()],
        "deadline_ts": None,
    }
    result = node(state)
    chunks = result["graded_chunks"]
    assert len(chunks) == 1
    assert chunks[0]["compressed_text"] == "The KYC process requires three steps."
    assert chunks[0]["text"] == _long_chunk()["text"]  # original preserved


def test_compress_node_skips_short_chunks():
    from app.graph.nodes.compress import make_compress_node
    llm = _stub_llm("irrelevant")
    node = make_compress_node(llm, settings=_settings())
    short_text = "Short chunk."
    state = {
        "department": "risk",
        "question": "anything",
        "retrieval_query": "anything",
        "graded_chunks": [_make_chunk(text=short_text)],
        "deadline_ts": None,
    }
    result = node(state)
    chunks = result["graded_chunks"]
    assert "compressed_text" not in chunks[0]
    llm.complete.assert_not_called()


def test_compress_node_disabled_returns_empty_dict():
    from app.graph.nodes.compress import make_compress_node
    llm = _stub_llm("compressed")
    node = make_compress_node(llm, settings=_settings(compress_enabled=False))
    state = {
        "department": "risk",
        "question": "anything",
        "retrieval_query": "anything",
        "graded_chunks": [_long_chunk()],
        "deadline_ts": None,
    }
    result = node(state)
    assert result == {}
    llm.complete.assert_not_called()


def test_compress_node_returns_empty_dict_on_budget_exceeded():
    from app.graph.nodes.compress import make_compress_node
    llm = _stub_llm("compressed")
    node = make_compress_node(llm, settings=_settings())
    state = {
        "department": "risk",
        "question": "anything",
        "retrieval_query": "anything",
        "graded_chunks": [_long_chunk()],
        "deadline_ts": 0.0,  # already expired
    }
    result = node(state)
    assert result == {}
    llm.complete.assert_not_called()


def test_compress_node_falls_back_to_original_on_llm_error():
    from app.graph.nodes.compress import make_compress_node
    llm = MagicMock()
    llm.complete.side_effect = LLMUnavailable("MaaS down")
    node = make_compress_node(llm, settings=_settings())
    original_text = _long_chunk()["text"]
    state = {
        "department": "risk",
        "question": "KYC steps",
        "retrieval_query": "KYC steps",
        "graded_chunks": [_long_chunk()],
        "deadline_ts": None,
    }
    result = node(state)
    chunks = result["graded_chunks"]
    assert "compressed_text" not in chunks[0]
    assert chunks[0]["text"] == original_text


def test_compress_node_does_not_store_if_compressed_longer_than_original():
    from app.graph.nodes.compress import make_compress_node
    long_response = ("A word " * 500).strip()
    llm = _stub_llm(long_response)
    node = make_compress_node(llm, settings=_settings())
    state = {
        "department": "risk",
        "question": "KYC",
        "retrieval_query": "KYC",
        "graded_chunks": [_long_chunk()],
        "deadline_ts": None,
    }
    result = node(state)
    chunks = result["graded_chunks"]
    assert "compressed_text" not in chunks[0]
