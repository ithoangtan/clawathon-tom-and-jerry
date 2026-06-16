from __future__ import annotations

"""Resolve document links found in a Jira ticket into readable text.

A workflow step/trigger can instruct the agent to "read the doc link in the
ticket Description". *Which* link to read is **data** declared on the Confluence
workflow page; this module is the **code** that turns a link into content — but
only for links that point at systems we already integrate with:

- **Confluence** (`/wiki/.../pages/<id>`) → :meth:`ConfluenceClient.fetch_page_body`
- **Jira** (`/browse/<KEY>`)              → :meth:`JiraPort.get_issue`
- **Google Drive** (`drive|docs.google.com/.../d/<id>`, PDF) → :class:`GDriveClient`

Any link outside these in-system sources is **skipped** (counted, never fetched).
Every per-link failure degrades to a skip — the resolver never raises.
"""

import logging
import re
from dataclasses import dataclass, field

from app.config import Settings
from app.ingestion.confluence import ConfluenceClient
from app.ports.jira import JiraPort

logger = logging.getLogger(__name__)

# Bounds so one ticket with many links can't blow up the LLM context. A single
# campaign spec (info + full T&C) runs a few thousand chars, so the per-source cap
# must be large enough to keep the compliance evidence (else the reviewer marks
# rules "unclear" and can't reach PASS).
MAX_SOURCES = 4
MAX_CHARS_PER_SOURCE = 8000

# ── Link classification patterns (path-based; Jira & Confluence share a host) ──
_RE_CONFLUENCE_PAGE = re.compile(r"/wiki/(?:[^?#]*?/)?pages/(\d+)", re.IGNORECASE)
_RE_CONFLUENCE_PAGEID = re.compile(r"[?&]pageId=(\d+)", re.IGNORECASE)
_RE_JIRA_BROWSE = re.compile(r"/browse/([A-Z][A-Z0-9]+-\d+)", re.IGNORECASE)
_RE_GDRIVE = re.compile(r"(?:drive|docs)\.google\.com/[^?#]*?/d/([A-Za-z0-9_-]+)", re.IGNORECASE)
# Bare URLs inside plain text nodes.
_RE_URL = re.compile(r"https?://[^\s\"'<>)\]]+")


@dataclass
class ResolvedSource:
    """One successfully-read in-system document."""

    kind: str  # "confluence" | "jira" | "gdrive"
    ident: str
    title: str
    url: str
    text: str


@dataclass
class ResolutionResult:
    """Outcome of resolving every link found in a ticket Description."""

    sources: list[ResolvedSource] = field(default_factory=list)
    skipped_external: int = 0  # links to systems we don't integrate with
    unreadable: int = 0  # in-system links that errored / were unconfigured


def adf_to_text(adf: object) -> str:
    """Flatten an Atlassian Document Format value into plain text.

    Walks the node tree collecting ``text`` leaves; tolerant of ``None`` and of
    plain strings (returned as-is).
    """
    if adf is None:
        return ""
    if isinstance(adf, str):
        return adf
    if not isinstance(adf, dict):
        return ""
    out: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text" and isinstance(node.get("text"), str):
                out.append(node["text"])
            for child in node.get("content", []) or []:
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(adf)
    return " ".join(s for s in (p.strip() for p in out) if s).strip()


def extract_urls_from_adf(adf: object) -> list[str]:
    """Collect every URL referenced in a Jira description ADF, in order, deduped.

    Sources of URLs: ``link`` marks on text nodes, ``inlineCard``/``blockCard``
    ``attrs.url``, and bare ``http(s)`` URLs inside plain text.
    """
    urls: list[str] = []
    seen: set[str] = set()

    def add(url: object) -> None:
        if isinstance(url, str):
            u = url.strip()
            if u and u not in seen:
                seen.add(u)
                urls.append(u)

    def walk(node: object) -> None:
        if isinstance(node, dict):
            ntype = node.get("type")
            attrs = node.get("attrs") or {}
            if ntype in ("inlineCard", "blockCard", "embedCard"):
                add(attrs.get("url"))
            for mark in node.get("marks", []) or []:
                if isinstance(mark, dict) and mark.get("type") == "link":
                    add((mark.get("attrs") or {}).get("href"))
            if ntype == "text" and isinstance(node.get("text"), str):
                for m in _RE_URL.findall(node["text"]):
                    add(m)
            for child in node.get("content", []) or []:
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, str):
            for m in _RE_URL.findall(node):
                add(m)

    walk(adf)
    return urls


def classify_link(url: str) -> tuple[str | None, str]:
    """Map a URL to an in-system ``(kind, identifier)`` or ``(None, "")``.

    Confluence is checked before Jira because both live on the same Atlassian
    host and are distinguished only by path.
    """
    if not isinstance(url, str) or not url.strip():
        return None, ""
    m = _RE_CONFLUENCE_PAGE.search(url) or _RE_CONFLUENCE_PAGEID.search(url)
    if m:
        return "confluence", m.group(1)
    m = _RE_JIRA_BROWSE.search(url)
    if m:
        return "jira", m.group(1).upper()
    m = _RE_GDRIVE.search(url)
    if m:
        return "gdrive", m.group(1)
    return None, ""


def _cap(text: str) -> str:
    text = (text or "").strip()
    if len(text) > MAX_CHARS_PER_SOURCE:
        return text[:MAX_CHARS_PER_SOURCE].rstrip() + " […]"
    return text


def _read_confluence(ident: str, url: str, settings: Settings) -> ResolvedSource | None:
    client = ConfluenceClient(settings)
    if not client.configured():
        return None
    text, meta = client.fetch_page_body(ident)
    return ResolvedSource("confluence", ident, meta.get("title") or url, url, _cap(text))


def _read_jira(ident: str, url: str, jira: JiraPort | None) -> ResolvedSource | None:
    if jira is None:
        return None
    issue = jira.get_issue(ident)
    fields = issue.get("fields") or {}
    body = adf_to_text(fields.get("description"))
    summary = issue.get("summary") or ident
    text = f"{summary} (status: {issue.get('status', '')})\n{body}".strip()
    return ResolvedSource("jira", ident, summary, url, _cap(text))


def _read_gdrive(ident: str, url: str, settings: Settings) -> ResolvedSource | None:
    from app.ingestion.gdrive import GDriveClient  # lazy: pulls google libs

    client = GDriveClient(settings)
    if not client.configured():
        return None
    pages = client.extract_text(client.download_pdf(ident))
    text = "\n".join(t for _, t in pages)
    return ResolvedSource("gdrive", ident, url, url, _cap(text))


def resolve_description_sources(
    adf: object,
    *,
    settings: Settings,
    jira: JiraPort | None,
) -> ResolutionResult:
    """Read every in-system link found in *adf* (a Jira description).

    Out-of-system links are counted in ``skipped_external``; in-system links that
    error or are unconfigured are counted in ``unreadable``. Never raises.
    """
    result = ResolutionResult()
    for url in extract_urls_from_adf(adf):
        if len(result.sources) >= MAX_SOURCES:
            break
        kind, ident = classify_link(url)
        if not kind:
            result.skipped_external += 1
            continue
        try:
            if kind == "confluence":
                src = _read_confluence(ident, url, settings)
            elif kind == "jira":
                src = _read_jira(ident, url, jira)
            elif kind == "gdrive":
                src = _read_gdrive(ident, url, settings)
            else:  # pragma: no cover — classify_link only returns known kinds
                src = None
        except Exception as exc:  # noqa: BLE001 — one bad link must not fail the run
            logger.warning("source_links: read %s (%s) failed: %s", url, kind, exc)
            result.unreadable += 1
            continue
        if src is None or not src.text:
            result.unreadable += 1
            continue
        result.sources.append(src)
    return result
