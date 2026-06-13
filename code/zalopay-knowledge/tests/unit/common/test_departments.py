from __future__ import annotations

import pytest

from app.common.departments import (
    ROLES,
    DepartmentKey,
    all_departments,
    department_catalog_text,
    get_department,
    iter_keys,
    space_env_var,
)


class TestDepartmentRegistry:
    EXPECTED_KEYS = {
        DepartmentKey.RISK,
        DepartmentKey.GROW_ENABLEMENT,
        DepartmentKey.BANK_PARTNERSHIPS,
    }

    def test_all_departments_returns_three_entries(self) -> None:
        depts = all_departments()
        assert len(depts) == 3

    def test_all_departments_stable_order(self) -> None:
        keys = [d.key for d in all_departments()]
        assert keys == ["risk", "grow_enablement", "bank_partnerships"]

    def test_iter_keys_matches_all_departments(self) -> None:
        assert list(iter_keys()) == [d.key for d in all_departments()]

    def test_each_department_has_required_metadata(self) -> None:
        for dept in all_departments():
            assert dept.key
            assert dept.name_en
            assert dept.name_vi
            assert dept.space_env_var.startswith("CONFLUENCE_SPACE_")
            assert dept.accent_color.startswith("#")
            assert dept.channel_hint.startswith("teams-")

    def test_display_name_en_and_vi(self) -> None:
        risk = get_department("risk")
        assert risk.display_name("en") == "Risk"
        assert risk.display_name("vi") == "Quản lý Rủi ro"
        assert risk.display_name() == "Risk"

    def test_space_env_var_helper(self) -> None:
        assert space_env_var("risk") == "CONFLUENCE_SPACE_RISK"
        assert space_env_var("grow_enablement") == "CONFLUENCE_SPACE_GROW"
        assert space_env_var("bank_partnerships") == "CONFLUENCE_SPACE_BANK"

    def test_get_department_unknown_key_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown department key"):
            get_department("finance")

    def test_department_catalog_text_includes_all_keys(self) -> None:
        catalog = department_catalog_text("en")
        for key in iter_keys():
            # dept.key is stored as DepartmentKey enum; catalog renders str(key)
            assert str(key) in catalog or key.value in catalog

    def test_roles_list_complete(self) -> None:
        assert ROLES == ["engineer", "pm", "ops", "risk", "business"]

    def test_department_key_enum_values(self) -> None:
        assert {k.value for k in DepartmentKey} == {k.value for k in self.EXPECTED_KEYS}
