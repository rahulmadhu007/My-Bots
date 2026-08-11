"""NotificationAgent — format actionable items for the UI."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from models import ActionClassification, EmailMessage, Notification, Urgency

from .base import AgentResult, BaseAgent

URGENCY_ORDER = {
    Urgency.CRITICAL: 0,
    Urgency.HIGH: 1,
    Urgency.MEDIUM: 2,
    Urgency.LOW: 3,
}


def _title(email: EmailMessage, clf: ActionClassification) -> str:
    prefix = {
        "reply": "Reply needed",
        "approve": "Approval needed",
        "schedule": "Scheduling",
        "pay": "Payment due",
        "review": "Review requested",
        "follow_up": "Follow up",
        "other": "Action needed",
    }.get(clf.action_type.value, "Action needed")
    subject = email.subject or "(no subject)"
    return f"{prefix}: {subject}"


def _body(email: EmailMessage, clf: ActionClassification) -> str:
    snippet = (email.snippet or email.body or "").strip()
    if len(snippet) > 220:
        snippet = snippet[:217] + "…"
    reason = clf.reason.split(";")[0] if clf.reason else ""
    parts = [snippet]
    if clf.suggested_action:
        parts.append(f"Suggested: {clf.suggested_action}")
    if reason:
        parts.append(f"Why: {reason}")
    return "\n".join(p for p in parts if p)


class NotificationAgent(BaseAgent):
    name = "NotificationAgent"
    description = "Formats actionable emails into UI-ready notifications."
    capabilities = [
        "format_notifications",
        "urgency_sorting",
        "suggested_actions",
    ]

    def run(self, context: dict[str, Any]) -> AgentResult:
        result = AgentResult(agent=self.name)
        emails = {
            (e["id"] if isinstance(e, dict) else e.id): (
                EmailMessage(**e) if isinstance(e, dict) else e
            )
            for e in (context.get("emails") or [])
        }
        classifications = [
            ActionClassification(**c) if isinstance(c, dict) else c
            for c in (context.get("classifications") or [])
        ]

        # Preserve status from prior notifications when re-scanning same email ids
        prior = {
            n.get("email_id"): n
            for n in (context.get("prior_notifications") or [])
            if isinstance(n, dict)
        }

        notifications: list[Notification] = []
        for clf in classifications:
            if not clf.needs_action:
                continue
            email = emails.get(clf.email_id)
            if not email:
                continue
            existing = prior.get(email.id) or {}
            status = existing.get("status", "open")
            if status in ("dismissed", "completed") and context.get("preserve_status", True):
                # Keep terminal states out of the active list unless refresh forces reopen
                if not context.get("force_reopen"):
                    continue

            notif = Notification(
                id=existing.get("id") or f"notif-{uuid4().hex[:10]}",
                title=_title(email, clf),
                body=_body(email, clf),
                urgency=clf.urgency,
                sender=email.sender,
                subject=email.subject,
                received_at=email.date,
                action_type=clf.action_type,
                suggested_action=clf.suggested_action,
                email_id=email.id,
                confidence=clf.confidence,
                status="open",
            )
            notifications.append(notif)

        notifications.sort(key=lambda n: (URGENCY_ORDER.get(n.urgency, 9), n.received_at or ""))

        result.data = {
            "notifications": [n.model_dump(mode="json") for n in notifications],
            "count": len(notifications),
        }
        result.message = f"Formatted {len(notifications)} notifications"
        result.log(result.message, count=len(notifications))
        if notifications:
            top = notifications[0]
            result.log(
                f"Top urgency item: {top.urgency.value} — {top.subject}",
                level="decision",
                notification_id=top.id,
            )
        return result
