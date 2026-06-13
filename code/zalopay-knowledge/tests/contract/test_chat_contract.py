from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.schemas import ChatResponse, ClarifyingQuestion, ConflictModel, ConflictSide

AUTH_HEADERS = {
    "X-GreenNode-AgentBase-User-Id": "contract-user",
    "X-GreenNode-AgentBase-Session-Id": "contract-session",
    "X-GreenNode-AgentBase-Role": "business",
    "X-GreenNode-AgentBase-Home-Department": "risk",
}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture()
def ready_index(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    mock_retriever = MagicMock()
    mock_retriever.is_ready.return_value = True
    mock_deps = MagicMock()
    mock_deps.retriever = mock_retriever
    monkeypatch.setattr("app.api.routes.get_deps", lambda: mock_deps)


def _answered_response() -> ChatResponse:
    return ChatResponse(
        answer="The escalation process begins when… [1]\n\nFor urgent cases… [2]",
        citations=[
            {
                "title": "Risk Alert Escalation Policy",
                "url": "https://yoursite.atlassian.net/wiki/spaces/RISK/pages/123456",
                "section": "Escalation Levels > Level 1",
                "last_modified": "2024-11-15T09:30:00Z",
                "lifecycle_state": "active",
                "deprecated": False,
                "successor_url": None,
                "source_type": "confluence",
                "page": None,
            },
            {
                "title": "Incident Response Runbook.pdf",
                "url": "https://drive.google.com/file/d/abc123",
                "section": None,
                "last_modified": "2024-10-01T00:00:00Z",
                "lifecycle_state": "active",
                "deprecated": False,
                "successor_url": None,
                "source_type": "pdf",
                "page": 3,
            },
        ],
        source_departments=["risk"],
        confidence=0.87,
        feedback_id="fb-550e8400-e29b-41d4-a716-446655440000",
        status="answered",
        conflicts=None,
        clarifying_question=None,
        lang="en",
    )


class TestChatContractErrors:
    def test_missing_user_header_contract_detail(self, client: TestClient) -> None:
        resp = client.post(
            "/chat",
            json={"question": "hello"},
            headers={"X-GreenNode-AgentBase-Session-Id": "sess-xyz789"},
        )
        assert resp.status_code == 400
        assert resp.json() == {
            "detail": "Missing required header: X-GreenNode-AgentBase-User-Id"
        }

    def test_missing_session_header_contract_detail(self, client: TestClient) -> None:
        resp = client.post(
            "/chat",
            json={"question": "hello"},
            headers={"X-GreenNode-AgentBase-User-Id": "user-abc123"},
        )
        assert resp.status_code == 400
        assert resp.json() == {
            "detail": "Missing required header: X-GreenNode-AgentBase-Session-Id"
        }

    def test_index_not_ready_returns_503(self, client: TestClient) -> None:
        resp = client.post(
            "/chat",
            json={"question": "What is the escalation process for risk alerts?"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 503
        assert resp.json() == {
            "detail": "Knowledge base not ready — please sync first"
        }

    def test_timeout_returns_408(self, client: TestClient, ready_index: None) -> None:
        _ = ready_index
        with patch("app.api.routes.run_chat", side_effect=TimeoutError()):
            resp = client.post(
                "/chat",
                json={"question": "slow"},
                headers=AUTH_HEADERS,
            )
        assert resp.status_code == 408
        assert resp.json() == {"detail": "Request timeout"}


class TestChatContractSuccess:
    def test_answered_response_wire_shape(self, client: TestClient, ready_index: None) -> None:
        _ = ready_index
        with patch("app.api.routes.run_chat", return_value=_answered_response()):
            resp = client.post(
                "/chat",
                json={
                    "question": "What is the escalation process for risk alerts?",
                    "target_departments": ["risk"],
                },
                headers=AUTH_HEADERS,
            )

        assert resp.status_code == 200
        body = resp.json()

        # Top-level fields per API-CONTRACT.md
        assert set(body.keys()) >= {
            "answer",
            "citations",
            "source_departments",
            "confidence",
            "feedback_id",
            "status",
            "conflicts",
            "clarifying_question",
            "lang",
        }
        assert body["status"] == "answered"
        assert 0.0 <= body["confidence"] <= 1.0
        assert body["source_departments"] == ["risk"]
        assert body["lang"] == "en"
        assert "[1]" in body["answer"]

        # Citation shape
        assert len(body["citations"]) == 2
        cite = body["citations"][0]
        for field in (
            "title",
            "url",
            "section",
            "last_modified",
            "lifecycle_state",
            "deprecated",
            "successor_url",
            "source_type",
            "page",
        ):
            assert field in cite

        pdf_cite = body["citations"][1]
        assert pdf_cite["source_type"] == "pdf"
        assert pdf_cite["page"] == 3

    def test_clarifying_question_shape(self, client: TestClient, ready_index: None) -> None:
        _ = ready_index
        response = ChatResponse(
            answer="",
            citations=[],
            source_departments=[],
            confidence=0.0,
            feedback_id="fb-clarify",
            status="refused",
            clarifying_question=ClarifyingQuestion(
                prompt="Which department's policies are you asking about?",
                options=["risk", "grow_enablement"],
            ),
        )
        with patch("app.api.routes.run_chat", return_value=response):
            resp = client.post(
                "/chat",
                json={"question": "What is the policy?"},
                headers=AUTH_HEADERS,
            )

        body = resp.json()
        cq = body["clarifying_question"]
        assert cq["prompt"] == "Which department's policies are you asking about?"
        assert cq["options"] == ["risk", "grow_enablement"]

    def test_conflict_shape(self, client: TestClient, ready_index: None) -> None:
        _ = ready_index
        citation = {
            "title": "Policy A",
            "url": "https://example.com/a",
        }
        response = ChatResponse(
            answer="Conflicting info [1][2]",
            citations=[citation, citation],
            source_departments=["risk", "bank_partnerships"],
            confidence=0.6,
            feedback_id="fb-conflict",
            status="partial",
            conflicts=[
                ConflictModel(
                    topic="Escalation SLA for Level 2 incidents",
                    sides=[
                        ConflictSide(
                            department="risk",
                            statement="Level 2 must be resolved within 4 hours.",
                            citation=citation,  # type: ignore[arg-type]
                        ),
                        ConflictSide(
                            department="bank_partnerships",
                            statement="Level 2 SLA is 8 business hours.",
                            citation=citation,  # type: ignore[arg-type]
                        ),
                    ],
                )
            ],
        )
        with patch("app.api.routes.run_chat", return_value=response):
            resp = client.post(
                "/chat",
                json={"question": "Level 2 SLA?"},
                headers=AUTH_HEADERS,
            )

        body = resp.json()
        conflict = body["conflicts"][0]
        assert conflict["topic"] == "Escalation SLA for Level 2 incidents"
        assert len(conflict["sides"]) == 2
        assert conflict["sides"][0]["department"] == "risk"
        assert "citation" in conflict["sides"][0]

    def test_snake_case_wire_format(self, client: TestClient, ready_index: None) -> None:
        _ = ready_index
        with patch("app.api.routes.run_chat", return_value=_answered_response()):
            resp = client.post(
                "/chat",
                json={"question": "test"},
                headers=AUTH_HEADERS,
            )
        body = resp.json()
        assert "source_departments" in body
        assert "feedback_id" in body
        assert "clarifying_question" in body
        assert "sourceDepartments" not in body
        assert "feedbackId" not in body
