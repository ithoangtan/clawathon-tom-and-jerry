from __future__ import annotations

"""Resolve OpenAI API key from AgentBase Identity (production) or env (local)."""

import logging

from app.adapters.identity_client import fetch_api_key_for_agent, identity_runtime_ready
from app.config import Settings

logger = logging.getLogger(__name__)


def resolve_openai_api_key(settings: Settings) -> str:
    """Return the OpenAI API key.

    On AgentBase: fetched from the Identity apikey provider ``identity-openai``.
    Local dev: read from ``OPENAI_API_KEY`` env var (via ``openai_api_key`` field)
    or left empty so the OpenAI SDK reads ``OPENAI_API_KEY`` itself.
    """
    if identity_runtime_ready(settings):
        provider = (settings.openai_api_key_provider or "").strip()
        if provider:
            key = fetch_api_key_for_agent(settings, provider)
            if key:
                return key
            logger.warning(
                "AgentBase OpenAI Identity provider %s configured but retrieval failed; "
                "falling back to OPENAI_API_KEY env var",
                provider,
            )

    return (settings.openai_api_key or "").strip()
