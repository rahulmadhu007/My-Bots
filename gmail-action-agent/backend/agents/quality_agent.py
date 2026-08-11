"""QualityAgent — review classifications, filter false positives/negatives."""

from __future__ import annotations

import re
from typing import Any

from models import (
    ActionClassification,
    ActionType,
    EmailContext,
    EmailMessage,
    QualityReport,
    Urgency,
)

from .base import AgentResult, BaseAgent

NEWSLETTER_HINTS = re.compile(
    r"unsubscribe|newsletter|promotion|marketing|weekly digest|you.?re receiving this",
    re.I,
)
RECEIPT_HINTS = re.compile(
    r"\breceipt\b|order #|auto-?confirm|no further action|noreply@|no-?reply@",
    re.I,
)
FALSE_NEG_HINTS = re.compile(
    r"\bcan you\b|\bneed your\b|\bplease (?:confirm|reply|approve|send)\b|"
    r"\basap\b|\bby eod\b|\brsvp\b|\bapproval\b|\binvoice\b.*\bdue\b|"
    r"requested your review",
    re.I,
)


class QualityAgent(BaseAgent):
    name = "QualityAgent"
    description = (
        "Reviews classifications for false positives/negatives, scores confidence, "
        "and can override or filter results before notification formatting."
    )
    capabilities = [
        "false_positive_detection",
        "false_negative_detection",
        "confidence_scoring",
        "override_and_filter",
    ]

    def run(self, context: dict[str, Any]) -> AgentResult:
        result = AgentResult(agent=self.name)
        emails = {
            (e["id"] if isinstance(e, dict) else e.id): (
                EmailMessage(**e) if isinstance(e, dict) else e
            )
            for e in (context.get("emails") or [])
        }
        contexts = {
            (c["email_id"] if isinstance(c, dict) else c.email_id): (
                EmailContext(**c) if isinstance(c, dict) else c
            )
            for c in (context.get("contexts") or [])
        }
        classifications = [
            ActionClassification(**c) if isinstance(c, dict) else c
            for c in (context.get("classifications") or [])
        ]

        reviewed = 0
        overridden = 0
        filtered_out = 0
        flags: list[str] = []
        notes: list[str] = []
        confidences: list[float] = []
        adjusted: list[ActionClassification] = []
        needs_reclassify_ids: list[str] = []

        for clf in classifications:
            reviewed += 1
            email = emails.get(clf.email_id)
            ctx = contexts.get(clf.email_id)
            text = ""
            if email:
                text = f"{email.subject}\n{email.sender}\n{email.body}"

            updated = clf.model_copy(deep=True)
            note = None

            # False positive: newsletter/receipt marked actionable
            if updated.needs_action and email and (
                NEWSLETTER_HINTS.search(text) or RECEIPT_HINTS.search(text)
            ):
                # Allow calendar RSVP / GitHub review exceptions
                exception = bool(
                    re.search(r"\brsvp\b|requested your review|you have been invited", text, re.I)
                )
                if not exception:
                    updated.needs_action = False
                    updated.urgency = Urgency.LOW
                    updated.action_type = ActionType.OTHER
                    updated.suggested_action = "No action needed (filtered by quality gate)"
                    updated.confidence = min(updated.confidence, 0.4)
                    updated.overridden_by_quality = True
                    note = "False positive: looks like newsletter/receipt/automated mail"
                    overridden += 1
                    filtered_out += 1
                    flags.append(f"fp:{updated.email_id}")

            # False negative: strong action language marked non-actionable
            if (
                not updated.needs_action
                and email
                and FALSE_NEG_HINTS.search(text)
                and not (NEWSLETTER_HINTS.search(text) or RECEIPT_HINTS.search(text))
            ):
                updated.needs_action = True
                updated.urgency = Urgency.MEDIUM if updated.urgency == Urgency.LOW else updated.urgency
                if updated.action_type == ActionType.OTHER:
                    updated.action_type = ActionType.REPLY
                updated.suggested_action = updated.suggested_action or (
                    f"Reply to: {email.subject}" if email else "Take action"
                )
                updated.confidence = max(updated.confidence, 0.7)
                updated.overridden_by_quality = True
                note = "False negative corrected: strong action language detected"
                overridden += 1
                flags.append(f"fn:{updated.email_id}")
                needs_reclassify_ids.append(updated.email_id)

            # Low confidence actionable items get a soft flag
            if updated.needs_action and updated.confidence < 0.55:
                flags.append(f"low_conf:{updated.email_id}")
                note = (note + "; " if note else "") + "Low confidence actionable item"

            # Boost confidence when context agrees
            if ctx and updated.needs_action and ctx.intent in (
                "action_request",
                "approval_request",
                "payment_request",
                "meeting_response",
                "code_review",
            ):
                updated.confidence = min(0.95, updated.confidence + 0.08)

            updated.quality_notes = note
            if note:
                notes.append(f"{updated.email_id}: {note}")
            confidences.append(updated.confidence)
            adjusted.append(updated)

        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        # Count non-actionable after review as filtered noise (includes classifier + quality)
        non_actionable = sum(1 for c in adjusted if not c.needs_action)
        if filtered_out < non_actionable:
            filtered_out = non_actionable

        quality_failed = overridden > 0 and (
            len(needs_reclassify_ids) >= 2
            or sum(1 for c in adjusted if c.overridden_by_quality and not c.needs_action) >= 2
        )

        report = QualityReport(
            reviewed=reviewed,
            overridden=overridden,
            filtered_out=filtered_out,
            average_confidence=round(avg_conf, 3),
            flags=flags,
            notes=notes,
        )

        result.data = {
            "classifications": [c.model_dump() for c in adjusted],
            "quality_report": report.model_dump(),
            "quality_failed": quality_failed,
            "needs_reclassify_ids": needs_reclassify_ids,
            "actionable_count": sum(1 for c in adjusted if c.needs_action),
        }
        result.message = (
            f"Reviewed {reviewed}; overridden {overridden}; filtered {filtered_out}"
        )
        result.log(result.message, level="info", **report.model_dump())
        if quality_failed:
            result.log(
                "Quality gate FAILED — recommending reclassify/filter pass",
                level="decision",
                needs_reclassify_ids=needs_reclassify_ids,
            )
        else:
            result.log("Quality gate PASSED", level="decision")
        return result
