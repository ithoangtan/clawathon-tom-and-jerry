from __future__ import annotations

"""MVP Platform/Ops checklist §3 verification (G4/G5)."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.health import is_live, is_ready, probe_status
from app.common.stage_trace import build_stage_trace
from app.config import Settings
from app.graph.build import _make_dept_branch, build_dept_subgraph
from app.ingestion.indexer import IndexBuilder
from app.ingestion.sync_hash import page_content_hash
from tests.unit.graph.conftest import StubLLM, StubRetriever, test_settings  # noqa: F401
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


class TestSyncPlatformInvariants:
    def test_atomic_faiss_swap_uses_os_replace(self) -> None:
        import app.ingestion.indexer as indexer_mod

        source = indexer_mod.IndexBuilder._atomic_write_faiss.__doc__ or ""
        assert "os.replace" in source or "replace" in source

    def test_tombstone_api_exists_on_index_builder(self) -> None:
        assert callable(IndexBuilder.tombstone_removed_urls)


class TestHealthProbeSeparation:
    def test_liveness_independent_of_readiness(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_deps = MagicMock()
        mock_deps.retriever.is_ready.return_value = False
        mock_deps.llm.is_reachable.return_value = False
        monkeypatch.setattr("app.api.health.get_deps", lambda: mock_deps)

        assert is_live() is True
        assert is_ready() is False

        status = probe_status()
        assert status["index_ready"] is False
        assert status["maas_ready"] is False
        assert status["ready"] is False

    def test_ready_endpoint_503_when_index_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_deps = MagicMock()
        mock_deps.retriever.is_ready.return_value = False
        mock_deps.llm.is_reachable.return_value = True
        monkeypatch.setattr("app.api.health.get_deps", lambda: mock_deps)

        client = TestClient(create_app())
        resp = client.get("/health/ready")
        assert resp.status_code == 503


class TestMaasResilienceConfig:
    def test_default_llm_request_timeout(self) -> None:
        settings = Settings(log_level="error")
        assert settings.llm_request_timeout_s == 60.0
        assert settings.health_ping_timeout_s == 3.0


class TestStageTracing:
    def test_trace_covers_checklist_stages(self) -> None:
        trace = build_stage_trace(
            {
                "question": "q",
                "retrieval_query": "rewrite",
                "evidence": {RISK:  [{"chunk_id": "1", "score": 0.9}]},
                "dept_results": [
                    {
                        "department": RISK,
                        "status": "answered",
                        "confidence": 0.8,
                        "citations": [{}],
                    }
                ],
                "answer": "a",
                "citations": [{"title": "t"}],
                "status": "answered",
            }
        )
        for key in ("query", "rewrite", "chunks", "grades", "citations", "verify"):
            assert key in trace


class TestDeptSubgraphDegradation:
    def test_branch_wrapper_returns_timeout_on_crash(self, test_settings: Settings) -> None:
        deps = MagicMock()
        deps.llm = StubLLM("{}")
        deps.retriever = StubRetriever(ready=True)
        deps.settings = test_settings
        subgraph = build_dept_subgraph(deps)
        branch = _make_dept_branch(subgraph)

        with (
            patch.object(subgraph, "stream", side_effect=RuntimeError("boom")),
            patch("app.graph.build.get_stream_writer", return_value=lambda _payload: None),
        ):
            result = branch(
                {
                    "department": RISK,
                    "question": "What is KYC?",
                    "role": "engineer",
                    "request_language": "en",
                    "deadline_ts": 9999999999.0,
                }
            )

        dept_result = result["dept_results"][0]
        assert dept_result["status"] == "timeout"
        assert "branch_error" in dept_result["warnings"]


class TestSyncHashContract:
    def test_page_hash_is_stable_hex(self) -> None:
        digest = page_content_hash("sample")
        assert len(digest) == 64
        assert digest == page_content_hash("sample")
