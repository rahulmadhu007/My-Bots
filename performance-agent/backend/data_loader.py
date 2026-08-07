"""
Data loader for Performance Intelligence Agent.
Loads four Excel datasets once at startup and exposes filtered accessors.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

import pandas as pd

# Primary path as specified for the deployment host
PRIMARY_DATA_PATH = "/Users/rahulm/Desktop/My Deployments/"

# Ordered fallbacks so the demo runs in other environments too
_FALLBACK_PATHS = [
    PRIMARY_DATA_PATH,
    os.path.expanduser("~/Desktop/My Deployments/"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data") + os.sep,
]


def _resolve_data_path() -> str:
    for path in _FALLBACK_PATHS:
        candidate = path if path.endswith(os.sep) else path + os.sep
        ticket_file = os.path.join(candidate, "servicenow_export.xlsx")
        if os.path.isfile(ticket_file):
            return candidate
    # Default to primary even if missing — load will raise a clear error
    return PRIMARY_DATA_PATH


DATA_PATH = _resolve_data_path()

TICKET_FILE = "servicenow_export.xlsx"
QUALITY_FILE = "quality_scores.xlsx"
LEAVE_FILE = "leave_tracker.xlsx"
CAB_FILE = "cab_records.xlsx"

tickets_df: pd.DataFrame = pd.DataFrame()
quality_df: pd.DataFrame = pd.DataFrame()
leave_df: pd.DataFrame = pd.DataFrame()
cab_df: pd.DataFrame = pd.DataFrame()


def _normalize_name_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.casefold()


def _filter_by_name(df: pd.DataFrame, name: str) -> pd.DataFrame:
    if df.empty or "Employee Name" not in df.columns:
        return df.iloc[0:0].copy()
    target = str(name).strip().casefold()
    mask = _normalize_name_series(df["Employee Name"]) == target
    return df.loc[mask].copy()


def load_all_data() -> None:
    """Load all Excel files into module-level dataframes."""
    global tickets_df, quality_df, leave_df, cab_df, DATA_PATH

    DATA_PATH = _resolve_data_path()
    print(f"[data_loader] Loading Excel files from: {DATA_PATH}")

    required = [TICKET_FILE, QUALITY_FILE, LEAVE_FILE, CAB_FILE]
    missing = [f for f in required if not os.path.isfile(os.path.join(DATA_PATH, f))]
    if missing:
        raise FileNotFoundError(
            f"Missing Excel file(s) in {DATA_PATH}: {', '.join(missing)}"
        )

    tickets_df = pd.read_excel(os.path.join(DATA_PATH, TICKET_FILE))
    quality_df = pd.read_excel(os.path.join(DATA_PATH, QUALITY_FILE))
    leave_df = pd.read_excel(os.path.join(DATA_PATH, LEAVE_FILE))
    cab_df = pd.read_excel(os.path.join(DATA_PATH, CAB_FILE))

    # Normalise common date columns when present
    if "Date Closed" in tickets_df.columns:
        tickets_df["Date Closed"] = pd.to_datetime(tickets_df["Date Closed"], errors="coerce")
    if "Leave Date" in leave_df.columns:
        leave_df["Leave Date"] = pd.to_datetime(leave_df["Leave Date"], errors="coerce")
    if "CAB Date" in cab_df.columns:
        cab_df["CAB Date"] = pd.to_datetime(cab_df["CAB Date"], errors="coerce")

    print(
        "[data_loader] Loaded "
        f"tickets={len(tickets_df)}, quality={len(quality_df)}, "
        f"leave={len(leave_df)}, cab={len(cab_df)}"
    )


def get_all_employees() -> List[str]:
    """Return sorted unique employee names across all datasets (case-insensitive dedupe)."""
    names: List[str] = []
    for df in (tickets_df, quality_df, leave_df, cab_df):
        if not df.empty and "Employee Name" in df.columns:
            names.extend(df["Employee Name"].dropna().astype(str).str.strip().tolist())

    deduped: dict[str, str] = {}
    for name in names:
        if not name:
            continue
        key = name.casefold()
        # Prefer title-cased / first-seen original spelling
        if key not in deduped:
            deduped[key] = name

    return sorted(deduped.values(), key=lambda n: n.casefold())


def get_ticket_data(name: str) -> pd.DataFrame:
    return _filter_by_name(tickets_df, name)


def get_quality_data(name: str) -> pd.DataFrame:
    return _filter_by_name(quality_df, name)


def get_leave_data(name: str) -> pd.DataFrame:
    return _filter_by_name(leave_df, name)


def get_cab_data(name: str) -> pd.DataFrame:
    return _filter_by_name(cab_df, name)


def get_team_ticket_data() -> pd.DataFrame:
    return tickets_df.copy()


def get_team_quality_data() -> pd.DataFrame:
    return quality_df.copy()


def get_team_leave_data() -> pd.DataFrame:
    return leave_df.copy()


def get_team_cab_data() -> pd.DataFrame:
    return cab_df.copy()


# Load immediately on import so data is ready at startup
try:
    load_all_data()
except Exception as exc:  # noqa: BLE001 — surface clearly at startup
    print(f"[data_loader] WARNING: failed to load data at import: {exc}")


@lru_cache(maxsize=1)
def data_ready() -> bool:
    return not (
        tickets_df.empty and quality_df.empty and leave_df.empty and cab_df.empty
    )
