#!/usr/bin/env python3
"""Verify Google Drive OAuth2 (3LO) authentication via AgentBase identity-google-space.

Usage (requires GREENNODE_CLIENT_ID + GREENNODE_CLIENT_SECRET in env or .greennode.json):

  # Override agent identity for testing with operator credentials:
  GREENNODE_AGENT_IDENTITY=zalopay-knowledge python3 scripts/verify_gdrive_oauth.py

  # Override provider or agent user:
  GDRIVE_OAUTH_PROVIDER=identity-google-space \
  GDRIVE_OAUTH_AGENT_USER_ID=admin \
  GREENNODE_AGENT_IDENTITY=zalopay-knowledge \
  python3 scripts/verify_gdrive_oauth.py

Exit codes: 0 = success, 1 = failure.

If the response includes an authorization_url, an admin must visit that URL once
to complete the Google OAuth2 consent flow before tokens can be issued.
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    provider_name = os.environ.get("GDRIVE_OAUTH_PROVIDER", "identity-google-space")
    agent_identity = os.environ.get("GREENNODE_AGENT_IDENTITY", "").strip()
    agent_user_id = os.environ.get("GDRIVE_OAUTH_AGENT_USER_ID", "admin").strip()
    scope = "https://www.googleapis.com/auth/drive.readonly"

    print(f"Provider    : {provider_name}")
    print(f"Identity    : {agent_identity or '(not set)'}")
    print(f"Agent user  : {agent_user_id}")
    print(f"Scope       : {scope}")
    print()

    if not agent_identity:
        print(
            "ERROR: GREENNODE_AGENT_IDENTITY is not set.\n"
            "       Set it to your agent identity name, e.g.:\n"
            "         GREENNODE_AGENT_IDENTITY=zalopay-knowledge python3 scripts/verify_gdrive_oauth.py"
        )
        return 1

    # ── Step 1: Get 3LO token from AgentBase Identity ─────────────────────────
    print("Step 1: Fetching OAuth2 3LO token from AgentBase Identity...")
    try:
        from greennode_agentbase import IAMCredentials, IdentityClient
        from greennode_agentbase.identity import Get3loTokenRequest
    except ImportError:
        print(
            "ERROR: greennode-agentbase SDK not installed.\n"
            "       Install with: pip install 'greennode-agentbase>=0.1,<1'\n"
            "       (available in AgentBase runtime or with operator credentials)"
        )
        return 1

    try:
        client = IdentityClient(iam_credentials=IAMCredentials())
        result = client.get_3lo_token(
            provider_name=provider_name,
            agent_identity_name=agent_identity,
            request=Get3loTokenRequest(
                agent_user_id=agent_user_id,
                scopes=[scope],
            ),
        )
    except Exception as exc:
        print(f"ERROR: Failed to call get_3lo_token: {exc}")
        print()
        print("Possible causes:")
        print("  - Provider name mismatch — check Access Control → Outbound Auth")
        print("  - IAM credentials lack AgentBaseFullAccess policy")
        return 1

    access_token = (getattr(result, "access_token", None) or "").strip()
    auth_url = (getattr(result, "authorization_url", None) or "").strip()

    if not access_token:
        if auth_url:
            print("  NOT YET AUTHORIZED — admin must complete the Google OAuth2 consent flow.")
            print(f"\n  Visit this URL to authorize:\n\n    {auth_url}\n")
            print("  After authorizing, re-run this script to verify the token is issued.")
        else:
            print("  ERROR: Token response had empty access_token and no authorization_url")
        return 1

    print(f"  OK — got access token (first 20 chars): {access_token[:20]}...")
    print()

    # ── Step 2: Probe Google Drive API ────────────────────────────────────────
    print("Step 2: Probing Google Drive API with the token...")
    try:
        import httpx

        resp = httpx.get(
            "https://www.googleapis.com/drive/v3/about?fields=user",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            user = resp.json().get("user", {})
            print(
                f"  OK — authenticated as: "
                f"{user.get('displayName', '(unknown)')} <{user.get('emailAddress', '')}>"
            )
        elif resp.status_code == 403:
            print(f"  WARN — token valid but Drive scope not granted (HTTP 403): {resp.text[:200]}")
            print("         Ensure drive.readonly scope is included in the Google OAuth2 consent")
        else:
            print(f"  WARN — unexpected response (HTTP {resp.status_code}): {resp.text[:200]}")
    except ImportError:
        print("  SKIP — httpx not installed; skipping Drive API probe")
        print("         pip install httpx  to enable this step")
    except Exception as exc:
        print(f"  ERROR — Drive API probe failed: {exc}")
        return 1

    print()
    print("Authentication verification complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
