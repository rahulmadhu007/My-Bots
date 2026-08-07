"""CAB compliance specialist agent."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def _month_label(ts: pd.Timestamp) -> str:
    return ts.strftime("%b %Y")


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    text = str(value).strip().casefold()
    return text in {"true", "yes", "1", "y"}


def analyse_cab(
    employee_df: pd.DataFrame,
    team_df: pd.DataFrame,
    employee_name: str,
) -> Dict[str, Any]:
    """Analyse CAB attendance and compliance for one employee."""
    print(f"[cab_agent] Analysing CAB records for {employee_name}")

    emp = employee_df.copy()
    team = team_df.copy()

    total_scheduled = int(len(emp))

    if total_scheduled == 0:
        return {
            "metrics": {
                "total_scheduled": 0,
                "attended_count": 0,
                "attendance_pct": 0.0,
                "no_show_count": 0,
                "cancellation_count": 0,
                "avg_notice_hours": 0.0,
                "team_avg_attendance": 0.0,
                "worst_months": [],
                "monthly_attendance": [],
            },
            "findings": [f"No CAB records found for {employee_name}"],
            "status": "completed",
        }

    attended_col = emp["Attended"].astype(str).str.strip().str.casefold()
    attended_count = int((attended_col == "yes").sum())
    attendance_pct = _safe_pct(attended_count, total_scheduled)

    no_show_count = int(emp["No Show"].apply(_is_true).sum())

    status_col = emp["Attendance Status"].astype(str).str.strip().str.casefold()
    cancellation_mask = status_col == "cancelled"
    cancellation_count = int(cancellation_mask.sum())

    notice_vals = pd.to_numeric(
        emp.loc[cancellation_mask, "Notice Period Hours"], errors="coerce"
    ).dropna()
    avg_notice_hours = float(round(notice_vals.mean(), 1)) if len(notice_vals) else 0.0

    emp["_month"] = pd.to_datetime(emp["CAB Date"], errors="coerce").dt.to_period("M")

    monthly_attendance: List[Dict[str, Any]] = []
    for period, group in emp.dropna(subset=["_month"]).groupby("_month", sort=True):
        label = _month_label(period.to_timestamp())
        g_att = group["Attended"].astype(str).str.strip().str.casefold()
        pct = _safe_pct(int((g_att == "yes").sum()), len(group))
        noshows = int(group["No Show"].apply(_is_true).sum())
        monthly_attendance.append({"month": label, "pct": pct, "no_shows": noshows})

    worst_months = [
        item["month"]
        for item in sorted(monthly_attendance, key=lambda x: x["pct"])[:2]
    ]

    # Team average attendance percentage (mean of per-employee attendance rates)
    team_avg_attendance = 0.0
    if not team.empty and "Employee Name" in team.columns:
        rates: List[float] = []
        for _, group in team.groupby(
            team["Employee Name"].astype(str).str.strip().str.casefold()
        ):
            g_att = group["Attended"].astype(str).str.strip().str.casefold()
            rates.append(_safe_pct(int((g_att == "yes").sum()), len(group)))
        if rates:
            team_avg_attendance = float(round(sum(rates) / len(rates), 1))

    metrics = {
        "total_scheduled": total_scheduled,
        "attended_count": attended_count,
        "attendance_pct": attendance_pct,
        "no_show_count": no_show_count,
        "cancellation_count": cancellation_count,
        "avg_notice_hours": avg_notice_hours,
        "team_avg_attendance": team_avg_attendance,
        "worst_months": worst_months,
        "monthly_attendance": monthly_attendance,
    }

    findings: List[str] = []

    if no_show_count > 2:
        findings.append(
            f"No show recorded {no_show_count} times — all without prior notice"
        )

    if attendance_pct < team_avg_attendance - 10:
        findings.append(
            f"CAB attendance of {attendance_pct}% is significantly "
            f"below team average of {team_avg_attendance}%"
        )

    if avg_notice_hours < 24 and cancellation_count > 1:
        findings.append(
            f"Cancellations average only {avg_notice_hours} hours "
            f"notice — below the expected 24 hours"
        )

    if attendance_pct >= 95:
        findings.append(
            f"Excellent CAB compliance with {attendance_pct}% attendance"
        )

    if worst_months and attendance_pct < 90:
        findings.append(
            "Lowest CAB attendance months: " + ", ".join(worst_months)
        )

    return {
        "metrics": metrics,
        "findings": findings,
        "status": "completed",
    }
