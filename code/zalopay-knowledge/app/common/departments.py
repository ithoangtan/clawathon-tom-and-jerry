from __future__ import annotations

"""Canonical department registry for the Zalopay Knowledge Agent.

All other modules that need department metadata import from here — never
hard-code department keys or display names elsewhere.
"""

import json
import logging
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Iterator


logger = logging.getLogger(__name__)


# ── Department enum ───────────────────────────────────────────────────────────

class DepartmentKey(str, Enum):
    """Stable string keys for supported departments — the only literal key definitions."""

    RISK = "risk"
    GROW_ENABLEMENT = "grow_enablement"
    BANK_PARTNERSHIPS = "bank_partnerships"


DEFAULT_HOME_DEPARTMENT = DepartmentKey.RISK


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
    """Legacy per-department env var (merged into ``CONFLUENCE_SPACES`` at startup)."""

    accent_color: str
    """Hex color for UI badges / department chips."""

    channel_hint: str
    """Teams / Slack channel name users can contact for manual help."""

    head_manager_en: str
    """English name of the department head / manager."""

    head_manager_vi: str
    """Vietnamese name of the department head / manager."""

    description_en: str
    """Short English blurb for UI search and routing hints."""

    description_vi: str
    """Short Vietnamese blurb for UI search and routing hints."""

    default_doc_type: str = "Operation"
    """Default document-type label when chunker heuristics find no match."""

    gdrive_pdf_source: bool = False
    """When true, GDrive PDF sync indexes into this department's partition."""

    def display_name(self, lang: str = "en") -> str:
        """Return the display name for the given language code."""
        if lang == "vi":
            return self.name_vi
        return self.name_en


# ── Registry ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, Department] = {
    DepartmentKey.RISK.value: Department(
        key=DepartmentKey.RISK.value,
        name_en="Risk Management",
        name_vi="Quản lý Rủi ro",
        space_env_var="CONFLUENCE_SPACE_RISK",
        accent_color="#E63946",
        channel_hint="teams-risk-knowledge",
        head_manager_en="Lan Nguyen",
        head_manager_vi="Nguyễn Thị Lan",
        description_en="Risk controls, fraud monitoring, compliance policies, and incident escalation.",
        description_vi="Kiểm soát rủi ro, giám sát gian lận, chính sách tuân thủ và leo thang sự cố.",
        default_doc_type="Risk",
    ),
    DepartmentKey.GROW_ENABLEMENT.value: Department(
        key=DepartmentKey.GROW_ENABLEMENT.value,
        name_en="Growth Enablement",
        name_vi="Phát triển Kinh doanh",
        space_env_var="CONFLUENCE_SPACE_GROW",
        accent_color="#2A9D8F",
        channel_hint="teams-grow-enablement-knowledge",
        head_manager_en="Minh Tran",
        head_manager_vi="Trần Văn Minh",
        description_en="Merchant growth programs, onboarding playbooks, and enablement runbooks.",
        description_vi="Chương trình phát triển merchant, playbook onboarding và runbook enablement.",
        default_doc_type="Operation",
    ),
    DepartmentKey.BANK_PARTNERSHIPS.value: Department(
        key=DepartmentKey.BANK_PARTNERSHIPS.value,
        name_en="Bank Partnerships",
        name_vi="Đối tác Ngân hàng",
        space_env_var="CONFLUENCE_SPACE_BANK",
        accent_color="#457B9D",
        channel_hint="teams-bank-partnerships-knowledge",
        head_manager_en="Hoang Le",
        head_manager_vi="Lê Hoàng",
        description_en="Bank integrations, settlement reconciliation, and partner SLA documentation.",
        description_vi="Tích hợp ngân hàng, đối soát thanh toán và tài liệu SLA đối tác.",
        default_doc_type="Technical",
        gdrive_pdf_source=True,
    ),
}


# ── Role constants ────────────────────────────────────────────────────────────

ROLES: list[str] = ["engineer", "pm", "ops", "risk", "business"]
"""All recognised user roles in priority order (first = highest-privilege)."""


# ── Public helpers ─────────────────────────────────────────────────────────────

def all_departments() -> list[Department]:
    """Return all departments in enum declaration order."""
    return [_REGISTRY[member.value] for member in DepartmentKey]


def get_department(key: str) -> Department:
    """Return the Department for *key*, raising KeyError for unknown keys."""
    try:
        return _REGISTRY[key]
    except KeyError:
        valid = list(_REGISTRY.keys())
        raise KeyError(f"Unknown department key {key!r}. Valid keys: {valid}") from None


def department_keys_set() -> frozenset[str]:
    """Return the set of valid department key strings."""
    return frozenset(_REGISTRY.keys())


def space_env_var(key: str) -> str:
    """Return the name of the env var that holds *key*'s Confluence space key."""
    return get_department(key).space_env_var


def default_doc_type(department_key: str) -> str:
    """Return the default doc-type label for chunks in *department_key*."""
    return get_department(department_key).default_doc_type


def gdrive_department_key() -> str:
    """Return the department key that receives GDrive PDF sync."""
    for dept in all_departments():
        if dept.gdrive_pdf_source:
            return dept.key
    raise RuntimeError("No department marked gdrive_pdf_source in registry")


def format_valid_department_keys() -> str:
    """Comma-separated list of valid department keys (for error messages)."""
    return ", ".join(iter_keys())


def format_department_keys_for_prompt() -> str:
    """Comma-separated department keys for LLM prompt injection."""
    return format_valid_department_keys()


def validate_confluence_space_keys(
    spaces: Mapping[str, str],
    *,
    strict: bool = False,
) -> list[str]:
    """Return unknown keys in *spaces*; log or raise when *strict*."""
    unknown = sorted(k for k in spaces if k not in _REGISTRY)
    if unknown:
        msg = (
            f"CONFLUENCE_SPACES contains unknown department keys: {unknown}. "
            f"Valid keys: {format_valid_department_keys()}"
        )
        if strict:
            raise ValueError(msg)
        logger.warning(msg)
    return unknown


def parse_confluence_spaces(value: object) -> dict[str, str]:
    """Parse ``CONFLUENCE_SPACES`` from JSON string, dict, or empty."""
    if value is None or value == "":
        return {}
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items() if str(v).strip()}
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return {}
        # Guard against a common .env typo: CONFLUENCE_SPACES=={"..."} (double =)
        # which causes the value to arrive as ={"..."} — strip the spurious leading =.
        if raw.startswith("="):
            logger.warning(
                "CONFLUENCE_SPACES value starts with '=' — stripping it. "
                "Check your .env for a double-equals typo (KEY==value)."
            )
            raw = raw[1:].strip()
        if not raw:
            return {}
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("CONFLUENCE_SPACES must be a JSON object")
        return {str(k): str(v) for k, v in parsed.items() if str(v).strip()}
    raise TypeError(f"CONFLUENCE_SPACES must be JSON or dict, got {type(value).__name__}")


def merge_legacy_confluence_env(
    spaces: Mapping[str, str],
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Merge legacy ``CONFLUENCE_SPACE_*`` env vars when absent from *spaces*."""
    env = environ if environ is not None else os.environ
    merged = dict(spaces)
    for dept in all_departments():
        legacy = env.get(dept.space_env_var, "").strip()
        if legacy and dept.key not in merged:
            merged[dept.key] = legacy
    return merged


def confluence_space_key(settings: object, key: str) -> str | None:
    """Return the configured Confluence space key for *key*, or ``None`` when unset."""
    get_department(key)  # validate key
    spaces = getattr(settings, "confluence_spaces", None)
    if isinstance(spaces, dict):
        raw = (spaces.get(key) or "").strip()
        return raw or None
    return None


def confluence_space_map(settings: object) -> dict[str, str]:
    """Map department key → Confluence space key for all configured departments."""
    return {
        dept.key: space_key
        for dept in all_departments()
        if (space_key := confluence_space_key(settings, dept.key))
    }


def confluence_space_config_hint(department_key: str | None = None) -> str:
    """Human-readable env hint for configuring Confluence space keys."""
    if department_key is not None:
        dept = get_department(department_key)
        return (
            f"Set CONFLUENCE_SPACES JSON (key {department_key!r}) or "
            f"{dept.space_env_var}=<space-key> in your environment to enable sync "
            "for this department."
        )
    keys = ", ".join(iter_keys())
    return (
        f"Set CONFLUENCE_SPACES='{{\"<dept_key>\":\"<space-key>\", ...}}' with keys "
        f"from the department registry ({keys}) in your environment."
    )


def department_catalog_text(lang: str = "en") -> str:
    """Render a human-readable catalog for use in prompt templates."""
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


def export_frontend_catalog() -> dict[str, Any]:
    """Serialize the registry for the frontend ``departments.data.json`` mirror."""
    departments = []
    for dept in all_departments():
        departments.append(
            {
                "key": dept.key,
                "name_en": dept.name_en,
                "name_vi": dept.name_vi,
                "accent_color": dept.accent_color,
                "channel_hint": dept.channel_hint,
                "head_manager_en": dept.head_manager_en,
                "head_manager_vi": dept.head_manager_vi,
                "description_en": dept.description_en,
                "description_vi": dept.description_vi,
            }
        )
    return {
        "roles": list(ROLES),
        "departments": departments,
    }


def department_as_dict(dept: Department) -> dict[str, Any]:
    """Return a JSON-serializable dict for *dept* (tests / export)."""
    return asdict(dept)
