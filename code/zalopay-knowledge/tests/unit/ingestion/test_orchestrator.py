from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.ingestion.orchestrator import SyncService, _chunk_urls
from app.store.meta import MetaStore


@pytest.fixture
def sync_settings(tmp_path: Path) -> Settings:
    return Settings(
        confluence_base_url="https://acme.atlassian.net",
        confluence_email="bot@example.com",
        confluence_api_token="secret-token",
        confluence_space_risk="RISK",
        index_dir=str(tmp_path / "index"),
    )


@pytest.fixture
def sync_service(sync_settings: Settings):
    """Build SyncService with graph deps stubbed to avoid circular imports."""
    saved = {
        key: sys.modules.get(key)
        for key in ("app.graph", "app.graph.build", "app.adapters", "app.adapters.deps")
    }
    graph_build = ModuleType("app.graph.build")
    graph_build.GraphDeps = type("GraphDeps", (), {})
    graph_pkg = ModuleType("app.graph")
    graph_pkg.__path__ = []  # type: ignore[attr-defined]
    sys.modules["app.graph"] = graph_pkg
    sys.modules["app.graph.build"] = graph_build
    for key in ("app.adapters.deps", "app.adapters", "app.ingestion.indexer"):
        sys.modules.pop(key, None)

    svc = SyncService(sync_settings)

    yield svc

    for key, module in saved.items():
        if module is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = module


class TestChunkUrls:
    def test_collects_unique_urls(self):
        chunks = [
            {"url": "https://example.com/a"},
            {"url": "https://example.com/a"},
            {"url": "https://example.com/b"},
        ]
        assert _chunk_urls(chunks) == {
            "https://example.com/a",
            "https://example.com/b",
        }


class TestSyncServiceConfluence:
    def test_confluence_sync_indexes_pages(
        self,
        sync_service: SyncService,
        sync_settings: Settings,
        mock_encode_passages,
        sample_text: str,
    ):
        pages = [
            {"id": "1", "title": "Risk PRD"},
            {"id": "2", "title": "On-call runbook"},
        ]

        def fetch_body(page_id: str):
            return sample_text, {
                "title": f"Page {page_id}",
                "url": f"https://acme.atlassian.net/wiki/pages/{page_id}",
                "last_modified": "2025-01-15T10:00:00Z",
            }

        with (
            patch.object(sync_service._confluence, "configured", return_value=True),
            patch.object(sync_service._confluence, "list_pages", return_value=pages),
            patch.object(sync_service._confluence, "fetch_page_body", side_effect=fetch_body),
            patch.object(
                sync_service._indexer._embedder,
                "encode_passages",
                side_effect=mock_encode_passages,
            ),
            patch.object(sync_service._indexer, "reload_retriever"),
        ):
            sync_service._run_confluence()

        meta = MetaStore(Path(sync_settings.index_dir) / "meta.db")
        assert meta.count("risk") >= 2
        assert meta.doc_count("risk") == 2

        snapshot = sync_service.orchestrator.status_snapshot()
        confluence = next(s for s in snapshot if s["source"] == "confluence")
        assert confluence["state"] == "idle"
        assert confluence["doc_count"] == 2
        assert confluence["chunk_count"] >= 2

    def test_confluence_sync_tombstones_removed_urls_before_rebuild(
        self,
        sync_service: SyncService,
        sync_settings: Settings,
        mock_encode_passages,
        sample_text: str,
    ):
        """FR-5.2: absent URLs are tombstoned before department rebuild."""
        pages = [{"id": "1", "title": "Keep"}]

        def fetch_body(page_id: str):
            return sample_text, {
                "title": f"Page {page_id}",
                "url": f"https://acme.atlassian.net/wiki/pages/{page_id}",
                "last_modified": "2025-01-15T10:00:00Z",
            }

        with (
            patch.object(sync_service._confluence, "configured", return_value=True),
            patch.object(sync_service._confluence, "list_pages", return_value=pages),
            patch.object(sync_service._confluence, "fetch_page_body", side_effect=fetch_body),
            patch.object(
                sync_service._indexer._embedder,
                "encode_passages",
                side_effect=mock_encode_passages,
            ),
            patch.object(sync_service._indexer, "reload_retriever"),
            patch.object(
                sync_service._indexer,
                "tombstone_removed_urls",
                return_value={"https://acme.atlassian.net/wiki/pages/99"},
            ) as mock_tombstone,
            patch.object(sync_service._indexer, "rebuild_department") as mock_rebuild,
        ):
            sync_service._run_confluence()

        mock_tombstone.assert_called()
        assert mock_rebuild.called
        tombstone_urls = mock_tombstone.call_args[0][1]
        assert "https://acme.atlassian.net/wiki/pages/1" in tombstone_urls

    def test_confluence_sync_removes_deleted_pages_on_rebuild(
        self,
        sync_service: SyncService,
        sync_settings: Settings,
        mock_encode_passages,
        sample_text: str,
    ):
        """Second sync with fewer pages drops chunks for removed URLs."""
        all_pages = [
            {"id": "1", "title": "Keep"},
            {"id": "2", "title": "Remove me"},
        ]

        def fetch_body(page_id: str):
            return sample_text, {
                "title": f"Page {page_id}",
                "url": f"https://acme.atlassian.net/wiki/pages/{page_id}",
                "last_modified": "2025-01-15T10:00:00Z",
            }

        with (
            patch.object(sync_service._confluence, "configured", return_value=True),
            patch.object(sync_service._confluence, "list_pages", return_value=all_pages),
            patch.object(sync_service._confluence, "fetch_page_body", side_effect=fetch_body),
            patch.object(
                sync_service._indexer._embedder,
                "encode_passages",
                side_effect=mock_encode_passages,
            ),
            patch.object(sync_service._indexer, "reload_retriever"),
        ):
            sync_service._run_confluence()

        meta = MetaStore(Path(sync_settings.index_dir) / "meta.db")
        assert meta.distinct_urls("risk") == {
            "https://acme.atlassian.net/wiki/pages/1",
            "https://acme.atlassian.net/wiki/pages/2",
        }

        with (
            patch.object(sync_service._confluence, "configured", return_value=True),
            patch.object(
                sync_service._confluence,
                "list_pages",
                return_value=[all_pages[0]],
            ),
            patch.object(sync_service._confluence, "fetch_page_body", side_effect=fetch_body),
            patch.object(
                sync_service._indexer._embedder,
                "encode_passages",
                side_effect=mock_encode_passages,
            ),
            patch.object(sync_service._indexer, "reload_retriever"),
        ):
            sync_service._run_confluence()

        assert meta.distinct_urls("risk") == {
            "https://acme.atlassian.net/wiki/pages/1",
        }
        assert meta.doc_count("risk") == 1

    def test_confluence_not_configured_sets_error(self, sync_service: SyncService):
        with patch.object(sync_service._confluence, "configured", return_value=False):
            sync_service._run_confluence()

        snapshot = sync_service.orchestrator.status_snapshot()
        confluence = next(s for s in snapshot if s["source"] == "confluence")
        assert confluence["state"] == "error"
        assert confluence["errors"]


class TestSyncServiceTriggers:
    def test_trigger_confluence_starts_background_thread(self, sync_service: SyncService):
        with patch.object(sync_service, "_run_confluence") as mock_run:
            started = sync_service.trigger_confluence()
            assert started is True
            assert sync_service.orchestrator.is_running("confluence")
            # Thread runs async — wait briefly for the target to be invoked.
            import time

            for _ in range(20):
                if mock_run.called:
                    break
                time.sleep(0.05)
            assert mock_run.called

    def test_trigger_confluence_conflict_when_running(self, sync_service: SyncService):
        sync_service.orchestrator.start("confluence")
        assert sync_service.trigger_confluence() is False
