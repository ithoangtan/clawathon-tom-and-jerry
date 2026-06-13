from __future__ import annotations

import time
from typing import Any, Callable

import pytest

from app.config import Settings
from app.graph.build import GraphDeps
from app.graph.state import Chunk, Citation, DeptResult
from app.ports.errors import LLMUnavailable, RetrieverUnavailable
from app.ports.types import LLMResult, RetrievedChunk


class StubLLM:
    """Configurable LLM port stub — records calls, never hits the network."""

    def __init__(
        self,
        text: str = "{}",
        *,
        side_effect: Exception | Callable[..., LLMResult] | None = None,
    ) -> None:
        self._text = text
        self._side_effect = side_effect
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> LLMResult:
        self.calls.append(kwargs)
        if isinstance(self._side_effect, Exception):
            raise self._side_effect
        if callable(self._side_effect):
            return self._side_effect(**kwargs)
        return LLMResult(text=self._text, raw={}, usage={})


class StubRetriever:
    """Configurable retriever port stub."""

    def __init__(
        self,
        *,
        chunks: list[RetrievedChunk] | None = None,
        ready: bool = True,
        search_raises: Exception | None = None,
    ) -> None:
        self._chunks = list(chunks or [])
        self._ready = ready
        self._search_raises = search_raises
        self.search_calls: list[dict[str, Any]] = []

    def is_ready(self) -> bool:
        if not self._ready:
            raise RetrieverUnavailable()
        return True

    def search(self, **kwargs: Any) -> list[RetrievedChunk]:
        self.search_calls.append(kwargs)
        if self._search_raises:
            raise self._search_raises
        return list(self._chunks)


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        grade_threshold=0.5,
        route_confidence_min=0.55,
        topk=3,
        branch_timeout_s=20.0,
    )


@pytest.fixture
def graph_deps(test_settings: Settings) -> GraphDeps:
    return GraphDeps(
        llm=StubLLM(),
        retriever=StubRetriever(),
        settings=test_settings,
    )


@pytest.fixture
def future_deadline() -> float:
    """Deadline far enough in the future that budget guards do not trip."""
    return time.time() + 3600.0


@pytest.fixture
def past_deadline() -> float:
    return time.time() - 1.0


@pytest.fixture
def sample_retrieved_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c1",
        department="risk",
        doc_type="policy",
        title="Escalation Policy",
        url="https://example.com/policy",
        section="Overview",
        last_modified="2024-01-01T00:00:00Z",
        lifecycle_state="active",
        source_type="confluence",
        page=None,
        text="Risk escalation requires manager approval within 24 hours.",
        score=0.85,
    )


@pytest.fixture
def sample_chunk(sample_retrieved_chunk: RetrievedChunk) -> Chunk:
    return Chunk(
        chunk_id=sample_retrieved_chunk.chunk_id,
        department=sample_retrieved_chunk.department,
        doc_type=sample_retrieved_chunk.doc_type,
        title=sample_retrieved_chunk.title,
        url=sample_retrieved_chunk.url,
        section=sample_retrieved_chunk.section,
        last_modified=sample_retrieved_chunk.last_modified,
        lifecycle_state=sample_retrieved_chunk.lifecycle_state,
        source_type=sample_retrieved_chunk.source_type,
        page=sample_retrieved_chunk.page,
        text=sample_retrieved_chunk.text,
        score=sample_retrieved_chunk.score,
    )


@pytest.fixture
def sample_citation() -> Citation:
    return Citation(
        title="Escalation Policy",
        url="https://example.com/policy",
        section="Overview",
        last_modified="2024-01-01T00:00:00Z",
        lifecycle_state="active",
        deprecated=False,
        successor_url=None,
        source_type="confluence",
        page=None,
    )


@pytest.fixture
def answered_dept_result(sample_citation: Citation) -> DeptResult:
    return DeptResult(
        department="risk",
        status="answered",
        answer="Escalation requires approval [1].",
        citations=[sample_citation],
        confidence=0.8,
        warnings=[],
    )
