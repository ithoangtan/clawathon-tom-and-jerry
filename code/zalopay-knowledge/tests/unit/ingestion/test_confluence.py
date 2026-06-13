from __future__ import annotations

import hashlib
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.config import Settings
from app.ingestion.confluence import (
    ConfluenceClient,
    _extract_author,
    _extract_labels,
    _page_url,
    _storage_to_text,
)


class TestStorageToText:
    def test_empty_html_returns_empty_string(self):
        assert _storage_to_text("") == ""

    def test_converts_html_to_plain_text(self, sample_html: str):
        text = _storage_to_text(sample_html)
        assert "Risk Escalation Policy" in text
        assert "risk@zalopay.vn" in text
        assert "assess severity" in text
        assert "<h1>" not in text
        assert "<strong>" not in text

    def test_regex_fallback_when_beautifulsoup_fails(self, sample_html: str):
        with patch("bs4.BeautifulSoup", side_effect=RuntimeError("parser unavailable")):
            text = _storage_to_text(sample_html)
        assert "Risk Escalation Policy" in text
        assert "<h1>" not in text


class TestPageUrl:
    def test_builds_url_from_webui_link(self):
        base = "https://acme.atlassian.net/wiki"
        page = {"_links": {"webui": "/spaces/RISK/pages/123"}}
        assert _page_url(base, page) == "https://acme.atlassian.net/wiki/spaces/RISK/pages/123"

    def test_returns_absolute_webui_unchanged(self):
        url = "https://acme.atlassian.net/wiki/spaces/RISK/pages/1"
        page = {"_links": {"webui": url}}
        assert _page_url("https://acme.atlassian.net/wiki", page) == url


class TestPageMetadataHelpers:
    def test_extract_author_from_version_display_name(self):
        page = {"version": {"authorDisplayName": "Risk Owner"}}
        assert _extract_author(page) == "Risk Owner"

    def test_extract_labels_from_results_list(self):
        page = {"labels": {"results": [{"name": "ops-guidance"}, {"name": "policy"}]}}
        assert _extract_labels(page) == ["ops-guidance", "policy"]


class TestConfluenceClient:
    def test_configured_on_agentbase_with_identity_provider(self, tmp_path):
        settings = Settings(
            app_env="agentbase",
            greennode_agent_identity="zalopay-knowledge",
            confluence_api_key_provider="identity-confluence-zalopay-knowledge",
            confluence_base_url="https://acme.atlassian.net",
            confluence_email="bot@example.com",
            index_dir=str(tmp_path / "index"),
        )
        client = ConfluenceClient(settings)
        assert client.configured() is True

    def test_configured_when_credentials_present(self, confluence_settings: Settings):
        client = ConfluenceClient(confluence_settings)
        assert client.configured() is True

    def test_not_configured_when_missing_token(self, tmp_path):
        settings = Settings(
            confluence_base_url="https://acme.atlassian.net",
            confluence_email="bot@example.com",
            confluence_api_token="",
            index_dir=str(tmp_path / "index"),
        )
        client = ConfluenceClient(settings)
        assert client.configured() is False

    def test_base_url_appends_wiki_suffix(self):
        settings = Settings(
            confluence_base_url="https://acme.atlassian.net",
            confluence_email="a@b.com",
            confluence_api_token="tok",
        )
        client = ConfluenceClient(settings)
        assert client._base == "https://acme.atlassian.net/wiki"

    def test_list_pages_raises_when_not_configured(self, tmp_path):
        settings = Settings(
            app_env="local",
            confluence_base_url="",
            confluence_email="",
            confluence_api_token="",
            index_dir=str(tmp_path / "index"),
        )
        client = ConfluenceClient(settings)
        with pytest.raises(ValueError, match="not configured"):
            client.list_pages("RISK")

    def test_list_pages_v2_api(self, confluence_settings: Settings, confluence_list_response: dict):
        client = ConfluenceClient(confluence_settings)

        spaces_response = MagicMock()
        spaces_response.status_code = 200
        spaces_response.json.return_value = {"results": [{"id": "999"}]}

        pages_response = MagicMock()
        pages_response.status_code = 200
        pages_response.json.return_value = confluence_list_response
        pages_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.side_effect = [spaces_response, pages_response]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.ingestion.confluence.httpx.Client", return_value=mock_client):
            pages = client.list_pages("RISK")

        assert len(pages) == 2
        assert pages[0]["id"] == "12345"
        assert mock_client.get.call_count == 2
        spaces_call = mock_client.get.call_args_list[0]
        assert "/api/v2/spaces" in spaces_call[0][0]
        pages_call = mock_client.get.call_args_list[1]
        assert "/api/v2/pages" in pages_call[0][0]
        assert pages_call[1]["params"]["space-id"] == "999"

    def test_list_pages_falls_back_to_search_when_space_id_not_resolved(self, confluence_settings: Settings):
        client = ConfluenceClient(confluence_settings)

        spaces_not_found = MagicMock()
        spaces_not_found.status_code = 404

        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "results": [{"id": "99", "title": "CQL Page"}],
        }
        search_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.side_effect = [spaces_not_found, search_response]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.ingestion.confluence.httpx.Client", return_value=mock_client):
            pages = client.list_pages("RISK")

        assert len(pages) == 1
        assert pages[0]["title"] == "CQL Page"
        assert mock_client.get.call_count == 2
        assert "/rest/api/content/search" in mock_client.get.call_args_list[1][0][0]

    def test_list_pages_falls_back_to_search_on_400(self, confluence_settings: Settings):
        client = ConfluenceClient(confluence_settings)

        spaces_response = MagicMock()
        spaces_response.status_code = 200
        spaces_response.json.return_value = {"results": [{"id": "999"}]}

        bad_request = MagicMock()
        bad_request.status_code = 400

        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {"results": [{"id": "99", "title": "CQL Page"}]}
        search_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.side_effect = [spaces_response, bad_request, search_response]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.ingestion.confluence.httpx.Client", return_value=mock_client):
            pages = client.list_pages("RISK")

        assert pages[0]["title"] == "CQL Page"
        assert "/rest/api/content/search" in mock_client.get.call_args_list[2][0][0]

    def test_list_pages_returns_empty_when_space_not_found(self, confluence_settings: Settings):
        client = ConfluenceClient(confluence_settings)
        not_found = MagicMock()
        not_found.status_code = 404

        mock_client = MagicMock()
        mock_client.get.side_effect = [not_found, not_found]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.ingestion.confluence.httpx.Client", return_value=mock_client):
            pages = client.list_pages("ClawathonGrow")

        assert pages == []

    def test_fetch_page_body_extracts_text_and_metadata(
        self,
        confluence_settings: Settings,
        confluence_page_response: dict,
    ):
        client = ConfluenceClient(confluence_settings)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = confluence_page_response
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.ingestion.confluence.httpx.Client", return_value=mock_client):
            text, meta = client.fetch_page_body("12345")

        assert "Risk Escalation Policy" in text
        assert meta["title"] == "Risk Escalation Policy"
        assert meta["version"] == 3
        assert meta["last_modified"] == "2025-01-15T10:00:00Z"
        assert meta["source"] == "12345"
        assert "/wiki/spaces/RISK/pages/12345" in meta["url"]

    def test_content_hash_skip_unchanged_body(self, confluence_settings: Settings):
        """Same page body yields identical content hash — skip re-chunking signal."""
        client = ConfluenceClient(confluence_settings)
        storage_html = "<p>Unchanged policy text for hash comparison.</p>"

        def make_response(version: int) -> MagicMock:
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {
                "id": "1",
                "title": "Policy",
                "version": {"number": version, "createdAt": f"2025-01-0{version}T00:00:00Z"},
                "_links": {"webui": "/pages/1"},
                "body": {"storage": {"value": storage_html}},
            }
            resp.raise_for_status = MagicMock()
            return resp

        mock_client = MagicMock()
        mock_client.get.side_effect = [make_response(1), make_response(2)]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.ingestion.confluence.httpx.Client", return_value=mock_client):
            text_v1, _ = client.fetch_page_body("1")
            text_v2, meta_v2 = client.fetch_page_body("1")

        assert text_v1 == text_v2
        content_hash = hashlib.sha256(text_v1.encode()).hexdigest()
        assert content_hash == hashlib.sha256(text_v2.encode()).hexdigest()
        # Version bumped but body unchanged — hash-based skip would apply.
        assert meta_v2["version"] == 2

    def test_fetch_page_body_raises_on_http_error(self, confluence_settings: Settings):
        client = ConfluenceClient(confluence_settings)
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden",
            request=MagicMock(),
            response=mock_response,
        )

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch("app.ingestion.confluence.httpx.Client", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                client.fetch_page_body("999")
