"""Gmail OAuth2 helpers using google-auth-oauthlib."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# backend/gmail/auth.py -> project root is parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
TOKEN_PATH = DATA_DIR / "token.json"
DEFAULT_CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"


def _credentials_path() -> Path:
    env_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "").strip()
    if env_path:
        path = Path(env_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path
    return DEFAULT_CREDENTIALS_PATH


def _client_config_from_env() -> Optional[dict[str, Any]]:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return None
    redirect_uri = os.getenv(
        "OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"
    ).strip()
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


def has_client_credentials() -> bool:
    if _client_config_from_env() is not None:
        return True
    return _credentials_path().is_file()


def has_valid_token() -> bool:
    if not TOKEN_PATH.is_file():
        return False
    try:
        creds = _load_credentials()
        return bool(creds and creds.valid)
    except Exception:
        return False


def get_auth_status() -> dict[str, Any]:
    configured = has_client_credentials()
    authenticated = has_valid_token()
    mode = "gmail" if authenticated else "demo"
    return {
        "mode": mode,
        "auth_configured": configured,
        "authenticated": authenticated,
        "token_path": str(TOKEN_PATH),
        "credentials_path": str(_credentials_path()),
    }


def _load_client_config() -> dict[str, Any]:
    env_cfg = _client_config_from_env()
    if env_cfg is not None:
        return env_cfg
    path = _credentials_path()
    if not path.is_file():
        raise FileNotFoundError(
            "Gmail OAuth credentials not found. Set GOOGLE_CLIENT_ID/"
            "GOOGLE_CLIENT_SECRET or provide credentials.json."
        )
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_credentials():
    """Load and optionally refresh stored credentials. Returns None if unavailable."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        return None

    if not TOKEN_PATH.is_file():
        return None

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_credentials(creds)
        except Exception:
            return None
    return creds if creds and creds.valid else None


def _save_credentials(creds) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")


class GmailAuth:
    """Thin wrapper around the OAuth2 installed-app / web flow."""

    def __init__(self) -> None:
        self.redirect_uri = os.getenv(
            "OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"
        ).strip()

    def get_authorization_url(self, state: str = "gmail-action-agent") -> dict[str, Any]:
        if not has_client_credentials():
            return {
                "ok": False,
                "mode": "demo",
                "message": (
                    "Demo mode: Gmail OAuth is not configured. "
                    "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env, "
                    "or place credentials.json in the project root, then restart."
                ),
                "url": None,
            }

        from google_auth_oauthlib.flow import Flow

        client_config = _load_client_config()
        # Support both "web" and "installed" client JSON shapes
        client_type = "web" if "web" in client_config else "installed"
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            state=state,
        )
        flow.redirect_uri = self.redirect_uri
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return {
            "ok": True,
            "mode": "gmail",
            "message": "Open this URL to authorize Gmail access.",
            "url": auth_url,
            "redirect_uri": self.redirect_uri,
            "client_type": client_type,
        }

    def exchange_code(self, code: str) -> dict[str, Any]:
        from google_auth_oauthlib.flow import Flow

        client_config = _load_client_config()
        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = self.redirect_uri
        flow.fetch_token(code=code)
        creds = flow.credentials
        _save_credentials(creds)
        return {
            "ok": True,
            "message": "Gmail authorization complete. Token saved.",
            "mode": "gmail",
        }

    def get_credentials(self):
        return _load_credentials()

    def clear_token(self) -> None:
        if TOKEN_PATH.is_file():
            TOKEN_PATH.unlink()
