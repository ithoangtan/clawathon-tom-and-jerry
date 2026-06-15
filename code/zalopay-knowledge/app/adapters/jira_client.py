from __future__ import annotations

"""JiraClient — JiraPort backed by Jira Cloud REST v3.

Credentials are **reused from Confluence**: Jira is the same Atlassian instance
and account, so we derive the Jira base URL from ``confluence_base_url`` (strip
the trailing ``/wiki``) and authenticate with ``confluence_email`` + the same
Atlassian API token. No dedicated ``JIRA_*`` env vars are introduced.

Stable values are hardcoded module constants (default project key), per the
"minimize env vars" decision for the workflow platform.
"""

import logging

import httpx

from app.adapters.confluence_credentials import (
    confluence_identity_ready,
    resolve_confluence_api_token,
)
from app.config import Settings
from app.ports.errors import JiraUnavailable

logger = logging.getLogger(__name__)

# Hardcoded defaults (see module docstring — minimize env vars for the demo).
DEFAULT_PROJECT_KEY = "KAN"
_TIMEOUT = 30.0


def _to_adf(text: str, *, code_block: str | None = None, code_language: str = "json") -> dict:
    """Wrap text into a minimal Atlassian Document Format doc.

    Jira Cloud v3 requires ADF for ``description`` and comment ``body``. Each
    non-empty line of *text* becomes a paragraph; an empty doc gets one empty
    paragraph. When *code_block* is given it is appended as an ADF ``codeBlock``
    node so Jira renders it as a fenced, syntax-highlighted block.
    """
    lines = (text or "").split("\n")
    content: list[dict] = []
    for line in lines:
        para_content = [{"type": "text", "text": line}] if line else []
        content.append({"type": "paragraph", "content": para_content})
    if code_block:
        content.append({
            "type": "codeBlock",
            "attrs": {"language": code_language},
            "content": [{"type": "text", "text": code_block}],
        })
    if not content:
        content = [{"type": "paragraph", "content": []}]
    return {"type": "doc", "version": 1, "content": content}


class JiraClient:
    """Minimal Jira Cloud v3 client (read issue, create issue/sub-task, comment)."""

    def __init__(
        self,
        settings: Settings,
        *,
        dry_run: bool = False,
        default_project: str = DEFAULT_PROJECT_KEY,
    ) -> None:
        self._settings = settings
        self._dry_run = dry_run
        self._default_project = default_project
        # Derive the Jira base from the Confluence base (same Atlassian site).
        base = (settings.confluence_base_url or "").rstrip("/")
        if base.endswith("/wiki"):
            base = base[: -len("/wiki")]
        self._base = base

    # ── Credentials / config ────────────────────────────────────────────────

    def _auth(self) -> tuple[str, str]:
        email = (self._settings.confluence_email or "").strip()
        token = resolve_confluence_api_token(self._settings)
        return (email, token)

    def configured(self) -> bool:
        """True when a base URL + email + a resolvable token are all available."""
        if not self._base or not (self._settings.confluence_email or "").strip():
            return False
        if self._settings.is_agentbase and confluence_identity_ready(self._settings):
            return True
        return bool((self._settings.confluence_api_token or "").strip())

    def _browse_url(self, key: str) -> str:
        return f"{self._base}/browse/{key}" if self._base else ""

    def _request(self, method: str, path: str, *, json: dict | None = None) -> dict:
        if not self.configured():
            raise JiraUnavailable("Jira credentials are not configured")
        url = f"{self._base}/rest/api/3/{path.lstrip('/')}"
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.request(method, url, auth=self._auth(), json=json)
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            logger.error("Jira %s %s failed: %s — %s", method, path, exc.response.status_code, body)
            raise JiraUnavailable(f"Jira {method} {path} → {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            logger.error("Jira %s %s transport error: %s", method, path, exc)
            raise JiraUnavailable(f"Jira request failed: {exc}") from exc

    # ── JiraPort ──────────────────────────────────────────────────────────────

    def get_issue(self, key: str) -> dict:
        data = self._request("GET", f"issue/{key}")
        fields = data.get("fields", {}) or {}
        status = ((fields.get("status") or {}).get("name")) if fields else None
        return {
            "key": data.get("key", key),
            "url": self._browse_url(data.get("key", key)),
            "summary": fields.get("summary", ""),
            "status": status,
            "fields": fields,
        }

    def create_issue(
        self,
        *,
        project: str | None = None,
        summary: str,
        description: str = "",
        issuetype: str = "Task",
        parent: str | None = None,
        assignee: str | None = None,
    ) -> dict:
        project_key = project or self._default_project
        if self._dry_run:
            logger.info("Jira dry-run create_issue: %s/%s %r", project_key, issuetype, summary)
            return {
                "key": "DRY-RUN",
                "url": "",
                "dry_run": True,
                "summary": summary,
                "issuetype": issuetype,
                "parent": parent,
                "project": project_key,
            }
        fields: dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": _to_adf(description),
            "issuetype": {"name": issuetype},
        }
        if parent:
            fields["parent"] = {"key": parent}
        if assignee:
            fields["assignee"] = {"accountId": assignee}
        data = self._request("POST", "issue", json={"fields": fields})
        key = data.get("key", "")
        return {"key": key, "url": self._browse_url(key), "dry_run": False, "raw": data}

    def add_comment(
        self,
        *,
        key: str,
        body: str,
        code_block: str | None = None,
        code_language: str = "json",
    ) -> dict:
        if self._dry_run:
            logger.info("Jira dry-run add_comment on %s: %r (code_block=%s)", key, body[:80], bool(code_block))
            return {"key": key, "url": self._browse_url(key), "dry_run": True, "body": body}
        adf = _to_adf(body, code_block=code_block, code_language=code_language)
        data = self._request("POST", f"issue/{key}/comment", json={"body": adf})
        return {
            "key": key,
            "url": self._browse_url(key),
            "comment_id": data.get("id"),
            "dry_run": False,
        }

    def add_labels(self, *, key: str, labels: list[str]) -> dict:
        clean = [str(x).strip() for x in labels if str(x).strip() and ":" not in str(x) and " " not in str(x)]
        if not clean:
            return {"key": key, "labels": [], "dry_run": self._dry_run}
        if self._dry_run:
            logger.info("Jira dry-run add_labels on %s: %s", key, clean)
            return {"key": key, "labels": clean, "dry_run": True}
        self._request("PUT", f"issue/{key}", json={"update": {"labels": [{"add": lbl} for lbl in clean]}})
        return {"key": key, "labels": clean, "dry_run": False}

    def is_ready(self) -> bool:
        """Cheap reachability + credential check. Never raises."""
        if not self.configured():
            return False
        try:
            self._request("GET", "myself")
            return True
        except JiraUnavailable:
            return False


class NullJiraClient:
    """No-op JiraPort used when Jira is unconfigured.

    ``get_issue``/``create_issue``/``add_comment`` raise :class:`JiraUnavailable`
    so workflow nodes degrade gracefully; ``is_ready`` is ``False``.
    """

    def get_issue(self, key: str) -> dict:
        raise JiraUnavailable("Jira is not configured")

    def create_issue(self, **_kwargs) -> dict:
        raise JiraUnavailable("Jira is not configured")

    def add_comment(self, **_kwargs) -> dict:
        raise JiraUnavailable("Jira is not configured")

    def add_labels(self, **_kwargs) -> dict:
        raise JiraUnavailable("Jira is not configured")

    def is_ready(self) -> bool:
        return False
