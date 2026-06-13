from __future__ import annotations

"""Request context parsed from AgentBase headers."""

from dataclasses import dataclass

from fastapi import Header, HTTPException

from app.common.departments import DEFAULT_HOME_DEPARTMENT

_HEADER_USER = "X-GreenNode-AgentBase-User-Id"
_HEADER_SESSION = "X-GreenNode-AgentBase-Session-Id"
_HEADER_ROLE = "X-GreenNode-AgentBase-Role"
_HEADER_HOME = "X-GreenNode-AgentBase-Home-Department"


@dataclass(frozen=True)
class UserContext:
    user_id: str
    session_id: str
    role: str = "business"
    home_department: str = DEFAULT_HOME_DEPARTMENT.value


def _required_header(value: str | None, header_name: str) -> str:
    """Strip and reject absent or whitespace-only header values (FR-1.1)."""
    if value is None:
        raise ValueError(f"Missing required header: {header_name}")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"Missing required header: {header_name}")
    return stripped


def require_user_context(
    x_greennode_agentbase_user_id: str | None = Header(default=None, alias=_HEADER_USER),
    x_greennode_agentbase_session_id: str | None = Header(default=None, alias=_HEADER_SESSION),
    x_greennode_agentbase_role: str | None = Header(default=None, alias=_HEADER_ROLE),
    x_greennode_agentbase_home_department: str | None = Header(
        default=None, alias=_HEADER_HOME
    ),
) -> UserContext:
    """FastAPI dependency — rejects missing User-Id / Session-Id (FR-1.1 / AC-8)."""
    try:
        user_id = _required_header(x_greennode_agentbase_user_id, _HEADER_USER)
        session_id = _required_header(x_greennode_agentbase_session_id, _HEADER_SESSION)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserContext(
        user_id=user_id,
        session_id=session_id,
        role=(x_greennode_agentbase_role or "business").strip() or "business",
        home_department=(
            x_greennode_agentbase_home_department or DEFAULT_HOME_DEPARTMENT.value
        ).strip()
        or DEFAULT_HOME_DEPARTMENT.value,
    )


def parse_context_from_headers(headers: dict[str, str]) -> UserContext:
    """Parse context from a header dict (AgentBase SDK / tests)."""
    normalized = {k.lower(): v for k, v in headers.items()}

    def get(name: str) -> str | None:
        return normalized.get(name.lower())

    uid = _required_header(get(_HEADER_USER), _HEADER_USER)
    sid = _required_header(get(_HEADER_SESSION), _HEADER_SESSION)
    return UserContext(
        user_id=uid,
        session_id=sid,
        role=(get(_HEADER_ROLE) or "business").strip() or "business",
        home_department=(get(_HEADER_HOME) or DEFAULT_HOME_DEPARTMENT.value).strip()
        or DEFAULT_HOME_DEPARTMENT.value,
    )
