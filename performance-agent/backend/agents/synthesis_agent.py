"""AI synthesis agent — cross-references specialist findings via Groq."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

from groq import Groq


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def _tier_from_score(score: float) -> str:
    if score >= 90:
        return "Exceeds Expectations"
    if score >= 75:
        return "Meets Expectations"
    if score >= 60:
        return "Below Expectations"
    return "Needs Improvement"


def _calc_ticket_score(metrics: Dict[str, Any]) -> float:
    sla = float(metrics.get("sla_met_pct") or 0)
    turnaround = float(metrics.get("avg_turnaround") or 0)
    team_tat = float(metrics.get("team_avg_turnaround") or 0) or 1.0
    # SLA contributes up to 18, turnaround efficiency up to 7
    sla_part = (sla / 100.0) * 18.0
    tat_ratio = min(team_tat / max(turnaround, 0.1), 1.5)
    tat_part = _clamp(tat_ratio / 1.5, 0, 1) * 7.0
    return round(_clamp(sla_part + tat_part, 0, 25), 1)


def _calc_quality_score(metrics: Dict[str, Any]) -> float:
    avg = float(metrics.get("avg_quality_score") or 0)
    trend = str(metrics.get("quality_trend") or "Stable")
    base = (avg / 100.0) * 22.0
    if trend == "Improving":
        base += 2.0
    elif trend == "Declining":
        base -= 2.0
    below = int(metrics.get("months_below_target") or 0)
    base -= min(below, 4) * 0.5
    return round(_clamp(base, 0, 25), 1)


def _calc_leave_score(metrics: Dict[str, Any]) -> float:
    total = float(metrics.get("total_leave_days") or 0)
    team_avg = float(metrics.get("team_avg_leave") or 0) or 1.0
    monday_pct = float(metrics.get("monday_pct") or 0)
    sick = float(metrics.get("sick_days") or 0)

    # Start at 22; penalise excess leave / patterns
    score = 22.0
    if total > team_avg * 1.3:
        score -= min(((total / team_avg) - 1.3) * 10, 8)
    if monday_pct > 40:
        score -= 3.0
    if total > 0 and sick > total * 0.5:
        score -= 2.0
    if total <= team_avg:
        score += 2.0
    return round(_clamp(score, 0, 25), 1)


def _calc_cab_score(metrics: Dict[str, Any]) -> float:
    attendance = float(metrics.get("attendance_pct") or 0)
    no_shows = int(metrics.get("no_show_count") or 0)
    notice = float(metrics.get("avg_notice_hours") or 0)
    cancellations = int(metrics.get("cancellation_count") or 0)

    score = (attendance / 100.0) * 20.0
    if no_shows > 2:
        score -= min(no_shows, 5)
    if cancellations > 1 and notice < 24:
        score -= 2.0
    if attendance >= 95:
        score += 3.0
    return round(_clamp(score, 0, 25), 1)


def _fallback_synthesis(
    ticket_result: Dict[str, Any],
    quality_result: Dict[str, Any],
    leave_result: Dict[str, Any],
    cab_result: Dict[str, Any],
    employee_name: str,
) -> Dict[str, Any]:
    ticket_score = _calc_ticket_score(ticket_result.get("metrics", {}))
    quality_score = _calc_quality_score(quality_result.get("metrics", {}))
    leave_score = _calc_leave_score(leave_result.get("metrics", {}))
    cab_score = _calc_cab_score(cab_result.get("metrics", {}))
    overall = round(ticket_score + quality_score + leave_score + cab_score, 1)

    return {
        "overall_score": overall,
        "performance_tier": _tier_from_score(overall),
        "correlation_analysis": (
            f"Analysis unavailable via AI for {employee_name}. "
            "Scores were calculated from specialist agent metrics as a fallback."
        ),
        "recommendations": [
            "Review SLA performance metrics",
            "Monitor quality score trend",
            "Discuss attendance patterns",
        ],
        "summary_narrative": (
            f"Narrative unavailable. Based on calculated metrics, {employee_name} "
            f"received an overall score of {overall}/100 "
            f"({_tier_from_score(overall)})."
        ),
        "score_breakdown": {
            "ticket_score": ticket_score,
            "quality_score": quality_score,
            "leave_score": leave_score,
            "cab_score": cab_score,
        },
    }


def _build_prompt(
    ticket_result: Dict[str, Any],
    quality_result: Dict[str, Any],
    leave_result: Dict[str, Any],
    cab_result: Dict[str, Any],
    employee_name: str,
) -> str:
    payload = {
        "employee_name": employee_name,
        "ticket_metrics": ticket_result.get("metrics", {}),
        "ticket_findings": ticket_result.get("findings", []),
        "quality_metrics": quality_result.get("metrics", {}),
        "quality_findings": quality_result.get("findings", []),
        "leave_metrics": leave_result.get("metrics", {}),
        "leave_findings": leave_result.get("findings", []),
        "cab_metrics": cab_result.get("metrics", {}),
        "cab_findings": cab_result.get("findings", []),
    }

    return f"""You are a senior performance analyst synthesising results from four specialist agents
who independently analysed employee performance data for {employee_name}.

Here is the complete specialist output as JSON:
{json.dumps(payload, indent=2, default=str)}

Cross-reference findings across ticket (ServiceNow), quality, leave/attendance, and CAB datasets.
Identify correlations (for example: leave spikes vs SLA breaches, quality dips vs CAB no-shows).

Return ONLY a valid JSON object (no markdown fences) with this exact structure:
{{
  "overall_score": <number 0-100>,
  "performance_tier": "<Exceeds Expectations|Meets Expectations|Below Expectations|Needs Improvement>",
  "correlation_analysis": "<one paragraph identifying connections across datasets>",
  "recommendations": [
    "<specific evidence-based recommendation 1>",
    "<specific evidence-based recommendation 2>",
    "<specific evidence-based recommendation 3>"
  ],
  "summary_narrative": "<two paragraphs suitable for a performance review document>",
  "score_breakdown": {{
    "ticket_score": <number 0-25>,
    "quality_score": <number 0-25>,
    "leave_score": <number 0-25>,
    "cab_score": <number 0-25>
  }}
}}

Scoring guidance:
- ticket_score + quality_score + leave_score + cab_score should equal overall_score
- Be evidence-based and specific to the metrics provided
- Use professional HR/performance review language
"""


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    # Strip markdown fences if the model wraps them
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def synthesise(
    ticket_result: Dict[str, Any],
    quality_result: Dict[str, Any],
    leave_result: Dict[str, Any],
    cab_result: Dict[str, Any],
    employee_name: str,
) -> Dict[str, Any]:
    """Synthesise specialist results with Groq; fall back if API fails."""
    print(f"[synthesis_agent] Synthesising analysis for {employee_name}")

    fallback = _fallback_synthesis(
        ticket_result, quality_result, leave_result, cab_result, employee_name
    )

    prompt = _build_prompt(
        ticket_result, quality_result, leave_result, cab_result, employee_name
    )

    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        result_text = response.choices[0].message.content
        parsed = _extract_json(result_text)

        # Ensure required keys exist; fill gaps from fallback
        result = {
            "overall_score": parsed.get("overall_score", fallback["overall_score"]),
            "performance_tier": parsed.get("performance_tier", fallback["performance_tier"]),
            "correlation_analysis": parsed.get(
                "correlation_analysis", fallback["correlation_analysis"]
            ),
            "recommendations": parsed.get("recommendations", fallback["recommendations"]),
            "summary_narrative": parsed.get(
                "summary_narrative", fallback["summary_narrative"]
            ),
            "score_breakdown": parsed.get("score_breakdown", fallback["score_breakdown"]),
        }

        # Normalise recommendations to exactly 3 strings when possible
        recs: List[str] = list(result["recommendations"] or [])
        while len(recs) < 3:
            recs.append(fallback["recommendations"][len(recs)])
        result["recommendations"] = recs[:3]

        breakdown = result["score_breakdown"] or {}
        result["score_breakdown"] = {
            "ticket_score": breakdown.get(
                "ticket_score", fallback["score_breakdown"]["ticket_score"]
            ),
            "quality_score": breakdown.get(
                "quality_score", fallback["score_breakdown"]["quality_score"]
            ),
            "leave_score": breakdown.get(
                "leave_score", fallback["score_breakdown"]["leave_score"]
            ),
            "cab_score": breakdown.get(
                "cab_score", fallback["score_breakdown"]["cab_score"]
            ),
        }

        print(f"[synthesis_agent] Groq synthesis complete for {employee_name}")
        return result

    except Exception as exc:  # noqa: BLE001 — always return usable fallback
        print(f"[synthesis_agent] API failed, using fallback: {exc}")
        return fallback
