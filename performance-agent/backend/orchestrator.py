"""Orchestrator — coordinates specialist agents and synthesis."""

from __future__ import annotations

from typing import Any, Dict, List

import data_loader
from agents.ticket_agent import analyse_tickets
from agents.quality_agent import analyse_quality
from agents.leave_agent import analyse_leave
from agents.cab_agent import analyse_cab
from agents.synthesis_agent import synthesise


def analyse_employee(employee_name: str) -> Dict[str, Any]:
    """Run the full multi-agent analysis pipeline for one employee."""
    agent_log: List[str] = []
    name = (employee_name or "").strip()

    start_msg = f"Starting analysis for {name}"
    print(f"[orchestrator] {start_msg}")
    agent_log.append(start_msg)

    ticket_df = data_loader.get_ticket_data(name)
    quality_df = data_loader.get_quality_data(name)
    leave_df = data_loader.get_leave_data(name)
    cab_df = data_loader.get_cab_data(name)

    found_msg = "✅ Data Loader — Employee found"
    print(f"[orchestrator] {found_msg}")
    agent_log.append(found_msg)

    if ticket_df.empty and quality_df.empty and leave_df.empty and cab_df.empty:
        err = {"error": "Employee not found", "agent_log": agent_log}
        print(f"[orchestrator] Employee not found: {name}")
        return err

    ticket_result = analyse_tickets(
        ticket_df, data_loader.get_team_ticket_data(), name
    )
    ticket_msg = "✅ Ticket Agent — ServiceNow analysis complete"
    print(f"[orchestrator] {ticket_msg}")
    agent_log.append(ticket_msg)

    quality_result = analyse_quality(
        quality_df, data_loader.get_team_quality_data(), name
    )
    quality_msg = "✅ Quality Agent — Quality review complete"
    print(f"[orchestrator] {quality_msg}")
    agent_log.append(quality_msg)

    leave_result = analyse_leave(
        leave_df, data_loader.get_team_leave_data(), name
    )
    leave_msg = "✅ Leave Agent — Attendance analysis complete"
    print(f"[orchestrator] {leave_msg}")
    agent_log.append(leave_msg)

    cab_result = analyse_cab(
        cab_df, data_loader.get_team_cab_data(), name
    )
    cab_msg = "✅ CAB Agent — CAB compliance review complete"
    print(f"[orchestrator] {cab_msg}")
    agent_log.append(cab_msg)

    synthesis = synthesise(
        ticket_result, quality_result, leave_result, cab_result, name
    )
    synth_msg = "✅ Synthesis Agent — Cross-reference complete"
    print(f"[orchestrator] {synth_msg}")
    agent_log.append(synth_msg)

    return {
        "employee_name": name,
        "ticket_result": ticket_result,
        "quality_result": quality_result,
        "leave_result": leave_result,
        "cab_result": cab_result,
        "synthesis": synthesis,
        "agent_log": agent_log,
    }
