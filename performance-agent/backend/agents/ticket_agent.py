"""Ticket / ServiceNow specialist agent."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def _month_label(ts: pd.Timestamp) -> str:
    return ts.strftime("%b %Y")


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def analyse_tickets(
    employee_df: pd.DataFrame,
    team_df: pd.DataFrame,
    employee_name: str,
) -> Dict[str, Any]:
    """Analyse ServiceNow ticket performance for one employee vs the team."""
    print(f"[ticket_agent] Analysing tickets for {employee_name}")

    emp = employee_df.copy()
    team = team_df.copy()

    total_tickets = int(len(emp))

    if total_tickets == 0:
        return {
            "metrics": {
                "total_tickets": 0,
                "sla_met_count": 0,
                "sla_met_pct": 0.0,
                "sla_breach_count": 0,
                "sla_breach_pct": 0.0,
                "avg_turnaround": 0.0,
                "monthly_volume": [],
                "monthly_sla": [],
                "top_category": None,
                "breach_by_month": [],
                "team_avg_turnaround": 0.0,
                "team_avg_sla_pct": 0.0,
            },
            "findings": [f"No ticket records found for {employee_name}"],
            "status": "completed",
        }

    sla_col = emp["SLA Met"].astype(str).str.strip().str.casefold()
    sla_met_count = int((sla_col == "yes").sum())
    sla_breach_count = int((sla_col == "no").sum())
    sla_met_pct = _safe_pct(sla_met_count, total_tickets)
    sla_breach_pct = _safe_pct(sla_breach_count, total_tickets)

    avg_turnaround = float(round(pd.to_numeric(emp["Turnaround Hours"], errors="coerce").mean(), 1))

    emp["_month"] = pd.to_datetime(emp["Date Closed"], errors="coerce").dt.to_period("M")
    monthly_volume: List[Dict[str, Any]] = []
    monthly_sla: List[Dict[str, Any]] = []
    breach_by_month: List[Dict[str, Any]] = []

    for period, group in emp.dropna(subset=["_month"]).groupby("_month", sort=True):
        label = _month_label(period.to_timestamp())
        count = int(len(group))
        g_sla = group["SLA Met"].astype(str).str.strip().str.casefold()
        met = int((g_sla == "yes").sum())
        breaches = int((g_sla == "no").sum())
        monthly_volume.append({"month": label, "count": count})
        monthly_sla.append({"month": label, "pct": _safe_pct(met, count)})
        breach_by_month.append({"month": label, "breaches": breaches})

    top_category = None
    if "Category" in emp.columns and not emp["Category"].dropna().empty:
        top_category = str(emp["Category"].mode().iloc[0])

    # Team comparisons
    team_avg_turnaround = 0.0
    team_avg_sla_pct = 0.0
    if len(team) > 0:
        team_avg_turnaround = float(
            round(pd.to_numeric(team["Turnaround Hours"], errors="coerce").mean(), 1)
        )
        team_sla = team["SLA Met"].astype(str).str.strip().str.casefold()
        team_met = int((team_sla == "yes").sum())
        team_avg_sla_pct = _safe_pct(team_met, len(team))

    metrics = {
        "total_tickets": total_tickets,
        "sla_met_count": sla_met_count,
        "sla_met_pct": sla_met_pct,
        "sla_breach_count": sla_breach_count,
        "sla_breach_pct": sla_breach_pct,
        "avg_turnaround": avg_turnaround,
        "monthly_volume": monthly_volume,
        "monthly_sla": monthly_sla,
        "top_category": top_category,
        "breach_by_month": breach_by_month,
        "team_avg_turnaround": team_avg_turnaround,
        "team_avg_sla_pct": team_avg_sla_pct,
    }

    findings: List[str] = []

    if sla_breach_pct > 15:
        findings.append(
            f"SLA breach rate of {sla_breach_pct}% is significantly "
            f"above team average of {team_avg_sla_pct}%"
            if sla_breach_pct > team_avg_sla_pct
            else f"SLA breach rate of {sla_breach_pct}% exceeds the 15% threshold "
            f"(team average {team_avg_sla_pct}%)"
        )

    if team_avg_turnaround > 0 and avg_turnaround > team_avg_turnaround * 1.2:
        over_pct = round(((avg_turnaround / team_avg_turnaround) - 1) * 100, 1)
        findings.append(
            f"Average turnaround of {avg_turnaround} hours exceeds "
            f"team average of {team_avg_turnaround} hours by {over_pct}%"
        )

    sorted_breaches = sorted(breach_by_month, key=lambda x: x["breaches"], reverse=True)
    for item in sorted_breaches[:3]:
        if item["breaches"] > 0:
            findings.append(
                f"Highest SLA breach rate occurred in {item['month']} "
                f"with {item['breaches']} breaches"
            )

    if sla_met_pct >= 95:
        findings.append(
            f"Strong SLA performance — {sla_met_pct}% of tickets met SLA"
        )

    if top_category:
        findings.append(f"Most common ticket category is {top_category}")

    return {
        "metrics": metrics,
        "findings": findings,
        "status": "completed",
    }
