"""Base agent interface shared by all specialist sub-agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class AgentResult:
    """Structured result returned by every sub-agent."""

    agent: str
    success: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    logs: list[dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def log(self, message: str, level: str = "info", **data: Any) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.agent,
            "level": level,
            "message": message,
            "data": data or None,
        }
        self.logs.append(entry)


class BaseAgent(ABC):
    """Abstract base for orchestrator-invoked specialist agents."""

    name: str = "BaseAgent"
    description: str = ""
    capabilities: list[str] = []

    @abstractmethod
    def run(self, context: dict[str, Any]) -> AgentResult:
        """Execute the agent against the shared pipeline context."""

    def info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": list(self.capabilities),
        }
