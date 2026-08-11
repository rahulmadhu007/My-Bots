"""Orchestrator Agent — routes tasks to specialist sub-agents and enforces quality."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from agents import (
    ActionClassifierAgent,
    ContextAgent,
    GmailFetcherAgent,
    NotificationAgent,
    QualityAgent,
)
from agents.base import BaseAgent
from models import (
    AgentLogEntry,
    PipelineMeta,
    QualityReport,
    ScanResult,
)


class Orchestrator:
    """
    Central brain of the Gmail Action Agent system.

    Receives a task (scan_inbox / refresh / reclassify), decides which
    sub-agents to invoke, runs a quality gate, and returns a structured result.
    """

    def __init__(self) -> None:
        self.agents: dict[str, BaseAgent] = {
            "GmailFetcherAgent": GmailFetcherAgent(),
            "ContextAgent": ContextAgent(),
            "ActionClassifierAgent": ActionClassifierAgent(),
            "QualityAgent": QualityAgent(),
            "NotificationAgent": NotificationAgent(),
        }
        self.last_result: Optional[dict[str, Any]] = None
        self.last_scan_at: Optional[datetime] = None
        self._log: list[AgentLogEntry] = []

    # ------------------------------------------------------------------ logging
    def _decision(self, message: str, **data: Any) -> None:
        entry = AgentLogEntry(
            agent="orchestrator",
            level="decision",
            message=f"[orchestrator] {message}",
            data=data or None,
        )
        self._log.append(entry)
        print(entry.message)

    def _info(self, message: str, **data: Any) -> None:
        entry = AgentLogEntry(
            agent="orchestrator",
            level="info",
            message=f"[orchestrator] {message}",
            data=data or None,
        )
        self._log.append(entry)
        print(entry.message)

    def _ingest_agent_logs(self, logs: list[dict[str, Any]]) -> None:
        for item in logs:
            self._log.append(
                AgentLogEntry(
                    timestamp=datetime.fromisoformat(item["timestamp"])
                    if isinstance(item.get("timestamp"), str)
                    else datetime.utcnow(),
                    agent=item.get("agent", "unknown"),
                    level=item.get("level", "info"),
                    message=item.get("message", ""),
                    data=item.get("data"),
                )
            )

    # ---------------------------------------------------------------- registry
    def list_agents(self) -> list[dict[str, Any]]:
        return [agent.info() for agent in self.agents.values()]

    def _route(self, agent_name: str, reason: str, context: dict[str, Any]) -> dict[str, Any]:
        agent = self.agents[agent_name]
        self._decision(f"Routing to {agent_name} because {reason}")
        result = agent.run(context)
        self._ingest_agent_logs(result.logs)
        if not result.success:
            self._info(f"{agent_name} reported failure: {result.error}")
        return result.data

    # --------------------------------------------------------------- pipelines
    def decide_pipeline(self, task: str, state: dict[str, Any]) -> list[str]:
        """Decide which agents to call based on task type and pipeline state."""
        task = (task or "scan_inbox").lower()
        has_emails = bool(state.get("emails"))
        has_classifications = bool(state.get("classifications"))

        if task == "reclassify":
            if not has_emails:
                self._decision(
                    "Task=reclassify but no cached emails — falling back to full scan pipeline"
                )
                return [
                    "GmailFetcherAgent",
                    "ContextAgent",
                    "ActionClassifierAgent",
                    "QualityAgent",
                    "NotificationAgent",
                ]
            self._decision(
                "Task=reclassify — skipping fetch; will rebuild context and classify"
            )
            return [
                "ContextAgent",
                "ActionClassifierAgent",
                "QualityAgent",
                "NotificationAgent",
            ]

        if task == "refresh":
            self._decision("Task=refresh — full inbox rescan with status preservation")
            return [
                "GmailFetcherAgent",
                "ContextAgent",
                "ActionClassifierAgent",
                "QualityAgent",
                "NotificationAgent",
            ]

        # Default: scan_inbox
        if has_emails and has_classifications and task == "scan_inbox":
            # Still do a full scan by default for scan_inbox
            pass
        self._decision("Task=scan_inbox — running full fetch → context → classify → quality → notify")
        return [
            "GmailFetcherAgent",
            "ContextAgent",
            "ActionClassifierAgent",
            "QualityAgent",
            "NotificationAgent",
        ]

    def run(
        self,
        task: str = "scan_inbox",
        max_emails: int = 20,
        query: str = "is:inbox newer_than:7d",
        prior_notifications: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        self._log = []
        started = datetime.utcnow()
        self._info(f"Starting task={task!r} max_emails={max_emails}")

        # Seed state from last scan for reclassify
        state: dict[str, Any] = {
            "task": task,
            "max_emails": max_emails,
            "query": query,
            "emails": [],
            "contexts": [],
            "classifications": [],
            "notifications": [],
            "prior_notifications": prior_notifications or [],
            "preserve_status": True,
            "mode": "demo",
            "auth_status": {},
        }
        if task == "reclassify" and self.last_result:
            state["emails"] = list(self.last_result.get("emails") or [])
            state["mode"] = self.last_result.get("pipeline_meta", {}).get("mode", "demo")
            self._info(
                f"Loaded {len(state['emails'])} cached emails for reclassify",
            )

        plan = self.decide_pipeline(task, state)
        agents_invoked: list[str] = []
        quality_report = QualityReport()
        quality_failed = False

        # Auth-aware routing note before fetch
        if "GmailFetcherAgent" in plan:
            try:
                from gmail.auth import get_auth_status

                auth_status = get_auth_status()
                state["auth_status"] = auth_status
                self._decision(
                    f"Routing to GmailFetcherAgent because auth_status={auth_status.get('mode', 'demo')}"
                )
            except Exception as exc:
                self._info(f"Could not read auth status: {exc}")

        for agent_name in plan:
            # Avoid double-logging the fetcher decision
            if agent_name == "GmailFetcherAgent" and state.get("auth_status"):
                reason = f"auth_status={state['auth_status'].get('mode', 'demo')}"
                data = self._route_quiet(agent_name, reason, state)
            elif agent_name == "ContextAgent":
                data = self._route(
                    agent_name,
                    f"emails_fetched={len(state.get('emails') or [])}",
                    state,
                )
            elif agent_name == "ActionClassifierAgent":
                data = self._route(
                    agent_name,
                    f"contexts_ready={len(state.get('contexts') or [])}",
                    state,
                )
            elif agent_name == "QualityAgent":
                data = self._route(
                    agent_name,
                    "post-classification quality gate required",
                    state,
                )
            elif agent_name == "NotificationAgent":
                data = self._route(
                    agent_name,
                    f"actionable={sum(1 for c in (state.get('classifications') or []) if c.get('needs_action'))}",
                    state,
                )
            else:
                data = self._route(agent_name, f"task={task}", state)

            agents_invoked.append(agent_name)
            state.update({k: v for k, v in data.items() if k in (
                "emails",
                "contexts",
                "classifications",
                "notifications",
                "mode",
                "auth_status",
                "quality_report",
            )})
            # Keep richer keys too
            for k, v in data.items():
                state[k] = v

            if agent_name == "QualityAgent":
                quality_failed = bool(data.get("quality_failed"))
                if data.get("quality_report"):
                    quality_report = QualityReport(**data["quality_report"])
                if quality_failed:
                    self._decision(
                        "Quality gate failed — re-routing to ActionClassifierAgent for corrective pass"
                    )
                    # Filter obvious non-actionables then reclassify
                    state["classifications"] = data.get("classifications") or state.get(
                        "classifications"
                    )
                    reclass = self._route(
                        "ActionClassifierAgent",
                        "quality_failed=true corrective reclassify",
                        state,
                    )
                    agents_invoked.append("ActionClassifierAgent")
                    state["classifications"] = reclass.get("classifications", [])
                    # Second quality pass (filter-focused)
                    self._decision(
                        "Routing to QualityAgent because corrective reclassify completed"
                    )
                    q2 = self._route(
                        "QualityAgent",
                        "second quality pass after reclassify",
                        state,
                    )
                    agents_invoked.append("QualityAgent")
                    state["classifications"] = q2.get("classifications", [])
                    if q2.get("quality_report"):
                        quality_report = QualityReport(**q2["quality_report"])
                    quality_failed = bool(q2.get("quality_failed"))

        finished = datetime.utcnow()
        notifications = state.get("notifications") or []
        emails = state.get("emails") or []
        classifications = state.get("classifications") or []
        mode = state.get("mode") or "demo"

        meta = PipelineMeta(
            task=task,
            mode=mode,
            started_at=started,
            finished_at=finished,
            emails_fetched=len(emails),
            contexts_built=len(state.get("contexts") or []),
            classified=len(classifications),
            actionable=sum(1 for c in classifications if c.get("needs_action")),
            notifications=len(notifications),
            agents_invoked=agents_invoked,
            query=query,
            max_emails=max_emails,
        )

        scan = ScanResult(
            notifications=notifications,
            agent_log=self._log,
            pipeline_meta=meta,
            quality_report=quality_report,
            emails=emails,
            classifications=classifications,
        )
        payload = scan.model_dump(mode="json")
        self.last_result = payload
        self.last_scan_at = finished
        self._info(
            f"Completed task={task} notifications={len(notifications)} mode={mode}"
        )
        return payload

    def _route_quiet(self, agent_name: str, reason: str, context: dict[str, Any]) -> dict[str, Any]:
        """Route when a decision log was already emitted for this agent."""
        agent = self.agents[agent_name]
        # Still log once in standard format if the earlier log wasn't the Routing line
        # (auth_status decision already printed). Run agent directly.
        result = agent.run(context)
        self._ingest_agent_logs(result.logs)
        return result.data

    def run_scan(
        self,
        max_emails: int = 20,
        query: str = "is:inbox newer_than:7d",
        task: str = "scan_inbox",
        prior_notifications: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        return self.run(
            task=task,
            max_emails=max_emails,
            query=query,
            prior_notifications=prior_notifications,
        )
