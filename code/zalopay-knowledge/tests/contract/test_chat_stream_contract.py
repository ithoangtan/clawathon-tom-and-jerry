"""Contract tests for POST /chat/stream SSE channel — FR-6.2."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.schemas import ChatResponse

from tests.contract.test_chat_contract import AUTH_HEADERS, ready_index
from tests.department_fixtures import ALL_DEPARTMENT_KEYS, ALL_KEYS, BANK, DEFAULT_HOME, GROW, RISK


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


class TestChatStreamContract:
    def test_stream_content_type_and_event_shape(
        self, client: TestClient, ready_index: None
    ) -> None:
        _ = ready_index
        response = ChatResponse(
            answer="Answer [1].",
            citations=[],
            source_departments=[RISK],
            confidence=0.7,
            feedback_id="fb-stream-contract",
            status="answered",
        )

        def fake_stream(_ctx, _body):
            yield {"event": "start", "data": {"question": "test"}}
            yield {"event": "node", "data": {"node": "router"}}
            yield {"event": "done", "data": response.model_dump()}

        with patch("app.api.routes.stream_chat", side_effect=fake_stream):
            resp = client.post(
                "/chat/stream",
                json={"question": "test"},
                headers=AUTH_HEADERS,
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

        events: list[dict] = []
        for line in resp.text.splitlines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        assert [e["event"] for e in events] == ["start", "node", "done"]
        assert events[0]["data"]["question"] == "test"
        assert events[-1]["data"]["feedback_id"] == "fb-stream-contract"
