from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from tests.unit.api.conftest import AUTH_HEADERS


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
            json={"source": "confluence", "department": "risk"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["department"] == "risk"
        mock_svc.trigger_confluence.assert_called_once_with(department="risk")

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
            json={"source": "gdrive", "department": "risk"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 400
        mock_svc.trigger_gdrive.assert_not_called()

    def test_admin_sync_status_no_auth_required(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.orchestrator.admin_status_snapshot.return_value = {
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
                "risk": {"chunk_count": 0, "doc_count": 0, "has_data": False},
                "grow_enablement": {"chunk_count": 0, "doc_count": 0, "has_data": False},
                "bank_partnerships": {
                    "chunk_count": 0,
                    "doc_count": 0,
                    "has_data": False,
                },
            },
        }
        monkeypatch.setattr("app.api.admin_routes.get_sync_service", lambda: mock_svc)

        resp = client.get("/api/admin/sync/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["jobs"]["confluence"]["status"] == "pending"
        assert "risk" in body["departments_indexed"]

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
