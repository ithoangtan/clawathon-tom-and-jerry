from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import create_app

CONFIG_KEYS = (
    "small_model",
    "main_model",
    "embedding_model",
    "grade_threshold",
    "topk",
    "route_confidence_min",
)


def test_health_contract_shape() -> None:
    """GET /health must match docs/API-CONTRACT.md."""
    client = TestClient(create_app())
    resp = client.get("/health")

    assert resp.status_code == 200
    body = resp.json()

    assert body["status"] == "healthy"
    assert isinstance(body["index_ready"], bool)
    assert body["version"] is not None

    config = body["config"]
    assert config is not None
    for key in CONFIG_KEYS:
        assert key in config, f"Missing config key: {key}"

    assert config["embedding_model"] == "intfloat/multilingual-e5-small"
    assert config["grade_threshold"] == 0.5
    assert config["topk"] == 8
    assert config["route_confidence_min"] == 0.55


def test_health_no_auth_headers_required() -> None:
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_content_type_json() -> None:
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.headers["content-type"].startswith("application/json")
