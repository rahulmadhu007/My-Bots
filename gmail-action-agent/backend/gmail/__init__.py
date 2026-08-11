"""Gmail OAuth, API client, and demo/mock email fixtures."""

from .auth import GmailAuth, get_auth_status
from .client import GmailClient
from .mock_emails import get_mock_emails

__all__ = [
    "GmailAuth",
    "GmailClient",
    "get_auth_status",
    "get_mock_emails",
]
