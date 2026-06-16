from __future__ import annotations

"""Send email via Gmail API using OAuth2.

Local dev: exchange refresh_token → access_token via Google token endpoint.
AgentBase runtime: reuse identity-google-space provider with gmail.send scope.
"""

import base64
import json
import logging
import urllib.parse
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import Settings

logger = logging.getLogger(__name__)

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
_GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def send_email(*, to: str, subject: str, body_html: str, settings: Settings) -> bool:
    """Send an HTML email via Gmail API. Returns True on success, False on failure."""
    if not to:
        logger.warning("Gmail: recipient email empty, skipping")
        return False

    token = _resolve_access_token(settings)
    if not token:
        logger.warning("Gmail: no access token available, skipping email to %s", to)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.gmail_sender or "me"
    msg["To"] = to
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    payload = json.dumps({"raw": raw}).encode()
    req = urllib.request.Request(
        _GMAIL_SEND_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        logger.info("Gmail: sent to=%s subject=%r", to, subject)
        return True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        logger.warning("Gmail: HTTP %s sending to %s: %s", exc.code, to, body)
    except Exception as exc:
        logger.warning("Gmail: failed to send to %s: %s", to, exc)
    return False


def _resolve_access_token(settings: Settings) -> str | None:
    """AgentBase identity first, then local refresh_token fallback."""
    if settings.is_agentbase:
        try:
            from app.adapters.identity_client import get_identity_client, identity_runtime_ready
            if identity_runtime_ready(settings):
                from greennode_agentbase.identity import Get3loTokenRequest
                client = get_identity_client()
                result = client.get_3lo_token(
                    provider_name=settings.gdrive_oauth_provider or "identity-google-space",
                    agent_identity_name=(settings.greennode_agent_identity or "").strip(),
                    request=Get3loTokenRequest(scopes=[GMAIL_SEND_SCOPE]),
                )
                token = (getattr(result, "access_token", None) or "").strip()
                if token:
                    return token
        except Exception as exc:
            logger.warning("Gmail: AgentBase identity token failed: %s", exc)

    return _refresh_to_access_token(settings)


def _refresh_to_access_token(settings: Settings) -> str | None:
    client_id = (settings.gmail_client_id or "").strip()
    client_secret = (settings.gmail_client_secret or "").strip()
    refresh_token = (settings.gmail_refresh_token or "").strip()
    if not (client_id and client_secret and refresh_token):
        return None

    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
        token = (body.get("access_token") or "").strip()
        if token:
            return token
        logger.warning("Gmail: token refresh returned no access_token: %s", body)
    except Exception as exc:
        logger.warning("Gmail: token refresh failed: %s", exc)
    return None
