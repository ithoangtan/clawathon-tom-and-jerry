from __future__ import annotations

"""Security middleware tests — gateway trust, kill-switch, audit."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.schemas import ChatResponse
from app.common.security import (
    HEADER_GATEWAY_TRUST,
    HEADER_GATEWAY_VERIFIED,
    HEADER_SESSION,
    HEADER_USER,
    build_gateway_trust_token,
)
from tests.unit.api.conftest import AUTH_HEADERS, ready_retriever
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK

GATEWAY_HEADERS = {
    **AUTH_HEADERS,
    HEADER_GATEWAY_VERIFIED: "true",
}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


class TestGatewayTrust:
    def test_local_mode_allows_client_headers(
        self, client: TestClient, ready_retriever: None
    ) -> None:
        _ = ready_retriever
        with patch("app.api.routes.run_chat", return_value=_sample_response()):
            resp = client.post(
                "/chat",
                json={"question": "hello"},
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 200

    def test_gateway_trust_rejects_spoofed_identity(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GATEWAY_TRUST_REQUIRED", "true")
        from app.config import get_settings

        get_settings.cache_clear()

        resp = client.post(
            "/chat",
            json={"question": "hello"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 403
        assert "Client-supplied" in resp.json()["detail"]

    def test_gateway_trust_accepts_verified_marker(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch, ready_retriever: None
    ) -> None:
        _ = ready_retriever
        monkeypatch.setenv("GATEWAY_TRUST_REQUIRED", "true")
        from app.config import get_settings

        get_settings.cache_clear()

        with patch("app.api.routes.run_chat", return_value=_sample_response()):
            resp = client.post(
                "/chat",
                json={"question": "hello"},
                headers=GATEWAY_HEADERS,
            )
        assert resp.status_code == 200

    def test_gateway_trust_hmac_secret(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch, ready_retriever: None
    ) -> None:
        _ = ready_retriever
        secret = "test-gateway-secret"
        monkeypatch.setenv("GATEWAY_TRUST_REQUIRED", "true")
        monkeypatch.setenv("GATEWAY_TRUST_SECRET", secret)
        from app.config import get_settings

        get_settings.cache_clear()

        headers = dict(AUTH_HEADERS)
        headers[HEADER_GATEWAY_TRUST] = build_gateway_trust_token(
            headers[HEADER_USER],
            headers[HEADER_SESSION],
            secret,
        )

        with patch("app.api.routes.run_chat", return_value=_sample_response()):
            resp = client.post(
                "/chat",
                json={"question": "hello"},
                headers=headers,
            )
        assert resp.status_code == 200

    def test_gateway_trust_rejects_spoofed_verified_marker_only(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GATEWAY_TRUST_REQUIRED", "true")
        from app.config import get_settings

        get_settings.cache_clear()

        resp = client.get(
            "/health",
            headers={HEADER_GATEWAY_VERIFIED: "true"},
        )
        assert resp.status_code == 403

    def test_gateway_trust_rejects_verified_without_identity_when_hmac(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GATEWAY_TRUST_REQUIRED", "true")
        monkeypatch.setenv("GATEWAY_TRUST_SECRET", "rotate-me")
        from app.config import get_settings

        get_settings.cache_clear()

        headers = {
            **AUTH_HEADERS,
            HEADER_GATEWAY_VERIFIED: "true",
        }
        resp = client.post("/chat", json={"question": "hello"}, headers=headers)
        assert resp.status_code == 403

    def test_agentbase_env_auto_requires_gateway_trust(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("APP_ENV", "agentbase")
        monkeypatch.delenv("GATEWAY_TRUST_REQUIRED", raising=False)
        from app.config import Settings, get_settings

        get_settings.cache_clear()
        # Ignore workspace .env so we test the APP_ENV default, not local dev overrides.
        cfg = Settings(_env_file=None)
        assert cfg.gateway_trust_required is True

    def test_agentbase_env_respects_explicit_gateway_trust_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("APP_ENV", "agentbase")
        monkeypatch.setenv("GATEWAY_TRUST_REQUIRED", "false")
        from app.config import Settings, get_settings

        get_settings.cache_clear()
        cfg = Settings()
        assert cfg.gateway_trust_required is False

    def test_local_env_enforces_gateway_trust_when_explicitly_required(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch, ready_retriever: None
    ) -> None:
        _ = ready_retriever
        monkeypatch.setenv("APP_ENV", "local")
        monkeypatch.setenv("GATEWAY_TRUST_REQUIRED", "true")
        from app.config import get_settings

        get_settings.cache_clear()

        resp = client.post(
            "/chat",
            json={"question": "hello"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 403


class TestKillSwitch:
    def test_kill_switch_blocks_chat(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_ENABLED", "false")
        from app.config import get_settings

        get_settings.cache_clear()

        resp = client.post(
            "/chat",
            json={"question": "hello"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 503
        assert resp.json()["detail"] == "Knowledge agent is temporarily disabled"

    def test_kill_switch_allows_health(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_ENABLED", "false")
        from app.config import get_settings

        get_settings.cache_clear()
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_kill_switch_allows_health_ready_and_sync_status(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_ENABLED", "false")
        from app.config import get_settings

        get_settings.cache_clear()

        ready = client.get("/health/ready")
        assert ready.status_code in (200, 503)

        status = client.get("/sync/status")
        assert status.status_code == 200

    def test_kill_switch_allows_dashboard(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_ENABLED", "false")
        from app.config import get_settings

        get_settings.cache_clear()
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200

    def test_kill_switch_blocks_sync(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_ENABLED", "false")
        from app.config import get_settings

        get_settings.cache_clear()
        resp = client.post("/sync/confluence", headers=AUTH_HEADERS)
        assert resp.status_code == 503

    def test_kill_switch_blocks_run_chat_directly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.api.context import UserContext
        from app.api.schemas import ChatRequest
        from app.api.service import run_chat
        from app.common.security import AgentDisabledError
        from app.config import get_settings

        monkeypatch.setenv("AGENT_ENABLED", "false")
        get_settings.cache_clear()

        ctx = UserContext(user_id="u", session_id="s")
        with pytest.raises(AgentDisabledError):
            run_chat(ctx, ChatRequest(question="hello"))


class TestAuditTrail:
    def test_audit_logs_question_citations_and_answer_preview(
        self, client: TestClient, ready_retriever: None
    ) -> None:
        _ = ready_retriever
        from app.api.context import UserContext
        from app.api.schemas import ChatRequest
        from app.api.service import get_audit_store, record_chat_outcome

        response = _sample_response()

        def _run_and_audit(ctx: UserContext, request: ChatRequest):
            record_chat_outcome(ctx, request, response, latency_ms=42)
            return response

        with patch("app.api.routes.run_chat", side_effect=_run_and_audit):
            client.post(
                "/chat",
                json={"question": "What is the escalation process?"},
                headers=AUTH_HEADERS,
            )

        import pymysql.cursors
        conn = get_audit_store()._connect()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute(
                    "SELECT question, departments, citations_json, answer_preview, status, user_id "
                    "FROM queries ORDER BY ts DESC LIMIT 1"
                )
                row = cur.fetchone()
        finally:
            conn.close()

        assert row is not None
        assert "escalation" in row["question"].lower()
        assert row["user_id"] == AUTH_HEADERS[HEADER_USER]
        assert row["status"] == "answered"
        assert "citations" in row["citations_json"] or "Risk" in row["citations_json"]
        assert "escalation" in row["answer_preview"].lower()


def _sample_response() -> ChatResponse:
    return ChatResponse(
        answer="The escalation process begins when… [1]",
        citations=[
            {
                "title": "Risk Alert Escalation Policy",
                "url": "https://example.atlassian.net/wiki/pages/123456",
                "section": "Escalation Levels",
                "last_modified": "2024-11-15T09:30:00Z",
                "lifecycle_state": "active",
                "deprecated": False,
                "successor_url": None,
                "source_type": "confluence",
                "page": None,
            }
        ],
        source_departments=[RISK],
        confidence=0.87,
        feedback_id="fb-security-test",
        status="answered",
        conflicts=None,
        clarifying_question=None,
        lang="en",
    )
