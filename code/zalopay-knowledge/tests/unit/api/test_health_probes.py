from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app, register_health_routes


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_health_routes_registered_on_app_factory() -> None:
    """Probes are mounted by create_app(), not the chat APIRouter."""
    from fastapi import FastAPI

    probe_app = FastAPI()
    register_health_routes(probe_app)
    paths = {getattr(route, "path", None) for route in probe_app.routes}
    assert {"/health", "/health/live", "/health/ready"}.issubset(paths)


def test_health_live_always_200(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_deps = MagicMock()
    mock_deps.retriever.is_ready.return_value = False
    mock_deps.llm.is_reachable.return_value = False
    monkeypatch.setattr("app.api.health.get_deps", lambda: mock_deps)

    resp = client.get("/health/live")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["index_ready"] is False
    assert body["maas_ready"] is False
    assert body["ready"] is False


def test_health_ready_503_until_index_and_maas(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_deps = MagicMock()
    mock_deps.retriever.is_ready.return_value = True
    mock_deps.llm.is_reachable.return_value = False
    monkeypatch.setattr("app.api.health.get_deps", lambda: mock_deps)

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["index_ready"] is True
    assert resp.json()["maas_ready"] is False


def test_health_ready_200_when_fully_ready(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_deps = MagicMock()
    mock_deps.retriever.is_ready.return_value = True
    mock_deps.llm.is_reachable.return_value = True
    monkeypatch.setattr("app.api.health.get_deps", lambda: mock_deps)

    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is True
    assert body["index_ready"] is True
    assert body["maas_ready"] is True


def test_health_root_always_200_no_maas_ping(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """/health is a liveness probe — never pings MaaS, never returns non-200."""
    mock_deps = MagicMock()
    mock_deps.retriever.is_ready.return_value = True
    mock_deps.llm.is_reachable.return_value = True
    monkeypatch.setattr("app.api.health.get_deps", lambda: mock_deps)

    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["index_ready"] is True
    # maas_ready is not checked on liveness — always False to avoid slow pings
    assert body["maas_ready"] is False
    # is_reachable must NOT have been called (no MaaS ping on /health)
    mock_deps.llm.is_reachable.assert_not_called()
