#!/usr/bin/env python3
"""Set up Google Calendar OAuth credentials for StudyPal.

Usage:
    1. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in .env
    2. Run: python scripts/setup_google_calendar.py
    3. A browser window will open for Google sign-in
    4. After authorizing, a token is saved to data/google_token.json
"""

import json
import os
import sys
from pathlib import Path

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def main() -> None:
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    project_id = os.getenv("GOOGLE_OAUTH_PROJECT_ID", "")

    if not client_id or not client_secret:
        print(
            "Error: GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set.\n"
            "Add them to your .env file or export them as environment variables."
        )
        sys.exit(1)

    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "data/google_token.json")

    # Generate credentials.json
    credentials_data = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "project_id": project_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"],
        }
    }

    Path(credentials_path).parent.mkdir(parents=True, exist_ok=True)
    with open(credentials_path, "w") as f:
        json.dump(credentials_data, f, indent=2)
    print(f"Created {credentials_path}")

    # Run OAuth flow
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print(
            "Error: google-auth-oauthlib not installed.\nRun: pip install google-auth-oauthlib google-api-python-client"
        )
        sys.exit(1)

    scopes = ["https://www.googleapis.com/auth/calendar"]
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
    creds = flow.run_local_server(port=8080)

    # Save token
    Path(token_path).parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as f:
        f.write(creds.to_json())

    print(f"Token saved to {token_path}")
    print("Google Calendar setup complete!")


if __name__ == "__main__":
    main()
