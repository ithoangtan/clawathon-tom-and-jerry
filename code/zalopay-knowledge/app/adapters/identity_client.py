from __future__ import annotations

"""Shared AgentBase Identity client helpers for outbound credential retrieval."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)


def identity_runtime_ready(settings: Settings) -> bool:
    """True when deployed on AgentBase with an injected agent identity name."""
    return settings.is_agentbase and bool((settings.greennode_agent_identity or "").strip())


def get_identity_client():
    from greennode_agentbase import IAMCredentials, IdentityClient

    return IdentityClient(iam_credentials=IAMCredentials())


def fetch_api_key_for_agent(settings: Settings, provider_name: str) -> str | None:
    """Retrieve a static API key from an Identity apikey provider."""
    provider = (provider_name or "").strip()
    identity = (settings.greennode_agent_identity or "").strip()
    if not identity_runtime_ready(settings) or not provider:
        return None

    try:
        client = get_identity_client()
        result = client.get_api_key_for_agent_identity(
            provider_name=provider,
            agent_identity_name=identity,
        )
        api_key = (getattr(result, "apikey", None) or "").strip()
        if api_key:
            logger.info("API key resolved via Identity provider %s", provider)
            return api_key
    except ImportError:
        logger.warning("greennode-agentbase not installed — cannot fetch Identity API key")
    except Exception:
        logger.exception("Failed to fetch API key from Identity provider %s", provider)
    return None
