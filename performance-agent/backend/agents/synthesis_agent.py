"""AI synthesis agent — cross-references specialist findings via Groq.

When GROQ_API_KEY is available, uses Groq (llama3-8b-8192).
When the key is missing or the API fails, synthesises locally from
specialist metrics so the dashboard always returns real analysis.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Tuple

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


def _score_breakdown(
    ticket_result: Dict[str, Any],
    quality_result: Dict[str, Any],
    leave_result: Dict[str, Any],
    cab_result: Dict[str, Any],
) -> Tuple[float, float, float, float, float]:
    ticket_score = _calc_ticket_score(ticket_result.get("metrics", {}))
    quality_score = _calc_quality_score(quality_result.get("metrics", {}))
    leave_score = _calc_leave_score(leave_result.get("metrics", {}))
    cab_score = _calc_cab_score(cab_result.get("metrics", {}))
    overall = round(ticket_score + quality_score + leave_score + cab_score, 1)
    return ticket_score, quality_score, leave_score, cab_score, overall


def _build_correlation_analysis(
    employee_name: str,
    ticket_m: Dict[str, Any],
    quality_m: Dict[str, Any],
    leave_m: Dict[str, Any],
    cab_m: Dict[str, Any],
) -> str:
    signals: List[str] = []

    sla = float(ticket_m.get("sla_met_pct") or 0)
    team_sla = float(ticket_m.get("team_avg_sla_pct") or 0)
    tat = float(ticket_m.get("avg_turnaround") or 0)
    team_tat = float(ticket_m.get("team_avg_turnaround") or 0)
    q_avg = float(quality_m.get("avg_quality_score") or 0)
    q_trend = str(quality_m.get("quality_trend") or "Stable")
    leave_total = float(leave_m.get("total_leave_days") or 0)
    team_leave = float(leave_m.get("team_avg_leave") or 0)
    monday_pct = float(leave_m.get("monday_pct") or 0)
    sick = float(leave_m.get("sick_days") or 0)
    cab_pct = float(cab_m.get("attendance_pct") or 0)
    team_cab = float(cab_m.get("team_avg_attendance") or 0)
    no_shows = int(cab_m.get("no_show_count") or 0)
    primary_error = quality_m.get("primary_error_type")
    below_months = int(quality_m.get("months_below_target") or 0)

    high_leave = team_leave > 0 and leave_total > team_leave * 1.3
    weak_sla = sla < max(team_sla - 5, 85)
    slow_tat = team_tat > 0 and tat > team_tat * 1.2
    weak_quality = q_avg < 95
    weak_cab = cab_pct < team_cab - 10 if team_cab else cab_pct < 85

    if high_leave and (weak_sla or slow_tat):
        signals.append(
            f"elevated leave usage ({int(leave_total)} days vs team avg "
            f"{team_leave}) aligns with weaker ticket outcomes "
            f"(SLA met {sla}%, avg turnaround {tat}h)"
        )
    elif weak_sla and slow_tat:
        signals.append(
            f"SLA attainment of {sla}% and turnaround of {tat}h both lag the "
            f"team benchmarks ({team_sla}% / {team_tat}h), indicating delivery "
            f"pressure rather than an isolated metric spike"
        )

    if high_leave and weak_quality:
        signals.append(
            f"quality averages {q_avg}% with {below_months} months below the "
            f"95% target during the same period of higher absence"
        )
    elif weak_quality and q_trend == "Declining":
        signals.append(
            f"quality is both below target ({q_avg}%) and trending downward, "
            f"suggesting process control issues that may also affect ticket work"
        )
    elif weak_quality and primary_error:
        signals.append(
            f"recurring quality theme of {primary_error} coincides with "
            f"{below_months} below-target months"
        )

    if monday_pct > 40 and (weak_sla or weak_cab):
        signals.append(
            f"a Monday leave concentration ({monday_pct}%) sits alongside "
            f"delivery/compliance gaps, pointing to start-of-week continuity risk"
        )

    if weak_cab and no_shows > 2:
        signals.append(
            f"CAB attendance of {cab_pct}% with {no_shows} no-shows signals "
            f"governance exposure that can compound operational instability"
        )
    elif weak_cab:
        signals.append(
            f"CAB attendance ({cab_pct}%) trails the team ({team_cab}%), "
            f"reducing change-control visibility"
        )

    if leave_total > 0 and sick > leave_total * 0.5 and (weak_sla or weak_quality):
        sick_pct = round((sick / leave_total) * 100, 1)
        signals.append(
            f"sick leave forms {sick_pct}% of absences, which may help explain "
            f"inconsistent SLA and quality outcomes across the review window"
        )

    if not signals:
        strengths: List[str] = []
        if sla >= 95:
            strengths.append(f"strong SLA delivery ({sla}%)")
        if q_avg >= 95:
            strengths.append(f"quality at or above target ({q_avg}%)")
        if not high_leave:
            strengths.append("leave usage within team norms")
        if cab_pct >= 90:
            strengths.append(f"solid CAB compliance ({cab_pct}%)")
        if strengths:
            joined = "; ".join(strengths)
            return (
                f"Across ServiceNow, quality, leave, and CAB datasets, "
                f"{employee_name} shows consistent cross-domain performance: "
                f"{joined}. No adverse multi-dataset correlation was detected "
                f"for the April–September 2024 review period."
            )
        return (
            f"Cross-agent review for {employee_name} shows mixed but largely "
            f"independent signals across ticket, quality, leave, and CAB data, "
            f"with no single dominant adverse correlation across datasets."
        )

    lead = (
        f"Cross-referencing ticket, quality, leave, and CAB results for "
        f"{employee_name} reveals connected performance patterns: "
    )
    return lead + "; ".join(signals) + "."


def _build_recommendations(
    ticket_m: Dict[str, Any],
    quality_m: Dict[str, Any],
    leave_m: Dict[str, Any],
    cab_m: Dict[str, Any],
    ticket_score: float,
    quality_score: float,
    leave_score: float,
    cab_score: float,
) -> List[str]:
    candidates: List[Tuple[float, str]] = []

    sla = float(ticket_m.get("sla_met_pct") or 0)
    team_sla = float(ticket_m.get("team_avg_sla_pct") or 0)
    tat = float(ticket_m.get("avg_turnaround") or 0)
    team_tat = float(ticket_m.get("team_avg_turnaround") or 0)
    breach_months = ticket_m.get("breach_by_month") or []
    worst_breach = sorted(
        breach_months, key=lambda x: x.get("breaches", 0), reverse=True
    )
    top_cat = ticket_m.get("top_category")

    if sla < 90 or ticket_score < 18:
        month_note = ""
        if worst_breach and worst_breach[0].get("breaches", 0) > 0:
            month_note = (
                f" Focus remediation on {worst_breach[0]['month']} "
                f"({worst_breach[0]['breaches']} breaches)."
            )
        candidates.append((
            100 - sla,
            f"Implement a weekly SLA recovery plan to lift met rate from "
            f"{sla}% toward the team average of {team_sla}%."
            f"{month_note}",
        ))
    if team_tat > 0 and tat > team_tat * 1.15:
        candidates.append((
            (tat / team_tat) * 20,
            f"Reduce average turnaround from {tat}h toward the team "
            f"benchmark of {team_tat}h through tighter queue triage"
            + (f" on {top_cat} tickets" if top_cat else "")
            + ".",
        ))

    q_avg = float(quality_m.get("avg_quality_score") or 0)
    q_trend = str(quality_m.get("quality_trend") or "Stable")
    primary_error = quality_m.get("primary_error_type")
    below = int(quality_m.get("months_below_target") or 0)
    if q_avg < 95 or quality_score < 18:
        err_bit = (
            f" targeting {primary_error} as the primary defect theme"
            if primary_error
            else ""
        )
        candidates.append((
            95 - q_avg + below,
            f"Run a focused quality clinic{err_bit} to restore scores from "
            f"{q_avg}% to the 95% target"
            + (f" (currently below target in {below} months)" if below else "")
            + ".",
        ))
    elif q_trend == "Declining":
        candidates.append((
            15,
            f"Arrest the declining quality trend with mid-month sampling "
            f"reviews while current average remains {q_avg}%.",
        ))

    leave_total = float(leave_m.get("total_leave_days") or 0)
    team_leave = float(leave_m.get("team_avg_leave") or 0)
    monday_pct = float(leave_m.get("monday_pct") or 0)
    sick = float(leave_m.get("sick_days") or 0)
    if team_leave > 0 and leave_total > team_leave * 1.3:
        candidates.append((
            leave_total - team_leave,
            f"Hold an attendance coaching discussion — leave of "
            f"{int(leave_total)} days is above the team average of "
            f"{team_leave} days — and agree coverage plans for peak months.",
        ))
    if monday_pct > 40:
        candidates.append((
            monday_pct / 2,
            f"Address the Monday leave pattern ({monday_pct}% of absences) "
            f"to protect start-of-week SLA and CAB commitments.",
        ))
    if leave_total > 0 and sick > leave_total * 0.5:
        sick_pct = round((sick / leave_total) * 100, 1)
        candidates.append((
            sick_pct / 3,
            f"Review wellbeing and workload factors behind sick leave "
            f"({sick_pct}% of total leave) with HR support as needed.",
        ))

    cab_pct = float(cab_m.get("attendance_pct") or 0)
    team_cab = float(cab_m.get("team_avg_attendance") or 0)
    no_shows = int(cab_m.get("no_show_count") or 0)
    notice = float(cab_m.get("avg_notice_hours") or 0)
    cancels = int(cab_m.get("cancellation_count") or 0)
    if no_shows > 2 or cab_score < 15:
        candidates.append((
            40 + no_shows * 5,
            f"Enforce CAB calendar ownership and backup coverage — "
            f"attendance is {cab_pct}% with {no_shows} no-shows "
            f"(team average {team_cab}%).",
        ))
    elif cancels > 1 and notice < 24:
        candidates.append((
            25,
            f"Require at least 24 hours notice for CAB cancellations; "
            f"current average notice is only {notice} hours across "
            f"{cancels} cancellations.",
        ))

    if sla >= 95 and q_avg >= 97:
        candidates.append((
            5,
            "Document and share current ticket/quality practices as a peer "
            "benchmark for the wider team.",
        ))
    if cab_pct >= 95 and leave_score >= 20:
        candidates.append((
            4,
            "Continue current CAB and attendance discipline; nominate as a "
            "coverage mentor for change windows.",
        ))
    if q_trend == "Improving" and q_avg < 98:
        candidates.append((
            6,
            f"Sustain the improving quality trajectory with monthly "
            f"error-trend reviews until average exceeds 98%.",
        ))

    defaults = [
        (1, "Maintain a monthly multi-metric performance huddle covering SLA, quality, leave, and CAB."),
        (0.5, "Track a personal scorecard against team averages each month and adjust workload early."),
        (0.25, "Align with the team lead on one development goal tied to the lowest domain score."),
    ]
    candidates.extend(defaults)
    candidates.sort(key=lambda x: x[0], reverse=True)

    selected: List[str] = []
    seen = set()
    for _, text in candidates:
        key = text[:48]
        if key in seen:
            continue
        seen.add(key)
        selected.append(text)
        if len(selected) == 3:
            break
    return selected


def _build_summary_narrative(
    employee_name: str,
    overall: float,
    tier: str,
    ticket_m: Dict[str, Any],
    quality_m: Dict[str, Any],
    leave_m: Dict[str, Any],
    cab_m: Dict[str, Any],
    ticket_score: float,
    quality_score: float,
    leave_score: float,
    cab_score: float,
) -> str:
    sla = float(ticket_m.get("sla_met_pct") or 0)
    tat = float(ticket_m.get("avg_turnaround") or 0)
    tickets = int(ticket_m.get("total_tickets") or 0)
    q_avg = float(quality_m.get("avg_quality_score") or 0)
    q_trend = str(quality_m.get("quality_trend") or "Stable")
    errors = int(quality_m.get("total_errors") or 0)
    leave_total = int(leave_m.get("total_leave_days") or 0)
    monday_pct = float(leave_m.get("monday_pct") or 0)
    cab_pct = float(cab_m.get("attendance_pct") or 0)
    no_shows = int(cab_m.get("no_show_count") or 0)

    domain_ranks = sorted(
        [
            ("ticket delivery", ticket_score),
            ("quality", quality_score),
            ("attendance", leave_score),
            ("CAB compliance", cab_score),
        ],
        key=lambda x: x[1],
    )
    weakest = domain_ranks[0][0]
    strongest = domain_ranks[-1][0]

    para1 = (
        f"Over the April–September 2024 review period, {employee_name} achieved "
        f"an overall performance score of {overall}/100, placing them in the "
        f"{tier} tier. Ticket delivery covered {tickets} closed items with an "
        f"SLA met rate of {sla}% and average turnaround of {tat} hours. Quality "
        f"averaged {q_avg}% ({q_trend.lower()} trend) with {errors} recorded "
        f"errors, while leave utilisation totalled {leave_total} days "
        f"(Monday share {monday_pct}%) and CAB attendance stood at {cab_pct}% "
        f"with {no_shows} no-shows."
    )

    if overall >= 90:
        para2 = (
            f"Strength is broad-based, with {strongest} leading the scorecard. "
            f"The synthesis agents found no material adverse correlation across "
            f"datasets. Recommended focus is to sustain current standards and "
            f"codify practices that keep {weakest} equally resilient under peak load."
        )
    elif overall >= 75:
        para2 = (
            f"Performance broadly meets expectations, with {strongest} as the "
            f"standout domain and {weakest} as the primary improvement lever. "
            f"Cross-agent review indicates manageable risk; targeted coaching in "
            f"{weakest} should be sufficient to protect team benchmarks through "
            f"the next cycle."
        )
    elif overall >= 60:
        para2 = (
            f"Results are below expectations, driven mainly by weaker "
            f"{weakest} outcomes relative to {strongest}. Specialist agents "
            f"identified linked pressure points across operational and attendance "
            f"signals that warrant a structured improvement plan with measurable "
            f"monthly checkpoints."
        )
    else:
        para2 = (
            f"Performance requires improvement. The lowest-scoring domain is "
            f"{weakest}, and cross-dataset correlation suggests compounding risk "
            f"across delivery, quality, and compliance. A formal action plan with "
            f"close managerial oversight is recommended, while preserving "
            f"strengths observed in {strongest}."
        )

    return para1 + "\n\n" + para2


def _local_synthesis(
    ticket_result: Dict[str, Any],
    quality_result: Dict[str, Any],
    leave_result: Dict[str, Any],
    cab_result: Dict[str, Any],
    employee_name: str,
) -> Dict[str, Any]:
    """Full offline synthesis from specialist metrics — never mentions API keys."""
    ticket_m = ticket_result.get("metrics", {}) or {}
    quality_m = quality_result.get("metrics", {}) or {}
    leave_m = leave_result.get("metrics", {}) or {}
    cab_m = cab_result.get("metrics", {}) or {}

    ticket_score, quality_score, leave_score, cab_score, overall = _score_breakdown(
        ticket_result, quality_result, leave_result, cab_result
    )
    tier = _tier_from_score(overall)

    return {
        "overall_score": overall,
        "performance_tier": tier,
        "correlation_analysis": _build_correlation_analysis(
            employee_name, ticket_m, quality_m, leave_m, cab_m
        ),
        "recommendations": _build_recommendations(
            ticket_m,
            quality_m,
            leave_m,
            cab_m,
            ticket_score,
            quality_score,
            leave_score,
            cab_score,
        ),
        "summary_narrative": _build_summary_narrative(
            employee_name,
            overall,
            tier,
            ticket_m,
            quality_m,
            leave_m,
            cab_m,
            ticket_score,
            quality_score,
            leave_score,
            cab_score,
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
    """Synthesise with Groq when configured; otherwise local agent synthesis."""
    print(f"[synthesis_agent] Synthesising analysis for {employee_name}")

    local = _local_synthesis(
        ticket_result, quality_result, leave_result, cab_result, employee_name
    )

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print(
            "[synthesis_agent] GROQ_API_KEY not set — "
            "using local synthesis agent (no Anthropic dependency)"
        )
        return local

    prompt = _build_prompt(
        ticket_result, quality_result, leave_result, cab_result, employee_name
    )

    try:
        client = Groq(api_key=api_key)
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

        result = {
            "overall_score": parsed.get("overall_score", local["overall_score"]),
            "performance_tier": parsed.get("performance_tier", local["performance_tier"]),
            "correlation_analysis": parsed.get(
                "correlation_analysis", local["correlation_analysis"]
            ),
            "recommendations": parsed.get("recommendations", local["recommendations"]),
            "summary_narrative": parsed.get(
                "summary_narrative", local["summary_narrative"]
            ),
            "score_breakdown": parsed.get("score_breakdown", local["score_breakdown"]),
        }

        recs: List[str] = list(result["recommendations"] or [])
        while len(recs) < 3:
            recs.append(local["recommendations"][len(recs)])
        result["recommendations"] = recs[:3]

        breakdown = result["score_breakdown"] or {}
        result["score_breakdown"] = {
            "ticket_score": breakdown.get(
                "ticket_score", local["score_breakdown"]["ticket_score"]
            ),
            "quality_score": breakdown.get(
                "quality_score", local["score_breakdown"]["quality_score"]
            ),
            "leave_score": breakdown.get(
                "leave_score", local["score_breakdown"]["leave_score"]
            ),
            "cab_score": breakdown.get(
                "cab_score", local["score_breakdown"]["cab_score"]
            ),
        }

        # Reject any model output that still mentions Anthropic/API key setup
        blob = json.dumps(result).upper()
        if "ANTHROPIC" in blob or "API_KEY IS NOT SET" in blob:
            print("[synthesis_agent] Rejected API text mentioning keys; using local synthesis")
            return local

        print(f"[synthesis_agent] Groq synthesis complete for {employee_name}")
        return result

    except Exception as exc:  # noqa: BLE001 — always return usable local synthesis
        print(f"[synthesis_agent] Groq API failed, using local synthesis: {exc}")
        return local
