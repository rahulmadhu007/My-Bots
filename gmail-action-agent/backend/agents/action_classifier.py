"""ActionClassifierAgent — decide needs_action, urgency, and action type."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from models import ActionClassification, ActionType, EmailContext, EmailMessage, Urgency

from .base import AgentResult, BaseAgent

ACTION_SIGNALS = [
    (r"\bcan you\b", 2.0, "direct_question"),
    (r"\bcould you\b", 1.8, "polite_request"),
    (r"\bplease\b", 1.5, "please"),
    (r"\basap\b", 3.0, "asap"),
    (r"\bby friday\b", 2.5, "deadline_friday"),
    (r"\bby eod\b", 2.8, "deadline_eod"),
    (r"\bby end of day\b", 2.8, "deadline_eod"),
    (r"\bby tomorrow\b", 2.6, "deadline_tomorrow"),
    (r"\bdue (?:by|on)\b", 2.5, "due_date"),
    (r"\brsvp\b", 2.4, "rsvp"),
    (r"\binvoice\b", 2.2, "invoice"),
    (r"\bapproval needed\b", 2.8, "approval_needed"),
    (r"\bneed your (?:help|approval|review|confirmation)\b", 2.7, "need_your"),
    (r"\bneed your\b", 2.0, "need_your_generic"),
    (r"\bplease confirm\b", 2.3, "confirm"),
    (r"\brespond\b", 1.4, "respond"),
    (r"\bschedule\b", 1.5, "schedule"),
    (r"\bblocked\b", 2.6, "blocked"),
    (r"\bescalate\b", 2.4, "escalate"),
    (r"\baction required\b", 3.0, "action_required"),
    (r"\byou have been invited\b", 2.2, "invite"),
    (r"\brequested your review\b", 2.3, "review_request"),
    (r"\?", 0.8, "question_mark"),
]

NON_ACTION_SIGNALS = [
    (r"\bunsubscribe\b", 3.0, "unsubscribe"),
    (r"\bnewsletter\b", 2.5, "newsletter"),
    (r"\bpromotion\b", 2.0, "promotion"),
    (r"noreply@", 2.8, "noreply"),
    (r"no[- ]reply@", 2.8, "noreply"),
    (r"\bno (?:further )?action (?:needed|required)\b", 3.0, "no_action"),
    (r"\bfyi\b", 1.5, "fyi"),
    (r"\bfor your reference\b", 2.0, "reference"),
    (r"notifications@github\.com", 1.2, "github_bot"),  # weak — reviews still matter
    (r"\breceipt\b", 1.8, "receipt"),
    (r"\bauto-?confirm\b", 2.5, "auto_confirm"),
    (r"\bcategory_promotions\b", 2.5, "promo_label"),
    (r"calendar-notification@google\.com", 0.5, "calendar"),  # invites may need RSVP
]


def _score(text: str, patterns: list[tuple[str, float, str]]) -> tuple[float, list[str]]:
    score = 0.0
    hits: list[str] = []
    for pat, weight, name in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            score += weight
            hits.append(name)
    return score, hits


def _infer_action_type(text: str, intent: str) -> ActionType:
    lower = text.lower()
    if intent == "payment_request" or "invoice" in lower or "pay" in lower:
        return ActionType.PAY
    if intent == "approval_request" or "approve" in lower:
        return ActionType.APPROVE
    if intent == "meeting_response" or "rsvp" in lower or "schedule" in lower:
        return ActionType.SCHEDULE
    if intent == "code_review" or "review" in lower:
        return ActionType.REVIEW
    if "follow up" in lower or "follow-up" in lower:
        return ActionType.FOLLOW_UP
    if "can you" in lower or "please reply" in lower or "let me know" in lower:
        return ActionType.REPLY
    if intent in ("action_request", "question"):
        return ActionType.REPLY
    return ActionType.OTHER


def _infer_urgency(action_score: float, hits: list[str], tone: str) -> Urgency:
    """Map signal hits to urgency. Critical is reserved for acute blockers."""
    acute = any(h in hits for h in ("asap", "blocked", "action_required", "escalate"))
    same_day = any(h in hits for h in ("deadline_eod", "deadline_tomorrow"))
    has_deadline = same_day or any(h.startswith("deadline") or h == "due_date" for h in hits)

    # Critical only when something is acute (ASAP/blocked) or same-day + urgent tone
    if acute or (same_day and tone == "urgent"):
        return Urgency.CRITICAL if action_score >= 4 else Urgency.HIGH
    if has_deadline or action_score >= 6:
        return Urgency.HIGH
    if action_score >= 3:
        return Urgency.MEDIUM
    return Urgency.LOW


def _suggest(action_type: ActionType, subject: str, ask: Optional[str]) -> str:
    ask_bit = f" — {ask}" if ask else ""
    mapping = {
        ActionType.REPLY: f"Reply to: {subject}{ask_bit}",
        ActionType.APPROVE: f"Review and approve: {subject}",
        ActionType.SCHEDULE: f"Respond to invite / schedule: {subject}",
        ActionType.PAY: f"Pay or process invoice: {subject}",
        ActionType.REVIEW: f"Review: {subject}",
        ActionType.FOLLOW_UP: f"Follow up on: {subject}",
        ActionType.OTHER: f"Take action on: {subject}",
    }
    return mapping.get(action_type, mapping[ActionType.OTHER])


def classify_email(
    email: EmailMessage,
    ctx: Optional[EmailContext] = None,
) -> ActionClassification:
    text = f"{email.subject}\n{email.sender}\n{email.snippet}\n{email.body}\n{' '.join(email.labels)}"
    action_score, action_hits = _score(text, ACTION_SIGNALS)
    non_score, non_hits = _score(text, NON_ACTION_SIGNALS)

    # Intent priors from ContextAgent
    intent = ctx.intent if ctx else ""
    if intent in ("newsletter_or_promo", "automated_receipt", "informational_fyi"):
        non_score += 3.0
        non_hits.append(f"intent:{intent}")
    elif intent in (
        "action_request",
        "approval_request",
        "payment_request",
        "meeting_response",
        "code_review",
        "question",
    ):
        action_score += 2.0
        action_hits.append(f"intent:{intent}")

    # GitHub review requests are actionable despite noreply-ish senders
    if "requested your review" in text.lower():
        action_score += 2.0
        non_score = max(0.0, non_score - 1.0)

    needs_action = action_score > non_score and action_score >= 2.0
    # Pure FYI / receipt override
    if any(h in non_hits for h in ("no_action", "unsubscribe", "newsletter", "auto_confirm")):
        if action_score < 4.5:
            needs_action = False

    action_type = _infer_action_type(text, intent) if needs_action else ActionType.OTHER
    urgency = _infer_urgency(action_score, action_hits, ctx.tone if ctx else "neutral")
    if not needs_action:
        urgency = Urgency.LOW

    confidence = min(0.95, 0.45 + abs(action_score - non_score) * 0.07)
    if needs_action and action_score >= 5:
        confidence = min(0.95, confidence + 0.1)

    reason_parts = []
    if action_hits:
        reason_parts.append("action signals: " + ", ".join(action_hits[:6]))
    if non_hits:
        reason_parts.append("non-action signals: " + ", ".join(non_hits[:6]))
    reason = "; ".join(reason_parts) or "no strong signals"

    suggested = (
        _suggest(action_type, email.subject, ctx.ask_or_request if ctx else None)
        if needs_action
        else "No action needed"
    )

    return ActionClassification(
        email_id=email.id,
        needs_action=needs_action,
        urgency=urgency,
        action_type=action_type,
        reason=reason,
        suggested_action=suggested,
        confidence=round(confidence, 3),
    )


def _maybe_llm_enhance(
    email: EmailMessage,
    classification: ActionClassification,
    ctx: Optional[EmailContext],
) -> ActionClassification:
    """Optionally refine with Groq/OpenAI. Never fails the pipeline."""
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if not provider:
        provider = "groq" if groq_key else ("openai" if openai_key else "")
    if not provider:
        return classification

    prompt = (
        "Classify whether this email needs the recipient to take action. "
        "Return JSON with keys: needs_action (bool), urgency "
        "(low|medium|high|critical), action_type "
        "(reply|approve|schedule|pay|review|follow_up|other), "
        "reason (short), suggested_action (short), confidence (0-1).\n\n"
        f"Subject: {email.subject}\nFrom: {email.sender}\n"
        f"Body: {email.body[:1500]}\n"
        f"Heuristic guess: {classification.model_dump_json()}\n"
        f"Context: {(ctx.model_dump_json() if ctx else '{}')}"
    )

    try:
        import httpx

        if provider == "groq" and groq_key:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}"}
            model = "llama-3.1-8b-instant"
        elif provider == "openai" and openai_key:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {openai_key}"}
            model = "gpt-4o-mini"
        else:
            return classification

        payload = {
            "model": model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "You are an email triage assistant. Reply with JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
        }
        with httpx.Client(timeout=12.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
        return ActionClassification(
            email_id=email.id,
            needs_action=bool(data.get("needs_action", classification.needs_action)),
            urgency=Urgency(str(data.get("urgency", classification.urgency.value)).lower()),
            action_type=ActionType(
                str(data.get("action_type", classification.action_type.value)).lower()
            ),
            reason=str(data.get("reason", classification.reason)) + " [llm]",
            suggested_action=str(
                data.get("suggested_action", classification.suggested_action)
            ),
            confidence=float(data.get("confidence", classification.confidence)),
        )
    except Exception:
        return classification


class ActionClassifierAgent(BaseAgent):
    name = "ActionClassifierAgent"
    description = (
        "Classifies emails as actionable or not with urgency, type, and suggestions. "
        "Uses heuristics by default; optionally enhances with LLM when API keys exist."
    )
    capabilities = [
        "heuristic_classification",
        "urgency_scoring",
        "action_type_detection",
        "optional_llm_enhancement",
    ]

    def run(self, context: dict[str, Any]) -> AgentResult:
        result = AgentResult(agent=self.name)
        raw_emails = context.get("emails") or []
        raw_contexts = context.get("contexts") or []
        emails = [EmailMessage(**e) if isinstance(e, dict) else e for e in raw_emails]
        contexts = {
            (c["email_id"] if isinstance(c, dict) else c.email_id): (
                EmailContext(**c) if isinstance(c, dict) else c
            )
            for c in raw_contexts
        }

        use_llm = bool(
            os.getenv("GROQ_API_KEY", "").strip()
            or os.getenv("OPENAI_API_KEY", "").strip()
        )
        classifications: list[ActionClassification] = []
        for email in emails:
            base = classify_email(email, contexts.get(email.id))
            final = _maybe_llm_enhance(email, base, contexts.get(email.id)) if use_llm else base
            classifications.append(final)

        actionable = [c for c in classifications if c.needs_action]
        result.data = {
            "classifications": [c.model_dump() for c in classifications],
            "actionable_count": len(actionable),
            "used_llm": use_llm,
        }
        result.message = (
            f"Classified {len(classifications)} emails; {len(actionable)} need action"
        )
        result.log(result.message, actionable=len(actionable), used_llm=use_llm)
        result.log(
            "Classification method: "
            + ("heuristics + LLM" if use_llm else "pure heuristics (no API key)"),
            level="decision",
        )
        return result
