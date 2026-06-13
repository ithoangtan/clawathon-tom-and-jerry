from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.common.departments import (
    ROLES,
    DepartmentKey,
    all_departments,
    confluence_space_key,
    confluence_space_map,
    default_doc_type,
    department_catalog_text,
    department_keys_set,
    export_frontend_catalog,
    format_department_keys_for_prompt,
    format_valid_department_keys,
    gdrive_department_key,
    get_department,
    iter_keys,
    merge_legacy_confluence_env,
    parse_confluence_spaces,
    space_env_var,
    validate_confluence_space_keys,
)
from tests.department_fixtures import ALL_KEYS, BANK, GROW, RISK


class TestDepartmentRegistry:
    EXPECTED_KEYS = {
        DepartmentKey.RISK,
        DepartmentKey.GROW_ENABLEMENT,
        DepartmentKey.BANK_PARTNERSHIPS,
    }

    def test_all_departments_returns_three_entries(self) -> None:
        depts = all_departments()
        assert len(depts) == len(DepartmentKey)

    def test_all_departments_stable_order(self) -> None:
        keys = [d.key for d in all_departments()]
        assert keys == list(iter_keys())
        assert keys == ALL_KEYS

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
            assert dept.head_manager_en
            assert dept.head_manager_vi
            assert dept.description_en
            assert dept.description_vi
            assert dept.default_doc_type

    def test_display_name_en_and_vi(self) -> None:
        risk = get_department(RISK)
        assert risk.display_name("en") == "Risk"
        assert risk.display_name("vi") == "Quản lý Rủi ro"
        assert risk.display_name() == "Risk"

    def test_space_env_var_helper(self) -> None:
        assert space_env_var(RISK) == "CONFLUENCE_SPACE_RISK"
        assert space_env_var(GROW) == "CONFLUENCE_SPACE_GROW"
        assert space_env_var(BANK) == "CONFLUENCE_SPACE_BANK"

    def test_default_doc_type_from_registry(self) -> None:
        assert default_doc_type(RISK) == "Risk"
        assert default_doc_type(GROW) == "Operation"
        assert default_doc_type(BANK) == "Technical"

    def test_gdrive_department_key(self) -> None:
        assert gdrive_department_key() == BANK

    def test_get_department_unknown_key_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown department key"):
            get_department("finance")

    def test_department_catalog_text_includes_all_keys(self) -> None:
        catalog = department_catalog_text("en")
        for key in iter_keys():
            assert key in catalog

    def test_format_department_keys_for_prompt(self) -> None:
        assert format_department_keys_for_prompt() == format_valid_department_keys()

    def test_roles_list_complete(self) -> None:
        assert ROLES == ["engineer", "pm", "ops", "risk", "business"]

    def test_department_key_enum_values(self) -> None:
        assert {k.value for k in DepartmentKey} == {k.value for k in self.EXPECTED_KEYS}

    def test_department_keys_set(self) -> None:
        assert department_keys_set() == {k.value for k in DepartmentKey}

    def test_validate_confluence_space_keys_warns_on_unknown(self, caplog) -> None:
        unknown = validate_confluence_space_keys({RISK: "RISK", "finance": "FIN"})
        assert unknown == ["finance"]

    def test_validate_confluence_space_keys_strict_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown department keys"):
            validate_confluence_space_keys({RISK: "RISK", "finance": "FIN"}, strict=True)

    def test_frontend_export_matches_registry(self) -> None:
        exported = export_frontend_catalog()
        assert [d["key"] for d in exported["departments"]] == ALL_KEYS
        json_path = (
            Path(__file__).resolve().parents[3]
            / "frontend"
            / "src"
            / "lib"
            / "departments.data.json"
        )
        on_disk = json.loads(json_path.read_text(encoding="utf-8"))
        assert on_disk == exported


class TestConfluenceSpaceHelpers:
    def test_parse_confluence_spaces_from_json_string(self) -> None:
        parsed = parse_confluence_spaces(json.dumps({RISK: "RISK", GROW: ""}))
        assert parsed == {RISK: "RISK"}

    def test_parse_confluence_spaces_from_dict(self) -> None:
        parsed = parse_confluence_spaces({BANK: "BANK"})
        assert parsed == {BANK: "BANK"}

    def test_merge_legacy_confluence_env(self) -> None:
        merged = merge_legacy_confluence_env(
            {RISK: "JSON-RISK"},
            {"CONFLUENCE_SPACE_GROW": "LEGACY-GROW"},
        )
        assert merged == {RISK: "JSON-RISK", GROW: "LEGACY-GROW"}

    def test_confluence_space_map_from_settings(self) -> None:
        class _Cfg:
            confluence_spaces = {RISK: "RISK", GROW: ""}

        assert confluence_space_map(_Cfg()) == {RISK: "RISK"}

    def test_confluence_space_key_validates_department(self) -> None:
        class _Cfg:
            confluence_spaces = {RISK: "RISK"}

        assert confluence_space_key(_Cfg(), RISK) == "RISK"
        with pytest.raises(KeyError, match="Unknown department key"):
            confluence_space_key(_Cfg(), "finance")

    def test_format_valid_department_keys(self) -> None:
        assert format_valid_department_keys() == ", ".join(ALL_KEYS)
