"""
Load BO-scoped data: optional per-BO file under backend/data/bo/{BOx}.csv|json,
else slice unified dataset (source_bo + time window).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from core.config import BO_DATA_DIR
from core.filled_transform import apply_filled_column_mapping, finalize_diagnostic_dataframe
from services.data_manager import DataManagerAgent


def _is_filled_schema(cols: set) -> bool:
    return (
        "risk_tier" in cols
        or "RSRP_dBm" in cols
        or "signal_strength_dbm" in cols
    )


def _transform_raw_df(raw: pd.DataFrame) -> pd.DataFrame:
    filled_cols = set(raw.columns)
    if _is_filled_schema(filled_cols):
        raw = apply_filled_column_mapping(raw)
        return finalize_diagnostic_dataframe(raw)
    df = raw.copy()
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def load_bo_dataframe(
    data_manager: DataManagerAgent,
    bo_filter: Optional[str],
    time_window_hours: int = 72,
    max_rows: int = 80000,
) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Returns (dataframe, provenance string).
    Provenance: file:BO1.csv | file:BO2.json | unified:BO1 | unified:all
    """
    bo_key = str(bo_filter).strip() if bo_filter else None

    if bo_key:
        csv_path = BO_DATA_DIR / f"{bo_key}.csv"
        json_path = BO_DATA_DIR / f"{bo_key}.json"
        for path in (csv_path, json_path):
            if path.exists():
                try:
                    if path.suffix.lower() == ".csv":
                        raw = pd.read_csv(path)
                    else:
                        raw = pd.read_json(path, orient=None)
                        if not isinstance(raw, pd.DataFrame):
                            raw = pd.DataFrame(raw)
                    df = _transform_raw_df(raw)
                    if max_rows and len(df) > max_rows:
                        df = df.sort_values("timestamp").tail(max_rows) if "timestamp" in df.columns else df.tail(max_rows)
                    return df, f"file:{path.name}"
                except Exception:
                    pass

    df = data_manager.get_working_frame(
        time_window_hours=time_window_hours,
        bo_filter=bo_key,
        max_rows=max_rows,
    )
    tag = f"unified:{bo_key or 'all'}"
    return df, tag


def cell_to_city_map(df: Optional[pd.DataFrame], limit: int = 8000) -> Dict[str, str]:
    """Latest row per cell_id → city (for alert → map highlight)."""
    if df is None or df.empty or "cell_id" not in df.columns:
        return {}
    if "city" not in df.columns:
        return {}
    sub = df.sort_values("timestamp").tail(limit) if "timestamp" in df.columns else df.tail(limit)
    out: Dict[str, str] = {}
    for _, row in sub.iterrows():
        cid = row.get("cell_id")
        city = row.get("city")
        if cid is not None and pd.notna(city):
            out[str(cid)] = str(city)
    return out


def bo_dashboard_bundle(
    data_manager: DataManagerAgent,
    diagnostic_agent: Any,
    bo_filter: Optional[str],
    time_window_hours: int = 24,
) -> Dict[str, Any]:
    df, source = load_bo_dataframe(
        data_manager,
        bo_filter,
        time_window_hours=max(72, time_window_hours * 3),
        max_rows=60000,
    )

    alerts: list = []
    if df is not None and not df.empty and hasattr(diagnostic_agent, "analyze_batch"):
        try:
            alerts = diagnostic_agent.analyze_batch(df, time_window_hours=time_window_hours)
        except Exception:
            alerts = []

    sev_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "NONE": 4}

    def _sort_key(a: Dict[str, Any]):
        s = str(a.get("severity") or "").upper()
        return (sev_rank.get(s, 9), int(a.get("priority") or 99))

    alerts = sorted(alerts, key=_sort_key)[:200]

    cell_map = cell_to_city_map(df)

    agg: Dict[str, Any] = {"row_count": 0}
    if df is not None and not df.empty:
        agg["row_count"] = int(len(df))
        if "latency_ms" in df.columns:
            agg["avg_latency_ms"] = round(float(pd.to_numeric(df["latency_ms"], errors="coerce").mean()), 2)
        if "MOS" in df.columns:
            agg["avg_mos"] = round(float(pd.to_numeric(df["MOS"], errors="coerce").mean()), 3)
        if "PRB_DL" in df.columns and "PRB_UL" in df.columns:
            agg["avg_prb_dl"] = round(float(pd.to_numeric(df["PRB_DL"], errors="coerce").mean()), 2)
            agg["avg_prb_ul"] = round(float(pd.to_numeric(df["PRB_UL"], errors="coerce").mean()), 2)
        if "anomaly_flag" in df.columns:
            af = pd.to_numeric(df["anomaly_flag"], errors="coerce").fillna(0)
            agg["anomaly_count"] = int((af > 0).sum())
        if "sla_breach_risk" in df.columns:
            agg["avg_sla_breach_risk"] = round(float(pd.to_numeric(df["sla_breach_risk"], errors="coerce").mean()), 4)
        if "capex_score" in df.columns:
            agg["avg_capex_score"] = round(float(pd.to_numeric(df["capex_score"], errors="coerce").mean()), 2)

    return {
        "bo_filter": bo_filter,
        "data_source": source,
        "row_count": agg["row_count"],
        "aggregates": agg,
        "alerts": alerts[:200],
        "cell_zone_map": cell_map,
    }
