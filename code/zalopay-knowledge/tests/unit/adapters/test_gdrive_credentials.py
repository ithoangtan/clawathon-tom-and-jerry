from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.adapters.gdrive_credentials import (
    gdrive_identity_ready,
    resolve_gdrive_credentials,
)
from app.config import Settings


class TestGdriveIdentityReady:
    def test_false_for_local_env(self, tmp_path):
        settings = Settings(
            app_env="local",
            greennode_agent_identity="my-agent",
            gdrive_oauth_provider="identity-google-space",
            index_dir=str(tmp_path / "index"),
        )
        assert gdrive_identity_ready(settings) is False

    def test_true_when_agentbase_identity_and_oauth_provider(self, tmp_path):
        settings = Settings(
            app_env="agentbase",
            greennode_agent_identity="zalopay-knowledge",
            gdrive_oauth_provider="identity-google-space",
            index_dir=str(tmp_path / "index"),
        )
        assert gdrive_identity_ready(settings) is True


class TestResolveGdriveCredentials:
    def test_local_api_key(self, tmp_path):
        settings = Settings(
            gdrive_api_key="dev-key",
            index_dir=str(tmp_path / "index"),
        )
        assert resolve_gdrive_credentials(settings) == {"kind": "api_key", "key": "dev-key"}

    def test_agentbase_oauth_m2m_token(self, tmp_path):
        settings = Settings(
            app_env="agentbase",
            greennode_agent_identity="zalopay-knowledge",
            gdrive_oauth_provider="identity-google-space",
            gdrive_sa_provider="",
            index_dir=str(tmp_path / "index"),
        )
        mock_client = MagicMock()
        mock_client.get_m2m_token.return_value = MagicMock(access_token="ya29.token")
        mock_request_cls = MagicMock()

        import sys
        from types import ModuleType

        identity_mod = ModuleType("greennode_agentbase.identity")
        identity_mod.GetM2mTokenRequest = mock_request_cls
        agentbase_mod = ModuleType("greennode_agentbase")
        agentbase_mod.IAMCredentials = MagicMock()
        agentbase_mod.IdentityClient = MagicMock(return_value=mock_client)

        with patch.dict(
            sys.modules,
            {
                "greennode_agentbase": agentbase_mod,
                "greennode_agentbase.identity": identity_mod,
            },
        ):
            creds = resolve_gdrive_credentials(settings)

        assert creds == {"kind": "oauth_token", "token": "ya29.token"}
        mock_client.get_m2m_token.assert_called_once()

    def test_agentbase_service_account_fallback(self, tmp_path):
        settings = Settings(
            app_env="agentbase",
            greennode_agent_identity="zalopay-knowledge",
            gdrive_oauth_provider="identity-google-space",
            gdrive_sa_provider="gdrive-sa",
            index_dir=str(tmp_path / "index"),
        )
        sa_info = {"type": "service_account", "client_email": "bot@project.iam.gserviceaccount.com"}
        mock_client = MagicMock()
        mock_client.get_m2m_token.side_effect = RuntimeError("oauth unavailable")
        mock_client.get_api_key_for_agent_identity.return_value = MagicMock(
            apikey=json.dumps(sa_info)
        )

        import sys
        from types import ModuleType

        agentbase_mod = ModuleType("greennode_agentbase")
        agentbase_mod.IAMCredentials = MagicMock()
        agentbase_mod.IdentityClient = MagicMock(return_value=mock_client)
        identity_mod = ModuleType("greennode_agentbase.identity")
        identity_mod.GetM2mTokenRequest = MagicMock()

        with patch.dict(
            sys.modules,
            {
                "greennode_agentbase": agentbase_mod,
                "greennode_agentbase.identity": identity_mod,
            },
        ):
            creds = resolve_gdrive_credentials(settings)

        assert creds == {"kind": "service_account_info", "info": sa_info}

    def test_raises_when_nothing_configured(self, tmp_path):
        settings = Settings(index_dir=str(tmp_path / "index"))
        with pytest.raises(ValueError, match="not configured"):
            resolve_gdrive_credentials(settings)
