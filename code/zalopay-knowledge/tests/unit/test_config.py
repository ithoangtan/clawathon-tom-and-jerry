from __future__ import annotations

import pytest

from app.common.departments import DepartmentKey
from app.config import Settings, get_settings


class TestSettingsDefaults:
    @staticmethod
    def _isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
        """Build Settings without autouse test_env overrides."""
        for var in ("INDEX_DIR", "LOG_LEVEL", "APP_ENV", "APP_VERSION"):
            monkeypatch.delenv(var, raising=False)
        return Settings(_env_file=None)

    def test_default_app_env_and_version(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = self._isolated_settings(monkeypatch)
        assert settings.app_env == "local"
        assert settings.app_version == "0.1.0"
        assert settings.log_level == "info"

    def test_default_retrieval_thresholds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = self._isolated_settings(monkeypatch)
        assert settings.grade_threshold == 0.5
        assert settings.topk == 8
        assert settings.route_confidence_min == 0.55

    def test_default_embedding_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = self._isolated_settings(monkeypatch)
        assert settings.embedding_model == "intfloat/multilingual-e5-small"

    def test_default_graph_timeouts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = self._isolated_settings(monkeypatch)
        assert settings.graph_budget_s == 30.0
        assert settings.branch_timeout_s == 20.0

    def test_default_index_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = self._isolated_settings(monkeypatch)
        assert settings.index_dir == "/data/index"

    def test_is_local_and_is_agentbase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("APP_ENV", raising=False)
        local = Settings(app_env="local", _env_file=None)
        agentbase = Settings(app_env="agentbase", _env_file=None)
        assert local.is_local is True
        assert local.is_agentbase is False
        assert agentbase.is_agentbase is True
        assert agentbase.is_local is False

    def test_effective_llm_api_key_prefers_llm_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = Settings(
            app_env="agentbase",
            llm_api_key="explicit-key",
            greennode_api_key="platform-key",
            _env_file=None,
        )
        assert settings.effective_llm_api_key == "explicit-key"

    def test_effective_llm_api_key_falls_back_on_agentbase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = Settings(
            app_env="agentbase",
            llm_api_key="",
            greennode_api_key="platform-key",
            _env_file=None,
        )
        assert settings.effective_llm_api_key == "platform-key"

    def test_effective_llm_api_key_ignores_greennode_when_local(self) -> None:
        settings = Settings(
            app_env="local",
            llm_api_key="",
            greennode_api_key="platform-key",
            _env_file=None,
        )
        assert settings.effective_llm_api_key == ""


class TestSettingsFromEnv:
    def test_loads_from_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_VERSION", "1.2.3")
        monkeypatch.setenv("TOPK", "12")
        monkeypatch.setenv("GRADE_THRESHOLD", "0.65")
        monkeypatch.setenv("SMALL_MODEL", "test-small")
        monkeypatch.setenv("MAIN_MODEL", "test-main")
        get_settings.cache_clear()

        settings = get_settings()
        assert settings.app_version == "1.2.3"
        assert settings.topk == 12
        assert settings.grade_threshold == 0.65
        assert settings.small_model == "test-small"
        assert settings.main_model == "test-main"

    def test_confluence_space_map_excludes_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CONFLUENCE_SPACE_RISK", "RISK")
        monkeypatch.setenv("CONFLUENCE_SPACE_GROW", "")
        monkeypatch.setenv("CONFLUENCE_SPACE_BANK", "BANK")
        settings = Settings(_env_file=None)
        assert settings.confluence_space_map == {
            DepartmentKey.RISK: "RISK",
            DepartmentKey.BANK_PARTNERSHIPS: "BANK",
        }

    def test_role_dept_access_default_restricts_business_from_risk(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.role_dept_access["business"] == [
            DepartmentKey.GROW_ENABLEMENT,
            DepartmentKey.BANK_PARTNERSHIPS,
        ]
        assert DepartmentKey.RISK in settings.role_dept_access["engineer"]

    def test_role_dept_access_from_json_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(
            "ROLE_DEPT_ACCESS",
            '{"business":["bank_partnerships"],"engineer":["risk","grow_enablement","bank_partnerships"]}',
        )
        settings = Settings(_env_file=None)
        assert settings.role_dept_access["business"] == [DepartmentKey.BANK_PARTNERSHIPS]
        assert settings.role_dept_access["engineer"] == [
            DepartmentKey.RISK,
            DepartmentKey.GROW_ENABLEMENT,
            DepartmentKey.BANK_PARTNERSHIPS,
        ]

    def test_role_dept_access_rejects_invalid_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ROLE_DEPT_ACCESS", "not-json")
        with pytest.raises(ValueError, match="valid JSON"):
            Settings(_env_file=None)

    def test_role_dept_access_rejects_unknown_department(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ROLE_DEPT_ACCESS", '{"business":["finance"]}')
        with pytest.raises(ValueError, match="invalid department"):
            Settings(_env_file=None)

    def test_graph_budget_positive(self) -> None:
        with pytest.raises(Exception):
            Settings(graph_budget_s=0, _env_file=None)

    def test_topk_bounds(self) -> None:
        with pytest.raises(Exception):
            Settings(topk=0, _env_file=None)
        with pytest.raises(Exception):
            Settings(topk=101, _env_file=None)
