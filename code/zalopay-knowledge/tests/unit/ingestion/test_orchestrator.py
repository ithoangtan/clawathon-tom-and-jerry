from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.ingestion.metadata import REQUIRED_CHUNK_METADATA_FIELDS
from app.ingestion.orchestrator import SyncService, _chunk_urls
from app.store.meta import MetaStore
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


@pytest.fixture
def sync_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        confluence_base_url="https://acme.atlassian.net",
        confluence_email="bot@example.com",
        confluence_api_token="secret-token",
        confluence_spaces={RISK:  "RISK"},
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
        assert meta.count(RISK) >= 2
        assert meta.doc_count(RISK) == 2

        snapshot = sync_service.orchestrator.status_snapshot()
        confluence = next(s for s in snapshot if s["source"] == "confluence")
        assert confluence["state"] == "idle"
        assert confluence["doc_count"] == 2
        assert confluence["chunk_count"] >= 2

    def test_confluence_sync_persists_required_metadata_fields(
        self,
        sync_service: SyncService,
        sync_settings: Settings,
        mock_encode_passages,
        sample_text: str,
    ):
        """Checklist §4: sync → index path retains the full chunk metadata contract."""
        pages = [
            {"id": "1", "title": "Q1 Product PRD"},
            {"id": "2", "title": "Settlement runbook"},
        ]

        def fetch_body(page_id: str):
            return sample_text, {
                "title": next(p["title"] for p in pages if p["id"] == page_id),
                "url": f"https://acme.atlassian.net/wiki/pages/{page_id}",
                "last_modified": "2025-01-15T10:00:00Z",
                "author": "owner@example.com",
                "labels": ["policy"],
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
        rows = meta.fetch_by_positions(RISK, list(range(meta.count(RISK))))
        assert rows

        doc_types = set()
        for row in rows.values():
            for field in REQUIRED_CHUNK_METADATA_FIELDS:
                assert field in row, f"missing {field} on indexed chunk"
            assert row["source"] in {"1", "2"}
            assert row["space"] == "RISK"
            assert row["author"] == "owner@example.com"
            assert row["last_modified"] == "2025-01-15T10:00:00Z"
            assert row["acl"]  # JSON placeholder present even when unused in MVP
            doc_types.add(row["doc_type"])

        assert "PRD" in doc_types
        assert "Operation" in doc_types

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
        assert meta.distinct_urls(RISK) == {
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

        assert meta.distinct_urls(RISK) == {
            "https://acme.atlassian.net/wiki/pages/1",
        }
        assert meta.doc_count(RISK) == 1

    def test_confluence_sync_skips_unchanged_pages_on_rerun(
        self,
        sync_service: SyncService,
        sync_settings: Settings,
        mock_encode_passages,
        sample_text: str,
    ):
        """G4: second sync with identical bodies reuses chunks (hash-skip)."""
        pages = [{"id": "1", "title": "Stable page"}]
        page_url = "https://acme.atlassian.net/wiki/pages/1"

        def fetch_body(page_id: str):
            return sample_text, {
                "title": "Stable page",
                "url": page_url,
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
            patch("app.ingestion.orchestrator.chunk_text") as mock_chunk_text,
        ):
            sync_service._run_confluence()
            assert mock_chunk_text.call_count == 0

    def test_confluence_not_configured_sets_error(self, sync_service: SyncService):
        with patch.object(sync_service._confluence, "configured", return_value=False):
            sync_service._run_confluence()

        snapshot = sync_service.orchestrator.status_snapshot()
        confluence = next(s for s in snapshot if s["source"] == "confluence")
        assert confluence["state"] == "error"
        assert confluence["errors"]


class TestSyncServiceTriggers:
    def test_trigger_confluence_rejects_unconfigured_department(
        self,
        sync_service: SyncService,
    ):
        with pytest.raises(ValueError, match="CONFLUENCE_SPACES"):
            sync_service.trigger_confluence(department=GROW)

    def test_trigger_confluence_accepts_configured_department(
        self,
        sync_settings: Settings,
    ):
        settings = sync_settings.model_copy(
            update={"confluence_spaces": {RISK:  "RISK", GROW: "GROW"}},
        )
        svc = SyncService(settings)
        with patch.object(svc, "_run_confluence"):
            assert svc.trigger_confluence(department=GROW) is True

    def test_confluence_sync_only_target_department_space(
        self,
        sync_settings: Settings,
        mock_encode_passages,
        sample_text: str,
    ):
        """Department-scoped sync must not list or rebuild other departments."""
        settings = sync_settings.model_copy(
            update={
                "confluence_spaces": {
                    RISK: "RISK",
                    GROW: "GROW",
                    BANK: "BANK",
                },
            },
        )
        svc = SyncService(settings)
        pages = [{"id": "g1", "title": "Grow playbook"}]

        def fetch_body(page_id: str):
            return sample_text, {
                "title": "Grow playbook",
                "url": f"https://acme.atlassian.net/wiki/pages/{page_id}",
                "last_modified": "2025-01-15T10:00:00Z",
            }

        with (
            patch.object(svc._confluence, "configured", return_value=True),
            patch.object(svc._confluence, "list_pages", return_value=pages) as mock_list,
            patch.object(svc._confluence, "fetch_page_body", side_effect=fetch_body),
            patch.object(
                svc._indexer._embedder,
                "encode_passages",
                side_effect=mock_encode_passages,
            ),
            patch.object(svc._indexer, "reload_retriever"),
            patch.object(svc._indexer, "rebuild_department") as mock_rebuild,
        ):
            svc._run_confluence(department=GROW)

        mock_list.assert_called_once_with("GROW")
        mock_rebuild.assert_called_once()
        assert mock_rebuild.call_args[0][0] == GROW

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

    def test_confluence_sync_is_idempotent(
        self,
        sync_service: SyncService,
        sync_settings: Settings,
        mock_encode_passages,
        sample_text: str,
    ):
        """Re-running sync with the same corpus yields stable index state."""
        pages = [{"id": "1", "title": "Risk PRD"}]

        def fetch_body(page_id: str):
            return sample_text, {
                "title": f"Page {page_id}",
                "url": f"https://acme.atlassian.net/wiki/pages/{page_id}",
                "last_modified": "2025-01-15T10:00:00Z",
            }

        patches = (
            patch.object(sync_service._confluence, "configured", return_value=True),
            patch.object(sync_service._confluence, "list_pages", return_value=pages),
            patch.object(sync_service._confluence, "fetch_page_body", side_effect=fetch_body),
            patch.object(
                sync_service._indexer._embedder,
                "encode_passages",
                side_effect=mock_encode_passages,
            ),
            patch.object(sync_service._indexer, "reload_retriever"),
        )

        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            sync_service._run_confluence()
        meta = MetaStore(Path(sync_settings.index_dir) / "meta.db")
        first_count = meta.count(RISK)
        first_urls = meta.distinct_urls(RISK)

        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            sync_service._run_confluence()

        assert meta.count(RISK) == first_count
        assert meta.distinct_urls(RISK) == first_urls

    def test_confluence_sync_never_calls_llm(
        self,
        sync_service: SyncService,
        mock_encode_passages,
        sample_text: str,
    ):
        """G4: ingestion uses local embeddings only — zero MaaS tokens on sync."""
        pages = [{"id": "1", "title": "Risk PRD"}]

        def fetch_body(page_id: str):
            return sample_text, {
                "title": f"Page {page_id}",
                "url": f"https://acme.atlassian.net/wiki/pages/{page_id}",
                "last_modified": "2025-01-15T10:00:00Z",
            }

        mock_llm = MagicMock()
        mock_llm.complete = MagicMock(side_effect=AssertionError("LLM must not run during sync"))

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
            patch("app.adapters.deps.get_deps") as mock_get_deps,
        ):
            mock_get_deps.return_value.llm = mock_llm
            sync_service._run_confluence()

        mock_llm.complete.assert_not_called()
