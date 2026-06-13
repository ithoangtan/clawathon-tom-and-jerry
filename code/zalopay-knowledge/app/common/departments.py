from __future__ import annotations

"""Canonical department registry for the ZaloPay Knowledge Agent.

All other modules that need department metadata import from here — never
hard-code department keys or display names elsewhere.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Iterator


# ── Department enum ───────────────────────────────────────────────────────────

class DepartmentKey(str, Enum):
    """Stable string keys for the three supported departments."""

    RISK = "risk"
    GROW_ENABLEMENT = "grow_enablement"
    BANK_PARTNERSHIPS = "bank_partnerships"


# ── Department descriptor ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Department:
    """All metadata for a single department."""

    key: str
    """Stable identifier used in API payloads and FAISS partition names."""

    name_en: str
    """English display name."""

    name_vi: str
    """Vietnamese display name."""

    space_env_var: str
    """Name of the environment variable that holds the Confluence space key."""

    accent_color: str
    """Hex color for UI badges / department chips."""

    channel_hint: str
    """Teams / Slack channel name users can contact for manual help."""

    def display_name(self, lang: str = "en") -> str:
        """Return the display name for the given language code."""
        if lang == "vi":
            return self.name_vi
        return self.name_en


# ── Registry ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, Department] = {
    DepartmentKey.RISK: Department(
        key=DepartmentKey.RISK,
        name_en="Risk",
        name_vi="Quản lý Rủi ro",
        space_env_var="CONFLUENCE_SPACE_RISK",
        accent_color="#E63946",  # assertive red — risk theme
        channel_hint="teams-risk-knowledge",
    ),
    DepartmentKey.GROW_ENABLEMENT: Department(
        key=DepartmentKey.GROW_ENABLEMENT,
        name_en="Grow Enablement",
        name_vi="Phát triển Kinh doanh",
        space_env_var="CONFLUENCE_SPACE_GROW",
        accent_color="#2A9D8F",  # teal-green — growth theme
        channel_hint="teams-grow-enablement-knowledge",
    ),
    DepartmentKey.BANK_PARTNERSHIPS: Department(
        key=DepartmentKey.BANK_PARTNERSHIPS,
        name_en="Bank Partnerships",
        name_vi="Đối tác Ngân hàng",
        space_env_var="CONFLUENCE_SPACE_BANK",
        accent_color="#457B9D",  # corporate blue — banking theme
        channel_hint="teams-bank-partnerships-knowledge",
    ),
}


# ── Role constants ────────────────────────────────────────────────────────────

ROLES: list[str] = ["engineer", "pm", "ops", "risk", "business"]
"""All recognised user roles in priority order (first = highest-privilege)."""


# ── Public helpers ─────────────────────────────────────────────────────────────

def all_departments() -> list[Department]:
    """Return all departments in a stable, deterministic order."""
    return [_REGISTRY[k] for k in (
        DepartmentKey.RISK,
        DepartmentKey.GROW_ENABLEMENT,
        DepartmentKey.BANK_PARTNERSHIPS,
    )]


def get_department(key: str) -> Department:
    """Return the Department for *key*, raising KeyError for unknown keys."""
    try:
        return _REGISTRY[key]
    except KeyError:
        valid = list(_REGISTRY.keys())
        raise KeyError(f"Unknown department key {key!r}. Valid keys: {valid}") from None


def space_env_var(key: str) -> str:
    """Return the name of the env var that holds *key*'s Confluence space key."""
    return get_department(key).space_env_var


def department_catalog_text(lang: str = "en") -> str:
    """Render a human-readable catalog for use in prompt templates.

    Example output (lang='en')::

        - risk: Risk (teams-risk-knowledge)
        - grow_enablement: Grow Enablement (teams-grow-enablement-knowledge)
        - bank_partnerships: Bank Partnerships (teams-bank-partnerships-knowledge)
    """
    lines: list[str] = []
    for dept in all_departments():
        lines.append(
            f"- {dept.key}: {dept.display_name(lang)} (contact: {dept.channel_hint})"
        )
    return "\n".join(lines)


def iter_keys() -> Iterator[str]:
    """Iterate over all department key strings."""
    for dept in all_departments():
        yield dept.key
