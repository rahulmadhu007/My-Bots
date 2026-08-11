"""Pydantic models for the Gmail Action Agent pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(str, Enum):
    REPLY = "reply"
    APPROVE = "approve"
    SCHEDULE = "schedule"
    PAY = "pay"
    REVIEW = "review"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class EmailMessage(BaseModel):
    id: str
    thread_id: Optional[str] = None
    subject: str = ""
    sender: str = ""
    to: str = ""
    date: Optional[str] = None
    snippet: str = ""
    body: str = ""
    labels: list[str] = Field(default_factory=list)
    is_unread: bool = False


class EmailContext(BaseModel):
    email_id: str
    intent: str = ""
    entities: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    ask_or_request: Optional[str] = None
    tone: str = "neutral"
    summary: str = ""
    signals: list[str] = Field(default_factory=list)


class ActionClassification(BaseModel):
    email_id: str
    needs_action: bool = False
    urgency: Urgency = Urgency.LOW
    action_type: ActionType = ActionType.OTHER
    reason: str = ""
    suggested_action: str = ""
    confidence: float = 0.5
    overridden_by_quality: bool = False
    quality_notes: Optional[str] = None


class Notification(BaseModel):
    id: str
    title: str
    body: str
    urgency: Urgency
    sender: str
    subject: str
    received_at: Optional[str] = None
    action_type: ActionType
    suggested_action: str
    email_id: str
    confidence: float = 0.5
    status: str = "open"  # open | dismissed | completed
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QualityReport(BaseModel):
    reviewed: int = 0
    overridden: int = 0
    filtered_out: int = 0
    average_confidence: float = 0.0
    flags: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AgentLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent: str
    level: str = "info"  # info | decision | warn | error
    message: str
    data: Optional[dict[str, Any]] = None


class PipelineMeta(BaseModel):
    task: str
    mode: str  # demo | gmail
    started_at: datetime
    finished_at: Optional[datetime] = None
    emails_fetched: int = 0
    contexts_built: int = 0
    classified: int = 0
    actionable: int = 0
    notifications: int = 0
    agents_invoked: list[str] = Field(default_factory=list)
    query: Optional[str] = None
    max_emails: int = 20


class ScanResult(BaseModel):
    notifications: list[Notification] = Field(default_factory=list)
    agent_log: list[AgentLogEntry] = Field(default_factory=list)
    pipeline_meta: PipelineMeta
    quality_report: QualityReport = Field(default_factory=QualityReport)
    emails: list[EmailMessage] = Field(default_factory=list)
    classifications: list[ActionClassification] = Field(default_factory=list)


class ScanRequest(BaseModel):
    max_emails: int = 20
    query: str = "is:inbox newer_than:7d"
    task: str = "scan_inbox"  # scan_inbox | refresh | reclassify


class AgentInfo(BaseModel):
    name: str
    description: str
    capabilities: list[str] = Field(default_factory=list)


class StatusResponse(BaseModel):
    mode: str
    auth_configured: bool
    authenticated: bool
    last_scan: Optional[datetime] = None
    notification_count: int = 0
    open_notifications: int = 0
