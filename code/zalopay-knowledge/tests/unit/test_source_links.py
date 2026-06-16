"""Unit tests for the in-system link resolver (app.integrations.source_links)."""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.integrations import source_links
from app.integrations.source_links import (
    adf_to_text,
    classify_link,
    extract_urls_from_adf,
    resolve_description_sources,
)

SETTINGS = Settings(_env_file=None)

CONF_URL = "https://ithoangtan-clawathon.atlassian.net/wiki/spaces/RISK/pages/12345/Spec"
JIRA_URL = "https://ithoangtan-clawathon.atlassian.net/browse/KAN-7"
GDRIVE_URL = "https://drive.google.com/file/d/ABC_123-xyz/view"
DOCS_URL = "https://docs.google.com/document/d/DocId123/edit"
EXT_URL = "https://example.com/some/external/page"


def _doc(*content: dict) -> dict:
    return {"type": "doc", "version": 1, "content": list(content)}


def _text_with_link(text: str, href: str) -> dict:
    return {"type": "paragraph", "content": [
        {"type": "text", "text": text, "marks": [{"type": "link", "attrs": {"href": href}}]}
    ]}


# ── classify_link ────────────────────────────────────────────────────────────

def test_classify_confluence_page():
    assert classify_link(CONF_URL) == ("confluence", "12345")


def test_classify_confluence_pageid_query():
    url = "https://x.atlassian.net/wiki/pages/viewpage.action?pageId=999"
    assert classify_link(url) == ("confluence", "999")


def test_classify_jira_browse():
    assert classify_link(JIRA_URL) == ("jira", "KAN-7")


def test_classify_gdrive_file_and_doc():
    assert classify_link(GDRIVE_URL) == ("gdrive", "ABC_123-xyz")
    assert classify_link(DOCS_URL) == ("gdrive", "DocId123")


def test_classify_external_returns_none():
    assert classify_link(EXT_URL) == (None, "")
    assert classify_link("") == (None, "")


# ── extract_urls_from_adf / adf_to_text ──────────────────────────────────────

def test_extract_urls_link_mark_inlinecard_and_bare_text():
    adf = _doc(
        _text_with_link("campaign spec", CONF_URL),
        {"type": "paragraph", "content": [{"type": "inlineCard", "attrs": {"url": JIRA_URL}}]},
        {"type": "paragraph", "content": [{"type": "text", "text": f"see {EXT_URL} too"}]},
    )
    assert extract_urls_from_adf(adf) == [CONF_URL, JIRA_URL, EXT_URL]


def test_extract_urls_dedupes_and_handles_none():
    adf = _doc(_text_with_link("a", CONF_URL), _text_with_link("b", CONF_URL))
    assert extract_urls_from_adf(adf) == [CONF_URL]
    assert extract_urls_from_adf(None) == []
    assert extract_urls_from_adf("plain string, no url") == []


def test_adf_to_text_flattens_tree():
    adf = _doc(
        {"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]},
        {"type": "paragraph", "content": [{"type": "text", "text": "world"}]},
    )
    assert adf_to_text(adf) == "Hello world"
    assert adf_to_text(None) == ""
    assert adf_to_text("already text") == "already text"


# ── resolve_description_sources ──────────────────────────────────────────────

class _FakeConfluence:
    def __init__(self, _settings: Any) -> None: ...
    def configured(self) -> bool:
        return True
    def fetch_page_body(self, page_id: str):
        return (f"Campaign spec for {page_id}", {"title": "Lucky Wheel Spec"})


class _FakeJira:
    def get_issue(self, key: str) -> dict:
        return {"key": key, "summary": f"Linked {key}", "status": "Done",
                "fields": {"description": {"type": "doc", "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "ngân sách 50tr"}]}]}}}


def test_resolve_mixes_in_system_and_skips_external(monkeypatch):
    monkeypatch.setattr(source_links, "ConfluenceClient", _FakeConfluence)
    adf = _doc(
        _text_with_link("spec", CONF_URL),
        {"type": "paragraph", "content": [{"type": "inlineCard", "attrs": {"url": JIRA_URL}}]},
        _text_with_link("blog", EXT_URL),
    )
    res = resolve_description_sources(adf, settings=SETTINGS, jira=_FakeJira())

    assert res.skipped_external == 1
    kinds = {s.kind for s in res.sources}
    assert kinds == {"confluence", "jira"}
    conf = next(s for s in res.sources if s.kind == "confluence")
    assert conf.title == "Lucky Wheel Spec"
    assert "Campaign spec for 12345" in conf.text
    jira_src = next(s for s in res.sources if s.kind == "jira")
    assert "ngân sách 50tr" in jira_src.text


def test_resolve_counts_unreadable_when_confluence_unconfigured(monkeypatch):
    class _Unconfigured(_FakeConfluence):
        def configured(self) -> bool:
            return False

    monkeypatch.setattr(source_links, "ConfluenceClient", _Unconfigured)
    res = resolve_description_sources(_doc(_text_with_link("spec", CONF_URL)),
                                      settings=SETTINGS, jira=None)
    assert res.sources == []
    assert res.unreadable == 1


def test_resolve_never_raises_on_reader_error(monkeypatch):
    class _Boom(_FakeConfluence):
        def fetch_page_body(self, page_id: str):
            raise RuntimeError("network down")

    monkeypatch.setattr(source_links, "ConfluenceClient", _Boom)
    res = resolve_description_sources(_doc(_text_with_link("spec", CONF_URL)),
                                      settings=SETTINGS, jira=None)
    assert res.sources == []
    assert res.unreadable == 1


def test_resolve_caps_number_of_sources(monkeypatch):
    monkeypatch.setattr(source_links, "ConfluenceClient", _FakeConfluence)
    links = [
        _text_with_link(f"p{i}", f"https://x.atlassian.net/wiki/spaces/R/pages/{i}/P")
        for i in range(source_links.MAX_SOURCES + 3)
    ]
    res = resolve_description_sources(_doc(*links), settings=SETTINGS, jira=None)
    assert len(res.sources) == source_links.MAX_SOURCES


def test_resolve_empty_description():
    res = resolve_description_sources(None, settings=SETTINGS, jira=None)
    assert res.sources == [] and res.skipped_external == 0 and res.unreadable == 0
