from __future__ import annotations

"""Minimal Markdown → Confluence *storage* (XHTML) converter.

The repo has no Markdown library, and we only need to render the constructs that
appear in our internal policy/spec docs: ATX headings (``#``/``##``/``###``),
pipe tables (with a ``---`` separator row), bullet lists (``-``/``*``),
``**bold**``, horizontal rules (``---``), inline ``<br>``, and paragraphs.

This is intentionally small and deterministic — not a full CommonMark parser.
"""

import html
import re

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET = re.compile(r"^[-*]\s+(.*)$")
_HR = re.compile(r"^-{3,}$")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_TABLE_SEP_CELL = re.compile(r"^:?-{2,}:?$")
_ESCAPED_BR = re.compile(r"&lt;br\s*/?&gt;", re.IGNORECASE)


def _inline(text: str) -> str:
    """Escape XHTML special chars, then re-enable ``**bold**`` and ``<br>``."""
    t = html.escape(text, quote=False)
    t = _BOLD.sub(r"<strong>\1</strong>", t)
    t = _ESCAPED_BR.sub("<br/>", t)
    return t


def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(_TABLE_SEP_CELL.match(c) for c in cells if c)


def _render_table(rows: list[list[str]]) -> str:
    out = ["<table><tbody>"]
    for idx, cells in enumerate(rows):
        if _is_separator(cells):
            continue
        tag = "th" if idx == 0 else "td"
        cells_html = "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells)
        out.append(f"<tr>{cells_html}</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def md_to_storage(md: str) -> str:
    """Convert *md* to a Confluence storage-format XHTML string."""
    lines = (md or "").splitlines()
    html_parts: list[str] = []
    i, n = 0, len(lines)

    while i < n:
        raw = lines[i]
        line = raw.strip()
        if not line:
            i += 1
            continue

        if _HR.match(line):
            html_parts.append("<hr/>")
            i += 1
            continue

        m = _HEADING.match(line)
        if m:
            level = len(m.group(1))
            html_parts.append(f"<h{level}>{_inline(m.group(2).strip())}</h{level}>")
            i += 1
            continue

        if line.startswith("|"):
            rows: list[list[str]] = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(_split_row(lines[i]))
                i += 1
            html_parts.append(_render_table(rows))
            continue

        if _BULLET.match(line):
            items: list[str] = []
            while i < n and _BULLET.match(lines[i].strip()):
                items.append(_BULLET.match(lines[i].strip()).group(1).strip())
                i += 1
            html_parts.append("<ul>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ul>")
            continue

        html_parts.append(f"<p>{_inline(line)}</p>")
        i += 1

    return "".join(html_parts)
