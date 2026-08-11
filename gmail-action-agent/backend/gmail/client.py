"""Gmail API client for listing and reading messages."""

from __future__ import annotations

import base64
import re
from email.utils import parsedate_to_datetime
from typing import Any, Optional

from .auth import GmailAuth, get_auth_status
from .mock_emails import get_mock_emails


def _decode_body(payload: dict[str, Any]) -> str:
    """Extract plain-text body from a Gmail message payload."""
    mime = payload.get("mimeType", "")
    body = payload.get("body", {}) or {}
    data = body.get("data")
    if data and mime.startswith("text/plain"):
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode(
            "utf-8", errors="replace"
        )

    parts = payload.get("parts") or []
    texts: list[str] = []
    for part in parts:
        texts.append(_decode_body(part))
    joined = "\n".join(t for t in texts if t).strip()
    if joined:
        return joined

    # Fallback: any text/html stripped lightly
    if data and "html" in mime:
        html = base64.urlsafe_b64decode(data.encode("utf-8")).decode(
            "utf-8", errors="replace"
        )
        return re.sub(r"<[^>]+>", " ", html)

    return ""


def _header_map(headers: list[dict[str, str]]) -> dict[str, str]:
    return {h.get("name", "").lower(): h.get("value", "") for h in headers}


class GmailClient:
    """Fetch inbox messages via Gmail API, or fall back to demo fixtures."""

    def __init__(self, auth: Optional[GmailAuth] = None) -> None:
        self.auth = auth or GmailAuth()

    @property
    def mode(self) -> str:
        return get_auth_status()["mode"]

    def list_messages(
        self,
        max_emails: int = 20,
        query: str = "is:inbox newer_than:7d",
    ) -> tuple[list[dict[str, Any]], str]:
        """
        Return (messages, mode).
        mode is 'gmail' when live API is used, otherwise 'demo'.
        """
        creds = self.auth.get_credentials()
        if not creds:
            return get_mock_emails(max_emails), "demo"

        try:
            from googleapiclient.discovery import build

            service = build("gmail", "v1", credentials=creds, cache_discovery=False)
            response = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_emails)
                .execute()
            )
            refs = response.get("messages", []) or []
            messages: list[dict[str, Any]] = []
            for ref in refs:
                detail = self._get_message(service, ref["id"])
                if detail:
                    messages.append(detail)
            if not messages:
                # Authenticated but empty inbox — still gmail mode
                return [], "gmail"
            return messages, "gmail"
        except Exception:
            # Soft-fallback so the product never hard-fails without credentials health
            return get_mock_emails(max_emails), "demo"

    def _get_message(self, service, message_id: str) -> Optional[dict[str, Any]]:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        payload = msg.get("payload", {}) or {}
        headers = _header_map(payload.get("headers") or [])
        labels = msg.get("labelIds") or []
        date_raw = headers.get("date", "")
        try:
            if date_raw:
                parsedate_to_datetime(date_raw)  # validate
        except Exception:
            pass

        return {
            "id": msg.get("id", message_id),
            "thread_id": msg.get("threadId"),
            "subject": headers.get("subject", "(no subject)"),
            "sender": headers.get("from", ""),
            "to": headers.get("to", ""),
            "date": date_raw,
            "snippet": msg.get("snippet", ""),
            "body": _decode_body(payload) or msg.get("snippet", ""),
            "labels": labels,
            "is_unread": "UNREAD" in labels,
        }
