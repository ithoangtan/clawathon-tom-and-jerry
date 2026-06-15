"""Unit tests for ConfluenceWriter (S2) — HTTP mocked via _request."""

from __future__ import annotations

from typing import Any

import pytest

from app.adapters.confluence_writer import ConfluenceWriter, NullConfluenceWriter, text_to_storage
from app.config import Settings
from app.ports.errors import ConfluenceUnavailable


def _writer(monkeypatch: pytest.MonkeyPatch, responses: list[Any]) -> tuple[ConfluenceWriter, list]:
    s = Settings(
        confluence_base_url="https://site.atlassian.net/wiki",
        confluence_email="a@b.com",
        confluence_api_token="tok",
        _env_file=None,
    )
    w = ConfluenceWriter(s)
    calls: list[dict] = []
    it = iter(responses)

    def fake_request(method: str, path: str, *, json=None, api: str = "v2") -> dict:
        calls.append({"method": method, "path": path, "json": json, "api": api})
        return next(it)

    monkeypatch.setattr(w, "_request", fake_request)
    return w, calls


def test_text_to_storage_escapes_and_paragraphs():
    html = text_to_storage("line1\nA & B <x>")
    assert "<p>line1</p>" in html
    assert "&amp;" in html and "&lt;x&gt;" in html


def test_create_page(monkeypatch: pytest.MonkeyPatch):
    w, calls = _writer(monkeypatch, [
        {"results": [{"id": "999"}]},   # resolve space
        {"id": "1001"},                  # create
    ])
    out = w.create_page(space_key="WF", title="T", body_storage="<p>x</p>")
    assert out["id"] == "1001"
    assert calls[0]["path"].startswith("spaces?keys=WF")
    assert calls[1]["method"] == "POST" and calls[1]["path"] == "pages"


def test_append_reads_then_writes_incremented_version(monkeypatch: pytest.MonkeyPatch):
    w, calls = _writer(monkeypatch, [
        {  # _get_page
            "title": "T", "spaceId": "999", "version": {"number": 3},
            "body": {"storage": {"value": "<p>old</p>"}},
        },
        {"_links": {"webui": "/x"}},  # PUT
    ])
    out = w.append_to_page(page_id="1001", html_fragment="<p>new</p>")
    assert out["version"] == 4
    put = calls[1]
    assert put["method"] == "PUT"
    assert put["json"]["body"]["value"] == "<p>old</p><p>new</p>"
    assert put["json"]["version"]["number"] == 4


def test_add_labels_drops_colon_labels(monkeypatch: pytest.MonkeyPatch):
    w, calls = _writer(monkeypatch, [
        {"results": [{"name": "status-active"}, {"name": "zalopay-workflow"}]},
    ])
    out = w.add_labels(page_id="1001", labels=["status-active", "bad:label", "zalopay-workflow"])
    sent = calls[0]["json"]
    assert {x["name"] for x in sent} == {"status-active", "zalopay-workflow"}  # colon dropped
    assert calls[0]["api"] == "v1"
    assert "status-active" in out


def test_not_ready_when_unconfigured():
    w = ConfluenceWriter(Settings(_env_file=None))
    assert w.is_ready() is False


def test_null_writer_raises():
    n = NullConfluenceWriter()
    assert n.is_ready() is False
    with pytest.raises(ConfluenceUnavailable):
        n.append_to_page(page_id="1", html_fragment="<p>x</p>")
