"""FastAPI entrypoint for the Performance Intelligence Agent."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import data_loader
from orchestrator import analyse_employee

app = FastAPI(
    title="Performance Intelligence Agent",
    description="Multi-agent employee performance analysis system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyseRequest(BaseModel):
    employee_name: str = Field(..., min_length=1)


@app.on_event("startup")
def startup() -> None:
    """Ensure Excel datasets are loaded when the server starts."""
    try:
        if not data_loader.data_ready():
            data_loader.load_all_data()
            data_loader.data_ready.cache_clear()
        print("[main] Performance Intelligence Agent ready")
        print(f"[main] Data path: {data_loader.DATA_PATH}")
        print(f"[main] Employees loaded: {len(data_loader.get_all_employees())}")
    except Exception as exc:  # noqa: BLE001
        print(f"[main] Startup data load failed: {exc}")


@app.get("/health")
def health() -> Dict[str, str]:
    return {
        "status": "ok",
        "message": "Performance Intelligence Agent running",
    }


@app.get("/employees")
def employees() -> Dict[str, Any]:
    if not data_loader.data_ready():
        try:
            data_loader.load_all_data()
            data_loader.data_ready.cache_clear()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"employees": data_loader.get_all_employees()}


@app.post("/analyse")
def analyse(body: AnalyseRequest) -> Dict[str, Any]:
    print(f"[main] /analyse requested for: {body.employee_name}")
    result = analyse_employee(body.employee_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
