from __future__ import annotations

import time

import pytest

from app.config import Settings
from app.graph.state import Chunk


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        grade_threshold=0.5,
        route_confidence_min=0.55,
        topk=3,
        branch_timeout_s=20.0,
        hybrid_search_enabled=False,
        reranker_enabled=False,
    )


@pytest.fixture
def future_deadline() -> float:
    return time.time() + 3600.0


@pytest.fixture
def sample_chunk() -> Chunk:
    return Chunk(
        chunk_id="c-inject-1",
        department="risk",
        doc_type="policy",
        title="Risk Policy",
        url="https://example.com/policy",
        section="Overview",
        last_modified="2024-01-01T00:00:00Z",
        lifecycle_state="active",
        source_type="confluence",
        page=None,
        text="Baseline policy text.",
        score=0.9,
    )


@pytest.fixture
def llm_settings() -> Settings:
    return Settings(
        llm_api_key="test-key",
        small_model="small-model",
        main_model="main-model",
        llm_base_url="https://maas.example/v1",
        log_level="error",
    )


@pytest.fixture()
def ready_retriever(monkeypatch: pytest.MonkeyPatch):
    """Mark FAISS index ready for adversarial chat routes (mirrors api conftest)."""
    from unittest.mock import MagicMock

    mock_retriever = MagicMock()
    mock_retriever.is_ready.return_value = True
    mock_deps = MagicMock()
    mock_deps.retriever = mock_retriever
    monkeypatch.setattr("app.api.routes.get_deps", lambda: mock_deps)
    return mock_retriever
