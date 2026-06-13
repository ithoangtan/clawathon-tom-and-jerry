from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.schemas import ChatResponse
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, BANK, DEFAULT_HOME, GROW, RISK

HEADER_USER = "X-GreenNode-AgentBase-User-Id"
HEADER_SESSION = "X-GreenNode-AgentBase-Session-Id"
HEADER_ROLE = "X-GreenNode-AgentBase-Role"
HEADER_HOME = "X-GreenNode-AgentBase-Home-Department"

AUTH_HEADERS = {
    HEADER_USER: "test-user",
    HEADER_SESSION: "test-session",
    HEADER_ROLE: "engineer",
    HEADER_HOME: RISK,
}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture()
def ready_retriever(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mark the FAISS index as ready for chat/sync-protected routes."""
    mock_retriever = MagicMock()
    mock_retriever.is_ready.return_value = True

    mock_deps = MagicMock()
    mock_deps.retriever = mock_retriever

    monkeypatch.setattr("app.api.routes.get_deps", lambda: mock_deps)
    return mock_retriever


@pytest.fixture()
def sample_chat_response() -> ChatResponse:
    return ChatResponse(
        answer="The escalation process begins when… [1]",
        citations=[
            {
                "title": "Risk Alert Escalation Policy",
                "url": "https://example.atlassian.net/wiki/pages/123456",
                "section": "Escalation Levels > Level 1",
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
        feedback_id="fb-550e8400-e29b-41d4-a716-446655440000",
        status="answered",
        conflicts=None,
        clarifying_question=None,
        lang="en",
    )
