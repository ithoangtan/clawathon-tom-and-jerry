from __future__ import annotations

"""Chunk metadata contract for the ingestion pipeline (FR-5.3 / checklist §4)."""

import json
from typing import Any

# Canonical doc types per G6 / 01-PROBLEM-AND-GOALS.md
DOC_TYPES: frozenset[str] = frozenset(
    {
        "PRD",
        "Operation",
        "Technical",
        "Risk",
        "Security",
        "Org-structure",
        "RCA",
        "Ops-guidance",
    }
)

# MVP corpus is all-employee-readable; ACL filter deferred to ROLLOUT.
MVP_ACL_DEFAULT: list[str] = ["all-employees"]

# Fields required on every indexed chunk row (values may be null except acl).
REQUIRED_CHUNK_METADATA_FIELDS: tuple[str, ...] = (
    "source",
    "url",
    "anchor",
    "section",
    "space",
    "labels",
    "last_modified",
    "author",
    "doc_type",
    "acl",
)


def default_acl() -> list[str]:
    """Return the MVP ACL placeholder applied when none is supplied at ingest."""
    return list(MVP_ACL_DEFAULT)


def serialize_labels(labels: list[str] | None) -> str:
    """Encode Confluence labels (or empty list) as JSON for SQLite storage."""
    return json.dumps(sorted(set(labels or [])), ensure_ascii=False)


def serialize_acl(acl: list[str] | None) -> str:
    """Encode ACL groups as JSON; defaults to :data:`MVP_ACL_DEFAULT`."""
    value = acl if acl is not None else default_acl()
    return json.dumps(value, ensure_ascii=False)


def parse_labels(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [str(x) for x in parsed] if isinstance(parsed, list) else []


def parse_acl(raw: str | None) -> list[str]:
    if not raw:
        return default_acl()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return default_acl()
    return [str(x) for x in parsed] if isinstance(parsed, list) else default_acl()


def slugify_heading(title: str) -> str:
    """Build a URL-safe anchor slug from a section heading."""
    slug = title.strip().lower()
    for ch in ("'", '"', "“", "”", "‘", "’"):
        slug = slug.replace(ch, "")
    slug = slug.replace("&", "and")
    allowed = []
    for ch in slug:
        if ch.isalnum() or ch in (" ", "-", "_"):
            allowed.append(ch)
    slug = "".join(allowed)
    slug = "-".join(part for part in slug.replace("_", " ").split() if part)
    return slug


def chunk_metadata_defaults(**overrides: Any) -> dict[str, Any]:
    """Build metadata field defaults merged with *overrides* for :func:`chunk_text`."""
    base: dict[str, Any] = {
        "source": None,
        "space": None,
        "labels": serialize_labels(None),
        "author": None,
        "acl": serialize_acl(None),
    }
    if "labels" in overrides and not isinstance(overrides["labels"], str):
        overrides = {**overrides, "labels": serialize_labels(overrides["labels"])}
    if "acl" in overrides and not isinstance(overrides["acl"], str):
        overrides = {**overrides, "acl": serialize_acl(overrides["acl"])}
    base.update(overrides)
    return base
