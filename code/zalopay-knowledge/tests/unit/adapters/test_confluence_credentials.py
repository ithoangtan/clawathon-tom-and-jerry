from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.adapters.confluence_credentials import (
    confluence_identity_ready,
    resolve_confluence_api_token,
)
from app.config import Settings


class TestConfluenceIdentityReady:
    def test_false_for_local_env(self, tmp_path):
        settings = Settings(
            app_env="local",
            greennode_agent_identity="zalopay-knowledge",
            confluence_api_key_provider="identity-confluence-zalopay-knowledge",
            index_dir=str(tmp_path / "index"),
        )
        assert confluence_identity_ready(settings) is False

    def test_true_on_agentbase_with_provider(self, tmp_path):
        settings = Settings(
            app_env="agentbase",
            greennode_agent_identity="zalopay-knowledge",
            confluence_api_key_provider="identity-confluence-zalopay-knowledge",
            index_dir=str(tmp_path / "index"),
        )
        assert confluence_identity_ready(settings) is True


class TestResolveConfluenceApiToken:
    def test_local_env_token(self, tmp_path):
        settings = Settings(
            confluence_api_token="local-token",
            index_dir=str(tmp_path / "index"),
        )
        assert resolve_confluence_api_token(settings) == "local-token"

    def test_agentbase_identity_api_key(self, tmp_path):
        settings = Settings(
            app_env="agentbase",
            greennode_agent_identity="zalopay-knowledge",
            confluence_api_key_provider="identity-confluence-zalopay-knowledge",
            index_dir=str(tmp_path / "index"),
        )

        with patch(
            "app.adapters.confluence_credentials.fetch_api_key_for_agent",
            return_value="vault-token",
        ) as mock_fetch:
            token = resolve_confluence_api_token(settings)

        assert token == "vault-token"
        mock_fetch.assert_called_once_with(settings, "identity-confluence-zalopay-knowledge")

    def test_raises_when_nothing_configured(self, tmp_path):
        settings = Settings(
            app_env="local",
            confluence_api_token="",
            index_dir=str(tmp_path / "index"),
        )
        with pytest.raises(ValueError, match="not configured"):
            resolve_confluence_api_token(settings)
