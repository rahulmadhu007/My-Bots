"""GmailFetcherAgent — pull recent emails via API or demo fixtures."""

from __future__ import annotations

from typing import Any

from models import EmailMessage

from .base import AgentResult, BaseAgent


class GmailFetcherAgent(BaseAgent):
    name = "GmailFetcherAgent"
    description = "Fetches recent inbox emails via Gmail API or demo mock data."
    capabilities = [
        "list_inbox",
        "fetch_message_details",
        "demo_mode_fallback",
    ]

    def run(self, context: dict[str, Any]) -> AgentResult:
        result = AgentResult(agent=self.name)
        max_emails = int(context.get("max_emails", 20))
        query = context.get("query", "is:inbox newer_than:7d")

        # Lazy import so unit smoke tests don't require package layout hacks
        from gmail.client import GmailClient
        from gmail.auth import get_auth_status

        auth_status = get_auth_status()
        client = GmailClient()
        raw_messages, mode = client.list_messages(max_emails=max_emails, query=query)

        emails = [EmailMessage(**m) for m in raw_messages]
        result.data = {
            "emails": [e.model_dump() for e in emails],
            "mode": mode,
            "auth_status": auth_status,
            "query": query,
            "count": len(emails),
        }
        result.message = f"Fetched {len(emails)} emails in {mode} mode"
        result.log(
            f"Fetched {len(emails)} emails (mode={mode}, query={query!r})",
            level="info",
            count=len(emails),
            mode=mode,
        )
        if mode == "demo":
            result.log(
                "Using mock inbox because no valid Gmail token was found",
                level="decision",
            )
        return result
