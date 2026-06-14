from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.schemas import ChatResponse
from tests.unit.api.conftest import AUTH_HEADERS, HEADER_SESSION, HEADER_USER
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


class TestHealthRoute:
    def test_health_returns_200(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert "version" in body
        assert "index_ready" in body
        assert body["config"]["topk"] == 8
        assert body["config"]["grade_threshold"] == 0.3


class TestChatRoute:
    def test_chat_missing_user_header_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/chat",
            json={"question": "hello"},
            headers={HEADER_SESSION: "s1"},
        )
        assert resp.status_code == 400
        assert "User-Id" in resp.json()["detail"]

    def test_chat_missing_session_header_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/chat",
            json={"question": "hello"},
            headers={HEADER_USER: "u1"},
        )
        assert resp.status_code == 400
        assert "Session-Id" in resp.json()["detail"]

    def test_chat_rejects_invalid_body(self, client: TestClient, ready_retriever: MagicMock) -> None:
        _ = ready_retriever
        resp = client.post("/chat", json={"question": ""}, headers=AUTH_HEADERS)
        assert resp.status_code == 422

    def test_chat_503_when_index_not_ready(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_retriever = MagicMock()
        mock_retriever.is_ready.return_value = False
        mock_deps = MagicMock()
        mock_deps.retriever = mock_retriever
        monkeypatch.setattr("app.api.routes.get_deps", lambda: mock_deps)

        resp = client.post(
            "/chat",
            json={"question": "What is the escalation process?"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 503
        assert resp.json()["detail"] == "Knowledge base not ready — please sync first"

    def test_chat_success_with_mocked_graph(
        self,
        client: TestClient,
        ready_retriever: MagicMock,
        sample_chat_response: ChatResponse,
    ) -> None:
        _ = ready_retriever
        with patch("app.api.routes.run_chat", return_value=sample_chat_response):
            resp = client.post(
                "/chat",
                json={
                    "question": "What is the escalation process?",
                    "target_departments": [RISK],
                },
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "answered"
        assert body["confidence"] == 0.87
        assert body["feedback_id"] == sample_chat_response.feedback_id
        assert body["source_departments"] == [RISK]
        assert len(body["citations"]) == 1
        assert body["citations"][0]["title"] == "Risk Alert Escalation Policy"

    def test_chat_timeout_returns_408(
        self,
        client: TestClient,
        ready_retriever: MagicMock,
    ) -> None:
        _ = ready_retriever
        with patch("app.api.routes.run_chat", side_effect=TimeoutError("Request timeout")):
            resp = client.post(
                "/chat",
                json={"question": "slow question"},
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 408
        assert resp.json()["detail"] == "Request timeout"

    def test_invocations_mirrors_chat(
        self,
        client: TestClient,
        ready_retriever: MagicMock,
        sample_chat_response: ChatResponse,
    ) -> None:
        _ = ready_retriever
        with patch("app.api.routes.run_chat", return_value=sample_chat_response) as mock_run:
            resp = client.post(
                "/invocations",
                json={"question": "hello"},
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "answered"
        mock_run.assert_called_once()


class TestChatStreamRoute:
    def test_chat_stream_missing_user_header_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/chat/stream",
            json={"question": "hello"},
            headers={HEADER_SESSION: "s1"},
        )
        assert resp.status_code == 400

    def test_chat_stream_emits_sse_events(
        self,
        client: TestClient,
        ready_retriever: MagicMock,
        sample_chat_response: ChatResponse,
    ) -> None:
        _ = ready_retriever

        def fake_stream(_ctx, _req):
            yield {"event": "start", "data": {"question": "hello"}}
            yield {"event": "done", "data": sample_chat_response.model_dump()}

        with patch("app.api.routes.stream_chat", side_effect=lambda ctx, req: fake_stream(ctx, req)):
            resp = client.post(
                "/chat/stream",
                json={"question": "hello"},
                headers=AUTH_HEADERS,
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = resp.text
        assert '"event": "start"' in body
        assert '"event": "done"' in body
        assert sample_chat_response.feedback_id in body

    def test_chat_stream_503_when_index_not_ready(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_retriever = MagicMock()
        mock_retriever.is_ready.return_value = False
        mock_deps = MagicMock()
        mock_deps.retriever = mock_retriever
        monkeypatch.setattr("app.api.routes.get_deps", lambda: mock_deps)

        resp = client.post(
            "/chat/stream",
            json={"question": "hello"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 503


class TestFeedbackRoute:
    def test_feedback_missing_header_returns_400(self, client: TestClient) -> None:
        resp = client.post(
            "/feedback",
            json={"feedback_id": "fb-1", "rating": "up"},
        )
        assert resp.status_code == 400

    def test_feedback_404_for_unknown_id(
        self,
        client: TestClient,
        ready_retriever: MagicMock,
    ) -> None:
        _ = ready_retriever
        resp = client.post(
            "/feedback",
            json={"feedback_id": "fb-unknown", "rating": "up"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "feedback_id not found"

    def test_feedback_204_on_success(
        self,
        client: TestClient,
        ready_retriever: MagicMock,
    ) -> None:
        _ = ready_retriever
        feedback_id = "fb-test-success"
        from app.api.service import get_feedback_store

        get_feedback_store().register_pending(feedback_id)

        resp = client.post(
            "/feedback",
            json={
                "feedback_id": feedback_id,
                "rating": "up",
                "comment": "Very helpful",
            },
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204
        assert resp.content == b""

        up, down = get_feedback_store().counts()
        assert up == 1
        assert down == 0

    def test_feedback_rejects_invalid_rating(
        self,
        client: TestClient,
        ready_retriever: MagicMock,
    ) -> None:
        _ = ready_retriever
        resp = client.post(
            "/feedback",
            json={"feedback_id": "fb-1", "rating": "maybe"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 422

    def test_feedback_accepts_rating_without_comment(
        self,
        client: TestClient,
        ready_retriever: MagicMock,
    ) -> None:
        _ = ready_retriever
        feedback_id = "fb-no-comment"
        from app.api.service import get_feedback_store

        get_feedback_store().register_pending(feedback_id)

        resp = client.post(
            "/feedback",
            json={"feedback_id": feedback_id, "rating": "down"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 204

        up, down = get_feedback_store().counts()
        assert up == 0
        assert down == 1


class TestSyncRoutes:
    def test_sync_confluence_requires_auth(self, client: TestClient) -> None:
        resp = client.post("/sync/confluence")
        assert resp.status_code == 400

    def test_sync_confluence_starts_job(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.trigger_confluence.return_value = True
        monkeypatch.setattr("app.api.routes.get_sync_service", lambda: mock_svc)

        resp = client.post("/sync/confluence", headers=AUTH_HEADERS)
        assert resp.status_code == 202
        body = resp.json()
        assert body["source"] == "confluence"
        assert body["started"] is True
        assert "started in background" in body["message"]

    def test_sync_confluence_conflict_when_running(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.trigger_confluence.return_value = False
        monkeypatch.setattr("app.api.routes.get_sync_service", lambda: mock_svc)

        resp = client.post("/sync/confluence", headers=AUTH_HEADERS)
        assert resp.status_code == 409
        body = resp.json()
        assert body["started"] is False
        assert "already running" in body["message"]

    def test_sync_gdrive_starts_job(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.trigger_gdrive.return_value = True
        monkeypatch.setattr("app.api.routes.get_sync_service", lambda: mock_svc)

        resp = client.post("/sync/gdrive", headers=AUTH_HEADERS)
        assert resp.status_code == 202
        body = resp.json()
        assert body["source"] == "gdrive"
        assert body["started"] is True

    def test_sync_gdrive_conflict_when_running(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_svc = MagicMock()
        mock_svc.trigger_gdrive.return_value = False
        monkeypatch.setattr("app.api.routes.get_sync_service", lambda: mock_svc)

        resp = client.post("/sync/gdrive", headers=AUTH_HEADERS)
        assert resp.status_code == 409
        assert resp.json()["started"] is False

    def test_sync_status_no_auth_required(self, client: TestClient) -> None:
        resp = client.get("/sync/status")
        assert resp.status_code == 200
        sources = resp.json()["sources"]
        assert len(sources) == 2
        assert {s["source"] for s in sources} == {"confluence", "gdrive"}
        for src in sources:
            assert src["state"] in ("running", "idle", "error")
            assert "doc_count" in src
            assert "chunk_count" in src


class TestDashboardRoute:
    def test_dashboard_empty_metrics(self, client: TestClient) -> None:
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["query_count"] == 0
        assert body["deflection_rate"] == 0.0
        assert body["answered_wrong_rate"] == 0.0
        assert body["refusal_rate"] == 0.0
        assert body["partial_rate"] == 0.0
        assert body["conflict_rate"] == 0.0
        assert body["feedback_up"] == 0
        assert body["feedback_down"] == 0
        assert body["history"] == []

    def test_dashboard_with_audit_data(self, client: TestClient) -> None:
        from app.api.service import get_audit_store

        get_audit_store().log_query(
            user_id="test-user",
            session_id="test-session",
            role="engineer",
            question="What is the escalation process?",
            departments=[RISK],
            status="answered",
            confidence=0.87,
            latency_ms=1523,
            feedback_id="fb-dashboard-test",
        )

        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["query_count"] >= 1
        assert len(body["history"]) >= 1
        assert body["history"][0]["status"] == "answered"

    def test_dashboard_answered_wrong_rate_from_feedback(self, client: TestClient) -> None:
        from app.api.service import get_feedback_store

        store = get_feedback_store()
        for fid, rating in (
            ("fb-dash-up-1", "up"),
            ("fb-dash-up-2", "up"),
            ("fb-dash-down-1", "down"),
        ):
            store.register_pending(fid)
            store.submit(feedback_id=fid, user_id="dash-test-user", rating=rating, comment=None)

        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        assert body["feedback_up"] == 2
        assert body["feedback_down"] == 1
        assert body["answered_wrong_rate"] == pytest.approx(1 / 3)
