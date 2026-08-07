"""Leave / attendance specialist agent."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def _month_label(ts: pd.Timestamp) -> str:
    return ts.strftime("%b %Y")


def analyse_leave(
    employee_df: pd.DataFrame,
    team_df: pd.DataFrame,
    employee_name: str,
) -> Dict[str, Any]:
    """Analyse leave patterns for one employee vs the team."""
    print(f"[leave_agent] Analysing leave for {employee_name}")

    emp = employee_df.copy()
    team = team_df.copy()

    total_leave_days = int(len(emp))

    if total_leave_days == 0:
        return {
            "metrics": {
                "total_leave_days": 0,
                "sick_days": 0,
                "casual_days": 0,
                "annual_days": 0,
                "team_avg_leave": 0.0,
                "monday_leaves": 0,
                "monday_pct": 0.0,
                "peak_leave_months": [],
                "leave_by_month": [],
            },
            "findings": [f"No leave records found for {employee_name}"],
            "status": "completed",
        }

    leave_type = emp["Leave Type"].astype(str).str.strip()
    sick_days = int((leave_type.str.casefold() == "sick").sum())
    casual_days = int((leave_type.str.casefold() == "casual").sum())
    annual_days = int((leave_type.str.casefold() == "annual").sum())

    day_of_week = emp["Day of Week"].astype(str).str.strip().str.casefold()
    monday_leaves = int((day_of_week == "monday").sum())
    monday_pct = round((monday_leaves / total_leave_days) * 100, 1) if total_leave_days else 0.0

    emp["_month"] = pd.to_datetime(emp["Leave Date"], errors="coerce").dt.to_period("M")

    leave_by_month: List[Dict[str, Any]] = []
    month_counts: List[Dict[str, Any]] = []

    for period, group in emp.dropna(subset=["_month"]).groupby("_month", sort=True):
        label = _month_label(period.to_timestamp())
        count = int(len(group))
        types = group["Leave Type"].astype(str).str.strip()
        breakdown = {
            "Sick": int((types.str.casefold() == "sick").sum()),
            "Casual": int((types.str.casefold() == "casual").sum()),
            "Annual": int((types.str.casefold() == "annual").sum()),
        }
        leave_by_month.append(
            {"month": label, "count": count, "type_breakdown": breakdown}
        )
        month_counts.append({"month": label, "count": count})

    peak_leave_months = [
        item["month"]
        for item in sorted(month_counts, key=lambda x: x["count"], reverse=True)[:2]
        if item["count"] > 0
    ]

    team_avg_leave = 0.0
    if not team.empty and "Employee Name" in team.columns:
        per_employee = team.groupby(
            team["Employee Name"].astype(str).str.strip().str.casefold()
        ).size()
        if len(per_employee) > 0:
            team_avg_leave = float(round(per_employee.mean(), 1))

    metrics = {
        "total_leave_days": total_leave_days,
        "sick_days": sick_days,
        "casual_days": casual_days,
        "annual_days": annual_days,
        "team_avg_leave": team_avg_leave,
        "monday_leaves": monday_leaves,
        "monday_pct": monday_pct,
        "peak_leave_months": peak_leave_months,
        "leave_by_month": leave_by_month,
    }

    findings: List[str] = []

    if team_avg_leave > 0 and total_leave_days > team_avg_leave * 1.3:
        above_pct = round(((total_leave_days / team_avg_leave) - 1) * 100, 1)
        findings.append(
            f"Total leave days of {total_leave_days} is {above_pct}% above "
            f"team average of {team_avg_leave} days"
        )

    if monday_pct > 40:
        findings.append(
            f"Monday leave pattern detected — {monday_pct}% "
            f"of all leaves fall on Mondays"
        )

    if total_leave_days > 0 and sick_days > total_leave_days * 0.5:
        sick_pct = round((sick_days / total_leave_days) * 100, 1)
        findings.append(
            f"Sick leave represents {sick_pct}% of total leave taken"
        )

    if peak_leave_months:
        findings.append(
            "Peak leave months: " + ", ".join(peak_leave_months)
        )

    if team_avg_leave > 0 and total_leave_days <= team_avg_leave:
        findings.append(
            f"Leave usage of {total_leave_days} days is at or below "
            f"team average of {team_avg_leave} days"
        )

    return {
        "metrics": metrics,
        "findings": findings,
        "status": "completed",
    }
