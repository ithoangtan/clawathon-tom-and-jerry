from __future__ import annotations

"""Resolve Confluence API tokens from AgentBase Identity (production) or env (local)."""

import logging

from app.adapters.identity_client import fetch_api_key_for_agent, identity_runtime_ready
from app.config import Settings

logger = logging.getLogger(__name__)


def confluence_identity_ready(settings: Settings) -> bool:
    """True when AgentBase Identity can supply the Confluence API token."""
    if not identity_runtime_ready(settings):
        return False
    return bool((settings.confluence_api_key_provider or "").strip())


def resolve_confluence_api_token(settings: Settings) -> str:
    """Return the Atlassian API token for Confluence Basic auth."""
    if confluence_identity_ready(settings):
        token = fetch_api_key_for_agent(settings, settings.confluence_api_key_provider)
        if token:
            return token
        logger.warning(
            "AgentBase Confluence identity provider %s configured but retrieval failed; "
            "falling back to CONFLUENCE_API_TOKEN if set",
            settings.confluence_api_key_provider,
        )

    token = (settings.confluence_api_token or "").strip()
    if token:
        return token

    raise ValueError("Confluence API token is not configured")
