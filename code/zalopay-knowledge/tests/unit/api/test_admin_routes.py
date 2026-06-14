from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from tests.unit.api.conftest import AUTH_HEADERS
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


class TestAdminSyncRoutes:
    def test_admin_sync_requires_auth(self, client: TestClient) -> None:
        resp = client.post("/api/admin/sync", json={"source": "confluence"})
        assert resp.status_code == 400

    def test_admin_sync_confluence_starts_job(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.trigger_confluence.return_value = True
        mock_svc.orchestrator.current_job_id.return_value = "job-123"
        monkeypatch.setattr("app.api.admin_routes.get_sync_service", lambda: mock_svc)

        resp = client.post(
            "/api/admin/sync",
            json={"source": "confluence"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["source"] == "confluence"
        assert body["started"] is True
        assert body["job_id"] == "job-123"
        mock_svc.trigger_confluence.assert_called_once_with(department=None)

    def test_admin_sync_confluence_department_filter(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.trigger_confluence.return_value = True
        mock_svc.orchestrator.current_job_id.return_value = "job-risk"
        monkeypatch.setattr("app.api.admin_routes.get_sync_service", lambda: mock_svc)

        resp = client.post(
            "/api/admin/sync",
            json={"source": "confluence", "department": RISK},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["department"] == RISK
        mock_svc.trigger_confluence.assert_called_once_with(department=RISK)

    def test_admin_sync_confluence_rejects_unconfigured_department(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.trigger_confluence.side_effect = ValueError(
            "Department GROW has no Confluence space configured. "
            "Set CONFLUENCE_SPACES JSON (key GROW) or "
            "CONFLUENCE_SPACE_GROW=<space-key> in your environment to enable sync "
            "for this department."
        )
        monkeypatch.setattr("app.api.admin_routes.get_sync_service", lambda: mock_svc)

        resp = client.post(
            "/api/admin/sync",
            json={"source": "confluence", "department": GROW},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 400
        assert "CONFLUENCE_SPACES" in resp.json()["detail"]

    def test_admin_sync_conflict_when_running(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.trigger_confluence.return_value = False
        monkeypatch.setattr("app.api.admin_routes.get_sync_service", lambda: mock_svc)

        resp = client.post(
            "/api/admin/sync",
            json={"source": "confluence"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 409
        assert resp.json()["started"] is False

    def test_admin_sync_gdrive_rejects_department_filter(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        monkeypatch.setattr("app.api.admin_routes.get_sync_service", lambda: mock_svc)

        resp = client.post(
            "/api/admin/sync",
            json={"source": "gdrive", "department": RISK},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 400
        mock_svc.trigger_gdrive.assert_not_called()

    def _make_sync_status_snapshot(
        self,
        *,
        risk_last_synced_at: str | None = None,
        grow_last_synced_at: str | None = None,
        bank_last_synced_at: str | None = None,
    ) -> dict:
        return {
            "jobs": {
                "confluence": {
                    "job_id": None,
                    "status": "pending",
                    "started_at": None,
                    "finished_at": None,
                    "last_success_at": None,
                    "target_department": None,
                    "doc_count": 0,
                    "chunk_count": 0,
                    "errors": [],
                    "progress": None,
                    "departments": [],
                }
            },
            "departments_indexed": {
                RISK: {
                    "chunk_count": 0,
                    "doc_count": 0,
                    "has_data": False,
                    "last_synced_at": risk_last_synced_at,
                },
                GROW: {
                    "chunk_count": 0,
                    "doc_count": 0,
                    "has_data": False,
                    "last_synced_at": grow_last_synced_at,
                },
                BANK: {
                    "chunk_count": 0,
                    "doc_count": 0,
                    "has_data": False,
                    "last_synced_at": bank_last_synced_at,
                },
            },
        }

    def test_admin_sync_status_no_auth_required(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.orchestrator.admin_status_snapshot.return_value = (
            self._make_sync_status_snapshot()
        )
        monkeypatch.setattr("app.api.admin_routes.get_sync_service", lambda: mock_svc)

        resp = client.get("/api/admin/sync/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["jobs"]["confluence"]["status"] == "pending"
        assert RISK in body["departments_indexed"]

    def test_admin_sync_status_last_synced_at_propagated(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regression: last_synced_at from sync_state must survive schema validation.

        AdminDepartmentIndexStatus had extra="forbid" and was missing last_synced_at,
        causing 422 on production while mock-based tests passed.
        """
        mock_svc = MagicMock()
        mock_svc.orchestrator.admin_status_snapshot.return_value = (
            self._make_sync_status_snapshot(
                risk_last_synced_at="2026-06-14T08:00:00Z",
                grow_last_synced_at=None,
            )
        )
        monkeypatch.setattr("app.api.admin_routes.get_sync_service", lambda: mock_svc)

        resp = client.get("/api/admin/sync/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["departments_indexed"][RISK]["last_synced_at"] == "2026-06-14T08:00:00Z"
        assert body["departments_indexed"][GROW]["last_synced_at"] is None

    def test_admin_sync_history(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.orchestrator.history_snapshot.return_value = [
            {
                "job_id": "job-1",
                "source": "confluence",
                "status": "success",
                "started_at": "2026-06-13T00:00:00Z",
                "finished_at": "2026-06-13T00:01:00Z",
                "department": None,
                "doc_count": 2,
                "chunk_count": 8,
                "errors": [],
                "departments": [],
            }
        ]
        monkeypatch.setattr("app.api.admin_routes.get_sync_service", lambda: mock_svc)

        resp = client.get("/api/admin/sync/history?source=confluence&limit=5")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["entries"]) == 1
        assert body["entries"][0]["job_id"] == "job-1"
        mock_svc.orchestrator.history_snapshot.assert_called_once_with(
            source="confluence",
            limit=5,
        )
