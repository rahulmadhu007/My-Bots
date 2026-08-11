"""Realistic demo inbox mixing actionable and non-actionable emails."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def _iso(days_ago: float = 0, hours_ago: float = 0) -> str:
    dt = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


MOCK_EMAILS: list[dict[str, Any]] = [
    {
        "id": "demo-001",
        "thread_id": "thread-001",
        "subject": "Q3 board deck — need your section by EOD",
        "sender": "Sarah Chen <sarah.chen@acme.com>",
        "to": "you@acme.com",
        "date": _iso(hours_ago=2),
        "snippet": "Can you please send me the metrics slide for the board deck by EOD today? ASAP if possible.",
        "body": (
            "Hi,\n\nCan you please send me the metrics slide for the Q3 board deck "
            "by EOD today? The CFO wants a preview before tomorrow's dry run.\n\n"
            "ASAP if possible — thanks!\n\nSarah Chen\nVP, Operations"
        ),
        "labels": ["INBOX", "IMPORTANT", "UNREAD"],
        "is_unread": True,
    },
    {
        "id": "demo-002",
        "thread_id": "thread-002",
        "subject": "Invitation: Product roadmap sync @ Thu Aug 14, 2026 10:00am – 10:30am",
        "sender": "Google Calendar <calendar-notification@google.com>",
        "to": "you@acme.com",
        "date": _iso(hours_ago=5),
        "snippet": "You have been invited. Please RSVP: Yes / No / Maybe.",
        "body": (
            "Product roadmap sync\nThursday Aug 14, 2026 · 10:00am – 10:30am\n"
            "Organizer: Jordan Lee\n\n"
            "You have been invited to this meeting. Please RSVP so we can finalize the room.\n\n"
            "Yes | No | Maybe"
        ),
        "labels": ["INBOX", "UNREAD"],
        "is_unread": True,
    },
    {
        "id": "demo-003",
        "thread_id": "thread-003",
        "subject": "This week in AI: 12 tools you should try",
        "sender": "AI Weekly <newsletter@aiweekly.io>",
        "to": "you@acme.com",
        "date": _iso(days_ago=1),
        "snippet": "Top launches, papers, and promotions. Unsubscribe anytime.",
        "body": (
            "Welcome to AI Weekly!\n\nHere are 12 tools you should try this week...\n\n"
            "Special offer: 30% off Pro plans — limited-time promotion.\n\n"
            "You're receiving this because you subscribed. Unsubscribe | Manage preferences"
        ),
        "labels": ["INBOX", "CATEGORY_PROMOTIONS"],
        "is_unread": False,
    },
    {
        "id": "demo-004",
        "thread_id": "thread-004",
        "subject": "Invoice #4821 due Friday — Net 15",
        "sender": "Billing <billing@cloudhost.io>",
        "to": "you@acme.com",
        "date": _iso(days_ago=1, hours_ago=3),
        "snippet": "Your invoice of $1,240.00 is due by Friday. Please pay to avoid service interruption.",
        "body": (
            "Hello,\n\nInvoice #4821 for CloudHost Pro ($1,240.00) is due by Friday.\n"
            "Please pay via the portal or reply with a PO number if approval is needed.\n\n"
            "Amount due: $1,240.00\nDue date: Friday\n\nThank you,\nCloudHost Billing"
        ),
        "labels": ["INBOX", "UNREAD"],
        "is_unread": True,
    },
    {
        "id": "demo-005",
        "thread_id": "thread-005",
        "subject": "Dinner Friday?",
        "sender": "Alex Rivera <alex.rivera@gmail.com>",
        "to": "you@acme.com",
        "date": _iso(hours_ago=8),
        "snippet": "Hey! Free for dinner Friday? Thinking that new Thai place.",
        "body": (
            "Hey!\n\nAre you free for dinner Friday? Thinking that new Thai place on 5th.\n"
            "Let me know if that works — can you confirm by Thursday?\n\nAlex"
        ),
        "labels": ["INBOX", "UNREAD"],
        "is_unread": True,
    },
    {
        "id": "demo-006",
        "thread_id": "thread-006",
        "subject": "[acme/api] PR #892: Fix rate limiter edge case",
        "sender": "GitHub <notifications@github.com>",
        "to": "you@acme.com",
        "date": _iso(hours_ago=1),
        "snippet": "@you requested your review on this pull request.",
        "body": (
            "GitHub notification\n\n"
            "jordanlee requested your review on pull request #892:\n"
            "Fix rate limiter edge case\n\n"
            "View it on GitHub: https://github.com/acme/api/pull/892\n\n"
            "You're receiving this because you were mentioned."
        ),
        "labels": ["INBOX", "CATEGORY_UPDATES"],
        "is_unread": True,
    },
    {
        "id": "demo-007",
        "thread_id": "thread-007",
        "subject": "Order delayed — need escalation (Ticket #10442)",
        "sender": "Maya Patel <maya.patel@northwind.example>",
        "to": "support@acme.com, you@acme.com",
        "date": _iso(hours_ago=3),
        "snippet": "This is unacceptable. We need your help resolving the delayed shipment today.",
        "body": (
            "Hi team,\n\nOur enterprise order (#NW-7781) is now 5 days late. "
            "This is blocking a customer launch and we need your help resolving it today.\n\n"
            "Can you please escalate and reply with an ETA?\n\n"
            "Regards,\nMaya Patel\nProcurement, Northwind"
        ),
        "labels": ["INBOX", "IMPORTANT", "UNREAD"],
        "is_unread": True,
    },
    {
        "id": "demo-008",
        "thread_id": "thread-008",
        "subject": "Updated remote work policy (FYI)",
        "sender": "HR Team <hr@acme.com>",
        "to": "all@acme.com",
        "date": _iso(days_ago=2),
        "snippet": "Please find the updated remote work policy attached for your reference. No action required.",
        "body": (
            "Hi everyone,\n\nPlease find the updated remote work policy for your reference.\n"
            "This is an FYI — no action required unless you have questions.\n\n"
            "Best,\nPeople Operations"
        ),
        "labels": ["INBOX"],
        "is_unread": False,
    },
    {
        "id": "demo-009",
        "thread_id": "thread-009",
        "subject": "Excited about your background — quick chat?",
        "sender": "Taylor Brooks <taylor@talentbridge.io>",
        "to": "you@acme.com",
        "date": _iso(days_ago=1, hours_ago=6),
        "snippet": "I'd love to schedule a 20-minute call next week about a Staff Engineer role.",
        "body": (
            "Hi,\n\nI came across your profile and I'd love to schedule a 20-minute call "
            "next week about a Staff Engineer role at a Series C company.\n\n"
            "Are you open to chatting? Happy to work around your calendar.\n\n"
            "Best,\nTaylor Brooks\nTalentBridge Recruiting"
        ),
        "labels": ["INBOX", "UNREAD"],
        "is_unread": True,
    },
    {
        "id": "demo-010",
        "thread_id": "thread-010",
        "subject": "Blocked on API keys for staging — need approval",
        "sender": "Dev Ops <devops@acme.com>",
        "to": "you@acme.com",
        "date": _iso(hours_ago=4),
        "snippet": "We're blocked deploying staging until you approve the new API key rotation.",
        "body": (
            "Hey,\n\nWe're blocked deploying staging until you approve the new API key rotation.\n"
            "Need your approval on the security ticket SEC-441 by tomorrow morning "
            "or the release slips.\n\n"
            "Please review and approve when you can.\n\n— DevOps"
        ),
        "labels": ["INBOX", "IMPORTANT", "UNREAD"],
        "is_unread": True,
    },
    {
        "id": "demo-011",
        "thread_id": "thread-011",
        "subject": "Your Amazon.com order #112-8849201-7732109",
        "sender": "Amazon.com <auto-confirm@amazon.com>",
        "to": "you@acme.com",
        "date": _iso(days_ago=2, hours_ago=5),
        "snippet": "Thanks for your order. Your receipt is attached. No further action needed.",
        "body": (
            "Hello,\n\nThanks for your order from Amazon.com.\n"
            "Order #112-8849201-7732109\nTotal: $48.22\n"
            "Your receipt is below. No further action needed.\n\n"
            "This is an automated message — please do not reply.\n"
            "noreply notifications from Amazon.com"
        ),
        "labels": ["INBOX", "CATEGORY_UPDATES"],
        "is_unread": False,
    },
    {
        "id": "demo-012",
        "thread_id": "thread-012",
        "subject": "Standup notes — please confirm Friday owners",
        "sender": "Priya Shah <priya.shah@acme.com>",
        "to": "eng-team@acme.com",
        "date": _iso(hours_ago=6),
        "snippet": "Notes from today's standup. Can everyone confirm their Friday owners by EOD?",
        "body": (
            "Team,\n\nNotes from today's standup:\n"
            "- Auth refactor: on track\n"
            "- Billing bug: needs repro\n"
            "- Docs: waiting on screenshots\n\n"
            "Can everyone please confirm their Friday owners by EOD?\n"
            "Need your confirmation so I can update the board.\n\nThanks,\nPriya"
        ),
        "labels": ["INBOX", "UNREAD"],
        "is_unread": True,
    },
]


def get_mock_emails(max_emails: int = 20) -> list[dict[str, Any]]:
    """Return a copy of demo emails, optionally truncated."""
    # Refresh relative dates on each call so demos feel current
    emails = []
    day_offsets = [0, 0, 1, 1, 0, 0, 0, 2, 1, 0, 2, 0]
    hour_offsets = [2, 5, 0, 3, 8, 1, 3, 0, 6, 4, 5, 6]
    for i, base in enumerate(MOCK_EMAILS):
        email = dict(base)
        email["date"] = _iso(
            days_ago=day_offsets[i] if i < len(day_offsets) else 0,
            hours_ago=hour_offsets[i] if i < len(hour_offsets) else 1,
        )
        emails.append(email)
    return emails[: max(1, max_emails)]
