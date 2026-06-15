from __future__ import annotations

"""Confluence Cloud v2 REST client for the sync pipeline."""

import logging
import re
import time
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.adapters.confluence_credentials import confluence_identity_ready, resolve_confluence_api_token
from app.config import Settings

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Minimal Confluence Cloud v2 reader (MVP — direct REST, no MCP)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        base = (settings.confluence_base_url or "").rstrip("/")
        if not base.endswith("/wiki"):
            base = f"{base}/wiki" if base else ""
        self._base = base
        self._timeout = 30.0

    def _auth(self) -> tuple[str, str]:
        email = (self._settings.confluence_email or "").strip()
        token = resolve_confluence_api_token(self._settings)
        return (email, token)

    def configured(self) -> bool:
        if not self._base or not (self._settings.confluence_email or "").strip():
            return False
        if self._settings.is_agentbase and confluence_identity_ready(self._settings):
            return True
        return bool((self._settings.confluence_api_token or "").strip())

    def list_pages(self, space_key: str, *, limit: int = 50) -> list[dict[str, Any]]:
        """List pages in a space (paginated)."""
        if not self.configured():
            raise ValueError("Confluence credentials are not configured")

        logger.info("Confluence list_pages space=%r", space_key)
        t0 = time.monotonic()
        pages: list[dict[str, Any]] = []
        cursor: str | None = None
        try:
            with httpx.Client(timeout=self._timeout) as client:
                # Resolve space key → numeric space ID required by v2 API
                space_id = self._resolve_space_id(client, space_key)
                if space_id is None:
                    result = self._search_space_pages(client, space_key)
                    logger.info(
                        "Confluence list_pages space=%r → %d pages via CQL (%.0fms)",
                        space_key, len(result), (time.monotonic() - t0) * 1000,
                    )
                    return result

                while True:
                    params: dict[str, Any] = {"limit": limit, "space-id": space_id}
                    if cursor:
                        params["cursor"] = cursor
                    resp = client.get(f"{self._base}/api/v2/pages", params=params, auth=self._auth())
                    if resp.status_code in (400, 404):
                        result = self._search_space_pages(client, space_key)
                        logger.info(
                            "Confluence list_pages space=%r → %d pages via CQL (%.0fms)",
                            space_key, len(result), (time.monotonic() - t0) * 1000,
                        )
                        return result
                    resp.raise_for_status()
                    data = resp.json()
                    pages.extend(data.get("results", []))
                    cursor = (data.get("_links") or {}).get("next")
                    if not cursor or len(data.get("results", [])) < limit:
                        break
        except Exception as exc:
            logger.error(
                "Confluence list_pages space=%r failed (%.0fms): %s",
                space_key, (time.monotonic() - t0) * 1000, exc,
            )
            raise
        logger.info(
            "Confluence list_pages space=%r → %d pages (%.0fms)",
            space_key, len(pages), (time.monotonic() - t0) * 1000,
        )
        return pages

    def _resolve_space_id(self, client: httpx.Client, space_key: str) -> str | None:
        """Resolve a space key to its numeric ID via the v2 spaces API."""
        try:
            resp = client.get(
                f"{self._base}/api/v2/spaces",
                params={"keys": space_key, "limit": 1},
                auth=self._auth(),
            )
            if resp.status_code != 200:
                return None
            results = resp.json().get("results", [])
            if results:
                return str(results[0]["id"])
        except Exception as exc:
            logger.warning("Confluence _resolve_space_id space=%r failed: %s", space_key, exc)
        return None

    def _search_space_pages(self, client: httpx.Client, space_key: str) -> list[dict[str, Any]]:
        cql = f'space="{space_key}" and type=page'
        t0 = time.monotonic()
        try:
            resp = client.get(
                f"{self._base}/rest/api/content/search",
                params={"cql": cql, "limit": 50, "expand": "version"},
                auth=self._auth(),
            )
            if resp.status_code == 404:
                logger.warning(
                    "Confluence space %r not found (404) — skipping. "
                    "Check CONFLUENCE_SPACES env var for the correct space key.",
                    space_key,
                )
                return []
            resp.raise_for_status()
            results = resp.json().get("results", [])
            logger.info(
                "Confluence search space=%r → %d pages (%.0fms)",
                space_key, len(results), (time.monotonic() - t0) * 1000,
            )
            return results
        except Exception as exc:
            logger.error(
                "Confluence search space=%r failed (%.0fms): %s",
                space_key, (time.monotonic() - t0) * 1000, exc,
            )
            raise

    def _fetch_labels(self, client: httpx.Client, page_id: str) -> list[str]:
        """Fetch a page's label names via the dedicated v2 labels endpoint.

        Returns an empty list on any error (labels are best-effort metadata —
        never fail a page sync over them).
        """
        try:
            resp = client.get(
                f"{self._base}/api/v2/pages/{page_id}/labels",
                params={"limit": 50},
                auth=self._auth(),
            )
            if resp.status_code != 200:
                return []
            results = resp.json().get("results", [])
            return [str(r["name"]) for r in results if isinstance(r, dict) and r.get("name")]
        except Exception as exc:  # noqa: BLE001 — labels are non-critical
            logger.warning("Confluence _fetch_labels page_id=%s failed: %s", page_id, exc)
            return []

    def fetch_page_body(self, page_id: str) -> tuple[str, dict[str, Any]]:
        """Return (plain_text, metadata) for a page."""
        logger.info("Confluence fetch_page page_id=%s", page_id)
        t0 = time.monotonic()
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(
                    f"{self._base}/api/v2/pages/{page_id}",
                    params={"body-format": "storage"},
                    auth=self._auth(),
                )
                resp.raise_for_status()
                data = resp.json()
                storage = (
                    data.get("body", {}).get("storage", {}).get("value", "")
                )
                text = _storage_to_text(storage)
                # The v2 page payload does not embed labels — fetch them from the
                # dedicated endpoint so label-based filtering (e.g. the workflow
                # registry's ``zalopay-workflow`` / ``status:active``) works.
                labels = _extract_labels(data) or self._fetch_labels(client, page_id)
                meta = {
                    "title": data.get("title", ""),
                    "url": _page_url(self._base, data),
                    "last_modified": (data.get("version") or {}).get("createdAt"),
                    "version": (data.get("version") or {}).get("number"),
                    "source": page_id,
                    "author": _extract_author(data),
                    "labels": labels,
                }
                logger.info(
                    "Confluence fetch_page page_id=%s title=%r chars=%d (%.0fms)",
                    page_id, meta["title"], len(text), (time.monotonic() - t0) * 1000,
                )
                return text, meta
        except Exception as exc:
            logger.error(
                "Confluence fetch_page page_id=%s failed (%.0fms): %s",
                page_id, (time.monotonic() - t0) * 1000, exc,
            )
            raise


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
