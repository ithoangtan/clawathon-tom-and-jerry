#!/usr/bin/env python3
"""Run once to get Gmail OAuth2 refresh token for email sending."""
import json
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID = input("Client ID: ").strip()
CLIENT_SECRET = input("Client Secret: ").strip()

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
    }
}

flow = InstalledAppFlow.from_client_config(
    client_config,
    scopes=["https://www.googleapis.com/auth/gmail.send"],
)

creds = flow.run_local_server(port=0)

print("\n--- Copy vào .env ---")
print(f"GMAIL_CLIENT_ID={CLIENT_ID}")
print(f"GMAIL_CLIENT_SECRET={CLIENT_SECRET}")
print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
print(f"GMAIL_SENDER=<your-gmail>@gmail.com")
