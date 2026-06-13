from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.context import (
    UserContext,
    parse_context_from_headers,
    require_user_context,
)
from tests.unit.api.conftest import (
    AUTH_HEADERS,
    HEADER_HOME,
    HEADER_ROLE,
    HEADER_SESSION,
    HEADER_USER,
)
from tests.department_fixtures import DEFAULT_HOME, GROW, RISK


class TestParseContextFromHeaders:
    def test_parses_all_headers(self) -> None:
        ctx = parse_context_from_headers(AUTH_HEADERS)
        assert ctx.user_id == "test-user"
        assert ctx.session_id == "test-session"
        assert ctx.role == "engineer"
        assert ctx.home_department == RISK

    def test_applies_defaults_for_optional_headers(self) -> None:
        ctx = parse_context_from_headers(
            {
                HEADER_USER: "u1",
                HEADER_SESSION: "s1",
            }
        )
        assert ctx.role == "business"
        assert ctx.home_department == RISK

    def test_case_insensitive_header_keys(self) -> None:
        ctx = parse_context_from_headers(
            {
                "x-greennode-agentbase-user-id": " u1 ",
                "x-greennode-agentbase-session-id": " s1 ",
            }
        )
        assert ctx.user_id == "u1"
        assert ctx.session_id == "s1"

    def test_missing_user_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match=HEADER_USER):
            parse_context_from_headers({HEADER_SESSION: "s1"})

    def test_missing_session_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match=HEADER_SESSION):
            parse_context_from_headers({HEADER_USER: "u1"})

    def test_empty_user_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match=HEADER_USER):
            parse_context_from_headers({HEADER_USER: "", HEADER_SESSION: "s1"})

    def test_empty_session_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match=HEADER_SESSION):
            parse_context_from_headers({HEADER_USER: "u1", HEADER_SESSION: ""})


class TestRequireUserContext:
    def test_returns_user_context_when_headers_present(self) -> None:
        ctx = require_user_context(
            x_greennode_agentbase_user_id="user-abc",
            x_greennode_agentbase_session_id="sess-xyz",
            x_greennode_agentbase_role="pm",
            x_greennode_agentbase_home_department=GROW,
        )
        assert ctx == UserContext(
            user_id="user-abc",
            session_id="sess-xyz",
            role="pm",
            home_department=GROW,
        )

    def test_missing_user_id_returns_400(self) -> None:
        with pytest.raises(HTTPException) as exc:
            require_user_context(
                x_greennode_agentbase_user_id=None,
                x_greennode_agentbase_session_id="sess-xyz",
                x_greennode_agentbase_role=None,
                x_greennode_agentbase_home_department=None,
            )
        assert exc.value.status_code == 400
        assert exc.value.detail == f"Missing required header: {HEADER_USER}"

    def test_missing_session_id_returns_400(self) -> None:
        with pytest.raises(HTTPException) as exc:
            require_user_context(
                x_greennode_agentbase_user_id="user-abc",
                x_greennode_agentbase_session_id=None,
                x_greennode_agentbase_role=None,
                x_greennode_agentbase_home_department=None,
            )
        assert exc.value.status_code == 400
        assert exc.value.detail == f"Missing required header: {HEADER_SESSION}"

    def test_optional_headers_default(self) -> None:
        ctx = require_user_context(
            x_greennode_agentbase_user_id="u1",
            x_greennode_agentbase_session_id="s1",
            x_greennode_agentbase_role=None,
            x_greennode_agentbase_home_department=None,
        )
        assert ctx.role == "business"
        assert ctx.home_department == RISK

    def test_whitespace_only_user_id_returns_400(self) -> None:
        with pytest.raises(HTTPException) as exc:
            require_user_context(
                x_greennode_agentbase_user_id="   ",
                x_greennode_agentbase_session_id="sess-xyz",
                x_greennode_agentbase_role=None,
                x_greennode_agentbase_home_department=None,
            )
        assert exc.value.status_code == 400
        assert exc.value.detail == f"Missing required header: {HEADER_USER}"

    def test_strips_surrounding_whitespace_on_required_headers(self) -> None:
        ctx = require_user_context(
            x_greennode_agentbase_user_id="  user-abc  ",
            x_greennode_agentbase_session_id="  sess-xyz  ",
            x_greennode_agentbase_role=None,
            x_greennode_agentbase_home_department=None,
        )
        assert ctx.user_id == "user-abc"
        assert ctx.session_id == "sess-xyz"
