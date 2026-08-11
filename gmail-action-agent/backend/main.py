"""FastAPI entrypoint for the Gmail Action Agent backend."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

from gmail.auth import GmailAuth, get_auth_status
from models import ScanRequest, StatusResponse
from orchestrator import Orchestrator

load_dotenv()

app = FastAPI(
    title="Gmail Action Agent",
    description="Multi-agent orchestrator that surfaces actionable Gmail items as notifications.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()
auth = GmailAuth()

# In-memory notification store (last scan + dismiss/complete mutations)
_notifications: list[dict[str, Any]] = []
_last_scan_at: Optional[datetime] = None


def _sync_notifications_from_scan(result: dict[str, Any]) -> None:
    global _notifications, _last_scan_at
    # Merge statuses from previous store
    prior_by_email = {n["email_id"]: n for n in _notifications if "email_id" in n}
    fresh = result.get("notifications") or []
    merged: list[dict[str, Any]] = []
    for n in fresh:
        old = prior_by_email.get(n.get("email_id"))
        if old and old.get("status") in ("dismissed", "completed"):
            # Keep terminal state unless this is a brand-new notification id set
            n = {**n, "status": old["status"], "id": old.get("id", n.get("id"))}
        merged.append(n)
    # Also keep dismissed/completed that weren't in the new actionable set
    fresh_emails = {n.get("email_id") for n in fresh}
    for old in _notifications:
        if old.get("status") in ("dismissed", "completed") and old.get("email_id") not in fresh_emails:
            merged.append(old)
    _notifications = merged
    _last_scan_at = datetime.utcnow()
    result["notifications"] = [n for n in _notifications if n.get("status") == "open"]


def _find_notification(notif_id: str) -> dict[str, Any]:
    for n in _notifications:
        if n.get("id") == notif_id:
            return n
    raise HTTPException(status_code=404, detail=f"Notification {notif_id} not found")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    auth_status = get_auth_status()
    open_count = sum(1 for n in _notifications if n.get("status") == "open")
    return StatusResponse(
        mode=auth_status["mode"],
        auth_configured=auth_status["auth_configured"],
        authenticated=auth_status["authenticated"],
        last_scan=_last_scan_at or orchestrator.last_scan_at,
        notification_count=len(_notifications),
        open_notifications=open_count,
    )


@app.get("/auth/url")
def auth_url(state: str = Query(default="gmail-action-agent")) -> dict[str, Any]:
    return auth.get_authorization_url(state=state)


@app.get("/auth/callback")
def auth_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    state: Optional[str] = None,
):
    if error:
        return HTMLResponse(
            f"<h3>Gmail authorization failed</h3><p>{error}</p>",
            status_code=400,
        )
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    try:
        result = auth.exchange_code(code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {exc}") from exc

    # Prefer redirecting a local frontend if present; otherwise show a simple page.
    frontend = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    try:
        return RedirectResponse(url=f"{frontend}/?auth=success")
    except Exception:
        return HTMLResponse(
            "<h3>Gmail connected</h3><p>You can close this window and run a scan.</p>"
            f"<pre>{result}</pre>"
        )


@app.post("/scan")
def scan(body: Optional[ScanRequest] = None) -> dict[str, Any]:
    req = body or ScanRequest()
    result = orchestrator.run_scan(
        max_emails=req.max_emails,
        query=req.query,
        task=req.task,
        prior_notifications=_notifications,
    )
    _sync_notifications_from_scan(result)
    # Return open notifications in the response payload
    result["notifications"] = [n for n in _notifications if n.get("status") == "open"]
    return result


@app.get("/notifications")
def list_notifications(
    include_closed: bool = Query(default=False),
) -> dict[str, Any]:
    items = _notifications if include_closed else [
        n for n in _notifications if n.get("status") == "open"
    ]
    return {
        "notifications": items,
        "count": len(items),
        "last_scan": (_last_scan_at or orchestrator.last_scan_at),
        "mode": get_auth_status()["mode"],
    }


@app.post("/notifications/{notif_id}/dismiss")
def dismiss_notification(notif_id: str) -> dict[str, Any]:
    notif = _find_notification(notif_id)
    notif["status"] = "dismissed"
    return {"ok": True, "notification": notif}


@app.post("/notifications/{notif_id}/complete")
def complete_notification(notif_id: str) -> dict[str, Any]:
    notif = _find_notification(notif_id)
    notif["status"] = "completed"
    return {"ok": True, "notification": notif}


@app.get("/agents")
def list_agents() -> dict[str, Any]:
    return {
        "orchestrator": {
            "name": "Orchestrator",
            "description": (
                "Routes tasks to specialist sub-agents, oversees quality, "
                "and decides which agent to call next."
            ),
            "capabilities": [
                "task_routing",
                "quality_gate",
                "pipeline_orchestration",
                "agent_registry",
            ],
        },
        "agents": orchestrator.list_agents(),
    }


@app.get("/pipeline/log")
def pipeline_log() -> dict[str, Any]:
    if not orchestrator.last_result:
        return {"agent_log": [], "message": "No pipeline has run yet. POST /scan first."}
    return {
        "agent_log": orchestrator.last_result.get("agent_log") or [],
        "pipeline_meta": orchestrator.last_result.get("pipeline_meta"),
        "quality_report": orchestrator.last_result.get("quality_report"),
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
