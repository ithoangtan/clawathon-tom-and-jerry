from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.spa_static import SPAStaticFiles, should_spa_fallback

FRONTEND_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"


@pytest.mark.parametrize(
    "path,expected",
    [
        ("settings", True),
        ("admin", True),
        ("dashboard", True),
        ("", True),
        ("assets/index.js", False),
        ("favicon.svg", False),
    ],
)
def test_should_spa_fallback(path: str, expected: bool) -> None:
    assert should_spa_fallback(path) is expected


def test_spa_static_files_serves_index_for_client_routes(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "<!doctype html><html><body><div id='root'></div></body></html>",
        encoding="utf-8",
    )

    app = FastAPI()
    app.mount("/", SPAStaticFiles(directory=str(tmp_path), html=True))
    client = TestClient(app)

    for route in ("/settings", "/admin", "/dashboard"):
        resp = client.get(route)
        assert resp.status_code == 200
        assert "id='root'" in resp.text

    missing_asset = client.get("/assets/missing.js")
    assert missing_asset.status_code == 404


@pytest.mark.skipif(not FRONTEND_DIST.is_dir(), reason="frontend/dist not built")
def test_create_app_serves_spa_routes() -> None:
    client = TestClient(create_app())

    for route in ("/settings", "/admin", "/dashboard"):
        resp = client.get(route)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert 'id="root"' in resp.text

    api_resp = client.get("/health/live")
    assert api_resp.status_code == 200
    assert api_resp.headers.get("content-type", "").startswith("application/json")
