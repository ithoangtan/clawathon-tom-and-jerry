from __future__ import annotations

"""Confluence Cloud v2 REST client for the sync pipeline."""

import logging
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.config import Settings

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Minimal Confluence Cloud v2 reader (MVP — direct REST, no MCP)."""

    def __init__(self, settings: Settings) -> None:
        base = (settings.confluence_base_url or "").rstrip("/")
        if not base.endswith("/wiki"):
            base = f"{base}/wiki" if base else ""
        self._base = base
        self._auth = (settings.confluence_email, settings.confluence_api_token)
        self._timeout = 30.0

    def configured(self) -> bool:
        return bool(self._base and self._auth[0] and self._auth[1])

    def list_pages(self, space_key: str, *, limit: int = 50) -> list[dict[str, Any]]:
        """List pages in a space (paginated)."""
        if not self.configured():
            raise ValueError("Confluence credentials are not configured")

        pages: list[dict[str, Any]] = []
        cursor: str | None = None
        with httpx.Client(timeout=self._timeout) as client:
            while True:
                params: dict[str, Any] = {"limit": limit, "space-id": space_key}
                if cursor:
                    params["cursor"] = cursor
                # v2 spaces/{id}/pages — space_key used as key filter via CQL fallback
                url = f"{self._base}/api/v2/pages"
                params["space-key"] = space_key
                resp = client.get(url, params=params, auth=self._auth)
                if resp.status_code == 404:
                    # Fallback: search API with CQL
                    return self._search_space_pages(client, space_key)
                resp.raise_for_status()
                data = resp.json()
                pages.extend(data.get("results", []))
                cursor = (data.get("_links") or {}).get("next")
                if not cursor or len(data.get("results", [])) < limit:
                    break
        return pages

    def _search_space_pages(self, client: httpx.Client, space_key: str) -> list[dict[str, Any]]:
        cql = f'space="{space_key}" and type=page'
        resp = client.get(
            f"{self._base}/rest/api/content/search",
            params={"cql": cql, "limit": 50, "expand": "version"},
            auth=self._auth,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])

    def fetch_page_body(self, page_id: str) -> tuple[str, dict[str, Any]]:
        """Return (plain_text, metadata) for a page."""
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(
                f"{self._base}/api/v2/pages/{page_id}",
                params={"body-format": "storage"},
                auth=self._auth,
            )
            resp.raise_for_status()
            data = resp.json()
            storage = (
                data.get("body", {}).get("storage", {}).get("value", "")
            )
            text = _storage_to_text(storage)
            meta = {
                "title": data.get("title", ""),
                "url": _page_url(self._base, data),
                "last_modified": (data.get("version") or {}).get("createdAt"),
                "version": (data.get("version") or {}).get("number"),
                "source": page_id,
                "author": _extract_author(data),
                "labels": _extract_labels(data),
            }
            return text, meta


def _page_url(base: str, page: dict[str, Any]) -> str:
    links = page.get("_links") or {}
    webui = links.get("webui") or links.get("tinyui") or ""
    if webui.startswith("http"):
        return webui
    site = base.replace("/wiki", "")
    return f"{site}/wiki{webui}" if webui else base


def _extract_author(page: dict[str, Any]) -> str | None:
    """Best-effort author from Confluence v2 page/version payloads."""
    version = page.get("version") or {}
    for key in ("authorDisplayName", "createdBy", "authorId"):
        value = version.get(key)
        if value:
            return str(value)
    for key in ("authorId", "ownerId", "createdBy"):
        value = page.get(key)
        if value:
            return str(value)
    return None


def _extract_labels(page: dict[str, Any]) -> list[str]:
    """Return label names when the API embeds them; otherwise an empty list."""
    raw = page.get("labels")
    if isinstance(raw, dict):
        results = raw.get("results") or raw.get("values") or []
    elif isinstance(raw, list):
        results = raw
    else:
        metadata = page.get("metadata") or {}
        labels_meta = metadata.get("labels") if isinstance(metadata, dict) else None
        if isinstance(labels_meta, dict):
            results = labels_meta.get("results") or []
        else:
            return []

    labels: list[str] = []
    for item in results:
        if isinstance(item, str):
            labels.append(item)
        elif isinstance(item, dict):
            name = item.get("name") or item.get("label")
            if name:
                labels.append(str(name))
    return labels


def _storage_to_text(html: str) -> str:
    if not html:
        return ""
    try:
        return BeautifulSoup(html, "lxml").get_text("\n", strip=True)
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)
