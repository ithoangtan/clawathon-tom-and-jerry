from __future__ import annotations

"""ConfluenceWriter — ConfluenceWriterPort backed by Confluence Cloud REST.

Reuses the Confluence Atlassian credentials (same as the read client and Jira):
``confluence_base_url`` + ``confluence_email`` + the resolved API token. No new
env vars. Pages are written in Confluence *storage* (XHTML) format via the v2
API; labels via the v1 label endpoint (v2 has no label-create).

All HTTP goes through :meth:`_request`, so tests monkeypatch that one method.
"""

import logging

import httpx

from app.adapters.confluence_credentials import (
    confluence_identity_ready,
    resolve_confluence_api_token,
)
from app.config import Settings
from app.ports.errors import ConfluenceUnavailable

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0


def text_to_storage(text: str) -> str:
    """Wrap plain text into minimal storage-format paragraphs (XHTML)."""
    import html

    paras = [f"<p>{html.escape(line)}</p>" for line in (text or "").split("\n") if line.strip()]
    return "".join(paras) or "<p></p>"


class ConfluenceWriter:
    """Minimal Confluence Cloud v2 writer (create/update/append page, add labels)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        base = (settings.confluence_base_url or "").rstrip("/")
        if base and not base.endswith("/wiki"):
            base = f"{base}/wiki"
        self._base = base

    # ── Credentials ───────────────────────────────────────────────────────────

    def _auth(self) -> tuple[str, str]:
        return ((self._settings.confluence_email or "").strip(), resolve_confluence_api_token(self._settings))

    def is_ready(self) -> bool:
        if not self._base or not (self._settings.confluence_email or "").strip():
            return False
        if self._settings.is_agentbase and confluence_identity_ready(self._settings):
            return True
        return bool((self._settings.confluence_api_token or "").strip())

    def _page_url(self, space_key: str, page_id: str) -> str:
        return f"{self._base}/spaces/{space_key}/pages/{page_id}" if self._base else ""

    def _request(self, method: str, path: str, *, json: dict | None = None, api: str = "v2") -> dict:
        if not self.is_ready():
            raise ConfluenceUnavailable("Confluence write credentials are not configured")
        root = f"{self._base}/api/v2" if api == "v2" else f"{self._base}/rest/api"
        url = f"{root}/{path.lstrip('/')}"
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.request(method, url, auth=self._auth(), json=json)
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            logger.error("Confluence %s %s → %s: %s", method, path, exc.response.status_code, body)
            raise ConfluenceUnavailable(f"Confluence {method} {path} → {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            logger.error("Confluence %s %s transport error: %s", method, path, exc)
            raise ConfluenceUnavailable(f"Confluence request failed: {exc}") from exc

    # ── ConfluenceWriterPort ────────────────────────────────────────────────────

    def _resolve_space_id(self, space_key: str) -> str:
        data = self._request("GET", f"spaces?keys={space_key}&limit=1")
        results = data.get("results", [])
        if not results:
            raise ConfluenceUnavailable(f"Confluence space {space_key!r} not found")
        return str(results[0]["id"])

    def create_page(self, *, space_key: str, title: str, body_storage: str) -> dict:
        space_id = self._resolve_space_id(space_key)
        data = self._request("POST", "pages", json={
            "spaceId": space_id, "status": "current", "title": title,
            "body": {"representation": "storage", "value": body_storage},
        })
        page_id = str(data.get("id", ""))
        return {"id": page_id, "url": self._page_url(space_key, page_id)}

    def _get_page(self, page_id: str) -> dict:
        return self._request("GET", f"pages/{page_id}?body-format=storage")

    def _put_body(self, *, page_id: str, cur: dict, title: str, body_storage: str) -> dict:
        """Write a new version from an already-fetched page payload (one PUT)."""
        version = int((cur.get("version") or {}).get("number", 1)) + 1
        space_id = str(cur.get("spaceId", ""))
        data = self._request("PUT", f"pages/{page_id}", json={
            "id": page_id, "status": "current", "title": title, "spaceId": space_id,
            "body": {"representation": "storage", "value": body_storage},
            "version": {"number": version},
        })
        return {"id": page_id, "url": (data.get("_links") or {}).get("webui", ""), "version": version}

    def update_page(self, *, page_id: str, title: str, body_storage: str) -> dict:
        cur = self._get_page(page_id)
        return self._put_body(page_id=page_id, cur=cur, title=title, body_storage=body_storage)

    def append_to_page(self, *, page_id: str, html_fragment: str) -> dict:
        cur = self._get_page(page_id)
        existing = (cur.get("body") or {}).get("storage", {}).get("value", "")
        return self._put_body(
            page_id=page_id, cur=cur, title=cur.get("title", ""),
            body_storage=existing + html_fragment,
        )

    def add_labels(self, *, page_id: str, labels: list[str]) -> list[str]:
        # v1 label endpoint; v2 has no label-create. Colons are rejected by Confluence.
        payload = [{"prefix": "global", "name": name} for name in labels if ":" not in name]
        data = self._request("POST", f"content/{page_id}/label", json=payload, api="v1")
        return [r["name"] for r in data.get("results", []) if r.get("name")]


class NullConfluenceWriter:
    """No-op writer used when Confluence is unconfigured — actions degrade gracefully."""

    def create_page(self, **_kwargs) -> dict:
        raise ConfluenceUnavailable("Confluence is not configured")

    def update_page(self, **_kwargs) -> dict:
        raise ConfluenceUnavailable("Confluence is not configured")

    def append_to_page(self, **_kwargs) -> dict:
        raise ConfluenceUnavailable("Confluence is not configured")

    def add_labels(self, **_kwargs) -> list[str]:
        raise ConfluenceUnavailable("Confluence is not configured")

    def is_ready(self) -> bool:
        return False
