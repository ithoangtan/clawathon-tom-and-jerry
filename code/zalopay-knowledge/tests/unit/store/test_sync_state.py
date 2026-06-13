from __future__ import annotations

from unittest.mock import patch

from app.store.meta import MetaStore
from app.store.sync_state import (
    DepartmentSyncResult,
    SyncOrchestrator,
    SyncedContentSummary,
)

from tests.unit.store.helpers import make_chunk_row
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


class TestSyncOrchestratorLifecycle:
    def test_start_marks_source_running(self, sync_orchestrator: SyncOrchestrator) -> None:
        assert sync_orchestrator.start("confluence") is True
        assert sync_orchestrator.is_running("confluence") is True

        snapshot = sync_orchestrator.status_snapshot()
        conf = next(s for s in snapshot if s["source"] == "confluence")
        assert conf["state"] == "running"
        assert conf["progress"] == {}

    def test_start_returns_false_when_already_running(
        self, sync_orchestrator: SyncOrchestrator
    ) -> None:
        assert sync_orchestrator.start("gdrive") is True
        assert sync_orchestrator.start("gdrive") is False

    def test_finish_success_sets_idle_and_timestamp(
        self, sync_orchestrator: SyncOrchestrator
    ) -> None:
        sync_orchestrator.start("confluence")
        sync_orchestrator.finish(
            "confluence",
            success=True,
            doc_count=12,
            chunk_count=48,
        )

        assert sync_orchestrator.is_running("confluence") is False
        snapshot = sync_orchestrator.status_snapshot()
        conf = next(s for s in snapshot if s["source"] == "confluence")
        assert conf["state"] == "idle"
        assert conf["doc_count"] == 12
        assert conf["last_success_at"] is not None
        assert conf["last_success_at"].endswith("Z")
        assert conf["freshness_hours"] is not None
        assert conf["freshness_hours"] >= 0.0
        assert conf["progress"] is None

    def test_finish_failure_sets_error_state(self, sync_orchestrator: SyncOrchestrator) -> None:
        sync_orchestrator.start("gdrive")
        sync_orchestrator.finish("gdrive", success=False, error="API timeout")

        snapshot = sync_orchestrator.status_snapshot()
        gdrive = next(s for s in snapshot if s["source"] == "gdrive")
        assert gdrive["state"] == "error"
        assert "API timeout" in gdrive["errors"]

    def test_start_clears_errors_on_retry(self, sync_orchestrator: SyncOrchestrator) -> None:
        sync_orchestrator.start("gdrive")
        sync_orchestrator.finish("gdrive", success=False, error="first-error")

        sync_orchestrator.start("gdrive")
        sync_orchestrator.finish("gdrive", success=False, error="second-error")

        gdrive = next(
            s for s in sync_orchestrator.status_snapshot() if s["source"] == "gdrive"
        )
        assert gdrive["errors"] == ["second-error"]


class TestSyncOrchestratorProgress:
    def test_update_progress_while_running(self, sync_orchestrator: SyncOrchestrator) -> None:
        sync_orchestrator.start("confluence")
        sync_orchestrator.update_progress(
            "confluence", {"pages_fetched": 10, "total_pages": 100}
        )

        conf = next(
            s for s in sync_orchestrator.status_snapshot() if s["source"] == "confluence"
        )
        assert conf["progress"] == {"pages_fetched": 10, "total_pages": 100}

    def test_progress_cleared_on_finish(self, sync_orchestrator: SyncOrchestrator) -> None:
        sync_orchestrator.start("confluence")
        sync_orchestrator.update_progress("confluence", {"step": "indexing"})
        sync_orchestrator.finish("confluence", success=True, doc_count=1, chunk_count=5)

        conf = next(
            s for s in sync_orchestrator.status_snapshot() if s["source"] == "confluence"
        )
        assert conf["progress"] is None


class TestSyncOrchestratorMetaIntegration:
    def test_idle_confluence_chunk_count_from_meta(
        self, meta_store: MetaStore, sync_orchestrator: SyncOrchestrator
    ) -> None:
        meta_store.upsert_chunks(
            [
                make_chunk_row(chunk_id="c0", vec_pos=0, department=RISK),
                make_chunk_row(chunk_id="c1", vec_pos=1, department=RISK),
                make_chunk_row(chunk_id="c2", vec_pos=0, department="legal"),
            ]
        )
        sync_orchestrator.finish("confluence", success=True, doc_count=2, chunk_count=99)

        conf = next(
            s for s in sync_orchestrator.status_snapshot() if s["source"] == "confluence"
        )
        # When idle, confluence chunk_count is recomputed from meta across departments.
        assert conf["chunk_count"] == 3

    def test_gdrive_uses_stored_chunk_count(
        self, sync_orchestrator: SyncOrchestrator
    ) -> None:
        sync_orchestrator.finish("gdrive", success=True, doc_count=5, chunk_count=20)

        gdrive = next(
            s for s in sync_orchestrator.status_snapshot() if s["source"] == "gdrive"
        )
        assert gdrive["chunk_count"] == 20

    def test_freshness_hours_increases_over_time(
        self, sync_orchestrator: SyncOrchestrator
    ) -> None:
        past_iso = "2020-01-01T00:00:00Z"
        with patch("app.store.sync_state._iso_now", return_value=past_iso):
            sync_orchestrator.start("confluence")
            sync_orchestrator.finish("confluence", success=True, doc_count=1, chunk_count=1)

        conf = next(
            s for s in sync_orchestrator.status_snapshot() if s["source"] == "confluence"
        )
        assert conf["freshness_hours"] is not None
        assert conf["freshness_hours"] > 24 * 365  # more than a year old

    def test_snapshot_includes_both_default_sources(
        self, sync_orchestrator: SyncOrchestrator
    ) -> None:
        sources = {s["source"] for s in sync_orchestrator.status_snapshot()}
        assert sources == {"confluence", "gdrive"}


class TestSyncOrchestratorAdmin:
    def test_admin_status_pending_when_never_synced(
        self, sync_orchestrator: SyncOrchestrator
    ) -> None:
        snapshot = sync_orchestrator.admin_status_snapshot()
        assert snapshot["jobs"]["confluence"]["status"] == "pending"
        assert snapshot["departments_indexed"][RISK]["has_data"] is False

    def test_admin_status_running_and_department_results(
        self, sync_orchestrator: SyncOrchestrator
    ) -> None:
        sync_orchestrator.start("confluence", department=RISK)
        sync_orchestrator.record_department_result(
            "confluence",
            DepartmentSyncResult(
                department=RISK,
                space_key="RISK",
                status="running",
                page_count=0,
            ),
        )

        snapshot = sync_orchestrator.admin_status_snapshot()
        conf = snapshot["jobs"]["confluence"]
        assert conf["status"] == "running"
        assert conf["target_department"] == RISK
        assert conf["departments"][0]["department"] == RISK
        assert conf["job_id"] is not None

    def test_history_records_finished_job(self, sync_orchestrator: SyncOrchestrator) -> None:
        sync_orchestrator.start("confluence")
        sync_orchestrator.record_department_result(
            "confluence",
            DepartmentSyncResult(
                department=RISK,
                space_key="RISK",
                status="success",
                page_count=2,
                chunk_count=6,
                synced_items=[
                    SyncedContentSummary(
                        source_id="1",
                        title="Risk PRD",
                        url="https://example.com/1",
                    )
                ],
            ),
        )
        sync_orchestrator.finish("confluence", success=True, doc_count=2, chunk_count=6)

        history = sync_orchestrator.history_snapshot(limit=5)
        assert len(history) == 1
        assert history[0]["status"] == "success"
        assert history[0]["departments"][0]["synced_items"][0]["title"] == "Risk PRD"

    def test_current_job_id_while_running(self, sync_orchestrator: SyncOrchestrator) -> None:
        sync_orchestrator.start("gdrive")
        job_id = sync_orchestrator.current_job_id("gdrive")
        assert job_id is not None
        sync_orchestrator.finish("gdrive", success=True, doc_count=1, chunk_count=1)
        assert sync_orchestrator.current_job_id("gdrive") == job_id
