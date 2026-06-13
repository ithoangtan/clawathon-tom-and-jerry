"""Tests for compress node and related helpers."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

from app.config import Settings
from app.graph.build import GraphDeps, build_dept_subgraph
from app.graph.nodes._helpers import render_chunks
from app.graph.state import Chunk
from app.ports.errors import LLMUnavailable
from app.ports.types import LLMResult, ModelTier
from app.ports.types import RetrievedChunk


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


# ── Smoke test: full dept subgraph end-to-end with compress enabled ───────────

def _make_smart_llm() -> MagicMock:
    """Return a MagicMock LLM that routes responses by tier and system prompt content."""

    def _complete(
        *,
        tier: ModelTier,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        response_format: str = "text",
        timeout_s: float | None = None,
    ) -> LLMResult:
        system_content = ""
        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content", "").lower()
                break

        # Grade call: SMALL tier, system prompt mentions "relevance grader"
        if tier == ModelTier.SMALL and "relevance grader" in system_content:
            return LLMResult(
                text='{"scores": [{"id": 0, "score": 0.9, "reason": "direct match"}]}',
                raw={},
                usage={},
            )

        # Compress call: SMALL tier, system prompt mentions "document compressor"
        if tier == ModelTier.SMALL and "document compressor" in system_content:
            return LLMResult(
                text='{"compressed": "Key sentence."}',
                raw={},
                usage={},
            )

        # Verify call: SMALL tier, system prompt mentions "entailment verifier"
        if tier == ModelTier.SMALL and "entailment verifier" in system_content:
            return LLMResult(
                text='{"verdict": "supported", "confidence": 0.9, "warnings": []}',
                raw={},
                usage={},
            )

        # Synthesize call: MAIN tier
        if tier == ModelTier.MAIN:
            return LLMResult(
                text="The KYC process requires three steps [1].",
                raw={},
                usage={},
            )

        # Fallback: return empty JSON so nodes degrade gracefully
        return LLMResult(text="{}", raw={}, usage={})

    llm = MagicMock()
    llm.complete.side_effect = _complete
    return llm


class _StubRetriever:
    """Minimal retriever stub that returns one long chunk."""

    def __init__(self, text: str) -> None:
        self._text = text

    def is_ready(self) -> bool:
        return True

    def search(self, **_kwargs) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                chunk_id="smoke-c1",
                department="risk",
                doc_type="policy",
                title="KYC Policy",
                url="https://example.com/kyc",
                section="Overview",
                last_modified="2024-01-01T00:00:00Z",
                lifecycle_state="active",
                source_type="confluence",
                page=None,
                text=self._text,
                score=0.88,
            )
        ]


def test_smoke_dept_subgraph_end_to_end_with_compress_enabled():
    """Smoke test: full retrieve→grade→compress→synthesize→verify pipeline.

    Verifies that:
    - The subgraph completes without error with compress_enabled=True.
    - dept_results is present in the output with status "answered" or "refused".
    - The compress node had an opportunity to run (long chunk >150 chars provided).
    """
    long_text = (
        "The KYC process requires three steps. "
        "First, the merchant submits identity documents. "
        "Second, the compliance team reviews within 48 hours. "
        "Third, a risk score is calculated based on transaction history. "
        "Merchants with a score below 30 are auto-approved. "
        "All records are stored for 7 years per regulation."
    )
    assert len(long_text) > 150, "fixture text must exceed compress threshold"

    settings = _settings(compress_enabled=True)
    deps = GraphDeps(
        llm=_make_smart_llm(),
        retriever=_StubRetriever(long_text),
        settings=settings,
    )
    subgraph = build_dept_subgraph(deps)

    result = subgraph.invoke(
        {
            "department": "risk",
            "question": "How many steps does KYC have?",
            "retrieval_query": "KYC steps",
            "role": "engineer",
            "request_language": "en",
            "home_department": "risk",
            "deadline_ts": time.time() + 60.0,
        }
    )

    dept_results = result.get("dept_results", [])
    assert dept_results, "dept_results must be non-empty"
    assert dept_results[0]["status"] in ("answered", "refused"), (
        f"Unexpected status: {dept_results[0]['status']}"
    )
