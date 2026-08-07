"""Quality scores specialist agent."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

MONTH_ORDER = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _month_sort_key(row: pd.Series) -> tuple:
    month_raw = str(row.get("Month", "")).strip()
    year = int(pd.to_numeric(row.get("Year"), errors="coerce") or 0)
    month_num = MONTH_ORDER.get(month_raw.casefold(), 0)
    return (year, month_num, month_raw)


def _format_month(month: str, year: Any) -> str:
    month = str(month).strip()
    try:
        year_i = int(year)
        return f"{month} {year_i}"
    except (TypeError, ValueError):
        return month


def analyse_quality(
    employee_df: pd.DataFrame,
    team_df: pd.DataFrame,
    employee_name: str,
) -> Dict[str, Any]:
    """Analyse quality scores and error patterns for one employee."""
    print(f"[quality_agent] Analysing quality for {employee_name}")

    emp = employee_df.copy()
    team = team_df.copy()

    if emp.empty:
        return {
            "metrics": {
                "avg_quality_score": 0.0,
                "monthly_scores": [],
                "months_below_target": 0,
                "total_errors": 0,
                "primary_error_type": None,
                "quality_trend": "Stable",
                "team_avg_quality": 0.0,
                "below_target_months": [],
            },
            "findings": [f"No quality records found for {employee_name}"],
            "status": "completed",
        }

    emp["_sort"] = emp.apply(_month_sort_key, axis=1)
    emp = emp.sort_values("_sort")

    scores = pd.to_numeric(emp["Quality Score"], errors="coerce")
    avg_quality_score = float(round(scores.mean(), 1))

    monthly_scores: List[Dict[str, Any]] = []
    below_target_months: List[str] = []

    for _, row in emp.iterrows():
        label = _format_month(row.get("Month"), row.get("Year"))
        score = float(round(pd.to_numeric(row.get("Quality Score"), errors="coerce") or 0, 1))
        team_avg = float(round(pd.to_numeric(row.get("Team Average"), errors="coerce") or 0, 1))
        monthly_scores.append({"month": label, "score": score, "team_avg": team_avg})
        if score < 95:
            below_target_months.append(label)

    months_below_target = len(below_target_months)
    total_errors = int(pd.to_numeric(emp["Error Count"], errors="coerce").fillna(0).sum())

    primary_error_type = None
    primary_months = 0
    if "Primary Error Type" in emp.columns:
        primaries = emp["Primary Error Type"].dropna()
        primaries = primaries[primaries.astype(str).str.strip().str.casefold() != "none"]
        primaries = primaries[primaries.astype(str).str.strip() != ""]
        if not primaries.empty:
            primary_error_type = str(primaries.mode().iloc[0])
            primary_months = int(
                emp.loc[
                    emp["Primary Error Type"].astype(str).str.strip() == primary_error_type,
                    "Month",
                ].nunique()
            )

    score_list = scores.dropna().tolist()
    quality_trend = "Stable"
    if len(score_list) >= 2:
        first_n = score_list[: min(3, len(score_list))]
        last_n = score_list[-min(3, len(score_list)) :]
        first_avg = sum(first_n) / len(first_n)
        last_avg = sum(last_n) / len(last_n)
        delta = last_avg - first_avg
        if abs(delta) <= 2:
            quality_trend = "Stable"
        elif delta > 2:
            quality_trend = "Improving"
        else:
            quality_trend = "Declining"

    team_avg_quality = 0.0
    if not team.empty and "Quality Score" in team.columns:
        team_avg_quality = float(
            round(pd.to_numeric(team["Quality Score"], errors="coerce").mean(), 1)
        )

    metrics = {
        "avg_quality_score": avg_quality_score,
        "monthly_scores": monthly_scores,
        "months_below_target": months_below_target,
        "total_errors": total_errors,
        "primary_error_type": primary_error_type,
        "quality_trend": quality_trend,
        "team_avg_quality": team_avg_quality,
        "below_target_months": below_target_months,
    }

    findings: List[str] = []

    if avg_quality_score < 95:
        findings.append(
            f"Average quality score of {avg_quality_score}% is below the 95% target"
        )

    total_months = len(monthly_scores)
    if months_below_target > 3:
        findings.append(
            f"Quality score fell below target in {months_below_target} "
            f"out of {total_months} months"
        )

    if primary_error_type:
        findings.append(
            f"Most common error type is {primary_error_type} — "
            f"appearing consistently across {primary_months} months"
        )

    if quality_trend == "Declining":
        findings.append(
            "Quality scores show a declining trend over the review period"
        )
    elif quality_trend == "Improving":
        findings.append(
            "Quality scores show an improving trend over the review period"
        )

    if avg_quality_score >= 98:
        findings.append(
            f"Exceptional quality performance with an average score of {avg_quality_score}%"
        )

    return {
        "metrics": metrics,
        "findings": findings,
        "status": "completed",
    }
