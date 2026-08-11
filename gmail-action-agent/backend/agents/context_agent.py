"""ContextAgent — extract intent, entities, deadlines, tone per email."""

from __future__ import annotations

import re
from typing import Any

from models import EmailContext, EmailMessage

from .base import AgentResult, BaseAgent

DEADLINE_PATTERNS = [
    r"\bby eod\b",
    r"\bby end of day\b",
    r"\bby friday\b",
    r"\bby thursday\b",
    r"\bby monday\b",
    r"\bby tomorrow\b",
    r"\bdue (?:by |on )?[\w\s,]+\b",
    r"\basap\b",
    r"\btoday\b",
    r"\bnext week\b",
    r"\bby \d{1,2}[/-]\d{1,2}\b",
]

ASK_PATTERNS = [
    r"\bcan you\b[^.?!\n]*[.?!]?",
    r"\bcould you\b[^.?!\n]*[.?!]?",
    r"\bplease\b[^.?!\n]*[.?!]?",
    r"\bneed your\b[^.?!\n]*[.?!]?",
    r"\bwould you\b[^.?!\n]*[.?!]?",
    r"\blet me know\b[^.?!\n]*[.?!]?",
    r"\bconfirm\b[^.?!\n]*[.?!]?",
    r"\brsvp\b[^.?!\n]*[.?!]?",
]

ENTITY_PATTERNS = [
    (r"\$[\d,]+(?:\.\d{2})?", "money"),
    (r"\bInvoice\s*#?\s*\w+\b", "invoice"),
    (r"\bPR\s*#?\s*\d+\b", "pull_request"),
    (r"\bTicket\s*#?\s*\w+\b", "ticket"),
    (r"\b[A-Z]{2,}-\d+\b", "issue_key"),
    (r"\b\d{1,2}:\d{2}\s*(?:am|pm)\b", "time"),
]


def _find_all(patterns: list[str], text: str) -> list[str]:
    found: list[str] = []
    for pat in patterns:
        for match in re.finditer(pat, text, flags=re.IGNORECASE):
            val = match.group(0).strip()
            if val and val not in found:
                found.append(val)
    return found


def _detect_tone(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ("unacceptable", "urgent", "asap", "blocked", "escalate")):
        return "urgent"
    if any(w in lower for w in ("please", "thanks", "thank you", "appreciate")):
        return "polite"
    if any(w in lower for w in ("fyi", "no action", "for your reference")):
        return "informational"
    if "?" in text:
        return "inquiring"
    return "neutral"


def _detect_intent(subject: str, body: str, asks: list[str], deadlines: list[str]) -> str:
    blob = f"{subject}\n{body}".lower()
    if "rsvp" in blob or "invitation:" in blob or "you have been invited" in blob:
        return "meeting_response"
    if "invoice" in blob or "payment" in blob or "amount due" in blob:
        return "payment_request"
    if "approve" in blob or "approval" in blob:
        return "approval_request"
    if "review" in blob and ("pr" in blob or "pull request" in blob):
        return "code_review"
    if "unsubscribe" in blob or "newsletter" in blob or "promotion" in blob:
        return "newsletter_or_promo"
    if "receipt" in blob or "order #" in blob or "noreply" in blob:
        return "automated_receipt"
    if "fyi" in blob or "no action required" in blob:
        return "informational_fyi"
    if asks or deadlines:
        return "action_request"
    if "?" in blob:
        return "question"
    return "general_update"


def build_context(email: EmailMessage) -> EmailContext:
    text = f"{email.subject}\n{email.snippet}\n{email.body}"
    deadlines = _find_all(DEADLINE_PATTERNS, text)
    asks = _find_all(ASK_PATTERNS, text)
    entities: list[str] = []
    for pat, label in ENTITY_PATTERNS:
        for match in re.finditer(pat, text, flags=re.IGNORECASE):
            entities.append(f"{label}:{match.group(0)}")

    tone = _detect_tone(text)
    intent = _detect_intent(email.subject, email.body, asks, deadlines)
    ask = asks[0] if asks else None
    signals: list[str] = []
    if deadlines:
        signals.append("has_deadline")
    if asks:
        signals.append("has_ask")
    if email.is_unread:
        signals.append("unread")
    if "IMPORTANT" in (email.labels or []):
        signals.append("important_label")

    summary = email.snippet or (email.body[:180] + ("…" if len(email.body) > 180 else ""))
    return EmailContext(
        email_id=email.id,
        intent=intent,
        entities=entities[:12],
        deadlines=deadlines[:8],
        ask_or_request=ask,
        tone=tone,
        summary=summary,
        signals=signals,
    )


class ContextAgent(BaseAgent):
    name = "ContextAgent"
    description = "Extracts intent, entities, deadlines, requests, and tone from emails."
    capabilities = [
        "intent_detection",
        "entity_extraction",
        "deadline_detection",
        "tone_analysis",
    ]

    def run(self, context: dict[str, Any]) -> AgentResult:
        result = AgentResult(agent=self.name)
        raw_emails = context.get("emails") or []
        emails = [EmailMessage(**e) if isinstance(e, dict) else e for e in raw_emails]

        contexts = [build_context(email) for email in emails]
        result.data = {
            "contexts": [c.model_dump() for c in contexts],
            "count": len(contexts),
        }
        result.message = f"Built context for {len(contexts)} emails"
        result.log(
            f"Extracted structured context for {len(contexts)} emails",
            count=len(contexts),
        )
        actionableish = sum(
            1
            for c in contexts
            if c.intent
            not in ("newsletter_or_promo", "automated_receipt", "informational_fyi", "general_update")
        )
        result.log(
            f"Detected {actionableish} emails with action-leaning intent",
            level="decision",
            actionableish=actionableish,
        )
        return result
