from __future__ import annotations

"""Resolve Google Drive credentials from AgentBase Identity (production) or env (local).

Spec: ``2-requirements/04-SKILLS-TOOLS-INTEGRATIONS.md`` §4–5;
deploy: ``docs/DEPLOY-READINESS.md`` (OAuth provider ``identity-google-space``).
"""

import json
import logging
from typing import Any

from app.adapters.identity_client import fetch_api_key_for_agent, get_identity_client, identity_runtime_ready
from app.config import Settings

logger = logging.getLogger(__name__)

GDRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"


def gdrive_identity_ready(settings: Settings) -> bool:
    """True when AgentBase Identity can supply GDrive credentials."""
    if not identity_runtime_ready(settings):
        return False
    return bool(
        (settings.gdrive_oauth_provider or "").strip()
        or (settings.gdrive_sa_provider or "").strip()
    )


def resolve_gdrive_credentials(settings: Settings) -> dict[str, Any]:
    """Return a credential descriptor for :class:`GDriveClient`.

    Returns one of:
    - ``{"kind": "oauth_token", "token": "<access_token>"}``
    - ``{"kind": "service_account_info", "info": {...}}``
    - ``{"kind": "api_key", "key": "<developer_key>"}``

    Raises:
        ValueError: when no credential source is configured.
    """
    if settings.is_agentbase and gdrive_identity_ready(settings):
        token = _fetch_oauth_m2m_token(settings)
        if token:
            return {"kind": "oauth_token", "token": token}

        sa_info = _fetch_service_account_info(settings)
        if sa_info:
            return {"kind": "service_account_info", "info": sa_info}

        logger.warning(
            "AgentBase GDrive identity providers configured but token retrieval failed; "
            "falling back to local GDRIVE_* env vars if present"
        )

    if settings.gdrive_sa_json_path:
        return {"kind": "service_account_file", "path": settings.gdrive_sa_json_path}

    if settings.gdrive_api_key:
        return {"kind": "api_key", "key": settings.gdrive_api_key}

    raise ValueError("Google Drive credentials are not configured")


def _fetch_oauth_m2m_token(settings: Settings) -> str | None:
    provider = (settings.gdrive_oauth_provider or "").strip()
    identity = (settings.greennode_agent_identity or "").strip()
    if not provider or not identity:
        return None

    try:
        from greennode_agentbase.identity import GetM2mTokenRequest

        client = get_identity_client()
        result = client.get_m2m_token(
            provider_name=provider,
            agent_identity_name=identity,
            request=GetM2mTokenRequest(scopes=settings.gdrive_oauth_scope_list),
        )
        token = (getattr(result, "access_token", None) or "").strip()
        if token:
            logger.info("GDrive OAuth M2M token resolved via Identity provider %s", provider)
            return token
    except ImportError:
        logger.warning("greennode-agentbase not installed — cannot fetch GDrive OAuth token")
    except Exception:
        logger.exception("Failed to fetch GDrive OAuth M2M token from Identity")
    return None


def _fetch_service_account_info(settings: Settings) -> dict[str, Any] | None:
    provider = (settings.gdrive_sa_provider or "").strip()
    if not provider:
        return None

    raw = fetch_api_key_for_agent(settings, provider)
    if not raw:
        return None

    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        logger.exception("Identity provider %s returned invalid service-account JSON", provider)
        return None

    if not isinstance(info, dict) or info.get("type") != "service_account":
        logger.warning(
            "Identity provider %s did not return a service-account JSON payload", provider
        )
        return None

    logger.info("GDrive service-account JSON resolved via Identity provider %s", provider)
    return info
