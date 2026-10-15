"""
Single source of truth for unified FILLED CSV -> KPI column mapping.
Used by DiagnosticAgent, TelecomDataPipeline, and DataManagerAgent.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def apply_filled_column_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map unified_telecom_dataset_FILLED.csv columns to the internal KPI schema.
    Preserves BO and rawQoS helper columns; does not drop columns (wide frame).
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if "cell_id" not in df.columns and "entity_id" in df.columns:
        df["cell_id"] = df["entity_id"]

    df["RSRP"] = pd.to_numeric(
        df.get("RSRP_dBm", df.get("signal_strength_dbm")), errors="coerce"
    )
    df["SINR"] = pd.to_numeric(df.get("SINR_dB", pd.NA), errors="coerce")
    df["PRB_DL"] = pd.to_numeric(df.get("PRBUsageDL", pd.NA), errors="coerce")
    df["PRB_UL"] = pd.to_numeric(df.get("PRBUsageUL", pd.NA), errors="coerce")
    df["throughput_DL"] = pd.to_numeric(df.get("meanThr_DL", pd.NA), errors="coerce")
    df["throughput_UL"] = pd.to_numeric(df.get("meanThr_UL", pd.NA), errors="coerce")
    df["latency_ms"] = pd.to_numeric(df.get("latency_ms", pd.NA), errors="coerce")

    sla_breach_risk = pd.to_numeric(df.get("sla_breach_risk", pd.NA), errors="coerce")
    df["MOS"] = (5 - 4 * sla_breach_risk).clip(1.0, 5.0)

    error_rate = pd.to_numeric(df.get("error_rate", pd.NA), errors="coerce")
    df["BLER_DL"] = (error_rate * 5.0).clip(0.5, 20.0)
    df["BLER_UL"] = (error_rate * 4.5).clip(0.5, 20.0)

    df["CQI"] = pd.to_numeric(df.get("CQI", pd.NA), errors="coerce")
    df["RLC_retransmissions"] = pd.to_numeric(df.get("RLC_RetxRate_pct", pd.NA), errors="coerce")

    df["call_drop_rate"] = pd.to_numeric(df.get("ERAB_DropRate_pct", pd.NA), errors="coerce")
    df["handover_success_rate"] = pd.to_numeric(df.get("HO_SuccessRate_pct", pd.NA), errors="coerce")

    df["jitter_ms"] = pd.to_numeric(df.get("jitter_ms", pd.NA), errors="coerce")
    df["packet_loss_rate"] = pd.to_numeric(df.get("packet_loss_rate", pd.NA), errors="coerce")

    df["hour"] = df["timestamp"].dt.hour

    df["source_bo"] = df.get("source_bo", pd.NA)
    df["city"] = df.get("city", pd.NA)
    df["anomaly_flag"] = pd.to_numeric(df.get("anomaly_flag", pd.NA), errors="coerce")
    df["sla_breach_risk"] = pd.to_numeric(df.get("sla_breach_risk", pd.NA), errors="coerce")
    df["capex_score"] = pd.to_numeric(df.get("capex_score", pd.NA), errors="coerce")
    df["radio_health_score"] = pd.to_numeric(df.get("radio_health_score", pd.NA), errors="coerce")
    df["unified_risk_score"] = pd.to_numeric(df.get("unified_risk_score", pd.NA), errors="coerce")
    df["capex_priority"] = df.get("capex_priority", pd.NA)
    df["risk_tier"] = df.get("risk_tier", pd.NA)

    return df


DIAGNOSTIC_KEEP_COLS = [
    "timestamp",
    "cell_id",
    "RSRP",
    "SINR",
    "PRB_UL",
    "PRB_DL",
    "throughput_DL",
    "throughput_UL",
    "latency_ms",
    "MOS",
    "call_drop_rate",
    "handover_success_rate",
    "BLER_UL",
    "BLER_DL",
    "CQI",
    "RLC_retransmissions",
    "hour",
    "source_bo",
    "city",
    "anomaly_flag",
    "sla_breach_risk",
    "capex_score",
    "capex_priority",
    "radio_health_score",
    "unified_risk_score",
    "risk_tier",
    "jitter_ms",
    "packet_loss_rate",
]


def finalize_diagnostic_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in DIAGNOSTIC_KEEP_COLS if c in df.columns]
    return df[keep].sort_values("timestamp").reset_index(drop=True)


def _add_pipeline_issue_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    risk_tier = df.get("risk_tier", pd.Series(index=df.index, data="LOW"))
    unified_risk_score = pd.to_numeric(df.get("unified_risk_score", pd.NA), errors="coerce").fillna(0)
    anomaly_flag = pd.to_numeric(df.get("anomaly_flag", 0), errors="coerce").fillna(0)

    is_normal = (anomaly_flag == 0) & (risk_tier == "LOW")

    is_capacity = (df["PRB_DL"] >= 85) | (df["PRB_UL"] >= 85)
    is_high_latency = df["latency_ms"] >= 110
    is_call_drop = df["call_drop_rate"] >= 7
    is_handover_failure = df["handover_success_rate"] <= 80
    is_low_throughput = df["throughput_DL"] <= 12
    is_low_mos = df["MOS"] <= 2.5
    pl = df.get("packet_loss_rate", pd.Series(0.0, index=df.index))
    jt = df.get("jitter_ms", pd.Series(0.0, index=df.index))
    is_session_drop = (pl >= 2.5) | (jt >= 20)

    conditions = [
        (~is_normal) & is_capacity,
        (~is_normal) & is_high_latency,
        (~is_normal) & is_call_drop,
        (~is_normal) & is_handover_failure,
        (~is_normal) & is_low_throughput,
        (~is_normal) & is_low_mos,
        (~is_normal) & is_session_drop,
    ]
    choices = [
        "Capacity Problem",
        "High Latency",
        "Call Drop",
        "Handover Failure",
        "Low Throughput",
        "Low MOS",
        "Session Drop",
    ]
    df["issue_type"] = np.select(conditions, choices, default="Normal")

    df["severity"] = "NONE"
    df.loc[risk_tier == "CRITICAL", "severity"] = "CRITICAL"
    df.loc[risk_tier == "MEDIUM", "severity"] = "MEDIUM"
    df.loc[(risk_tier == "MEDIUM") & (unified_risk_score >= 40), "severity"] = "HIGH"
    df.loc[df["issue_type"] == "Normal", "severity"] = "NONE"
    return df


PIPELINE_KEEP_COLS = [
    "timestamp",
    "cell_id",
    "RSRP",
    "SINR",
    "PRB_UL",
    "PRB_DL",
    "throughput_DL",
    "throughput_UL",
    "latency_ms",
    "call_drop_rate",
    "handover_success_rate",
    "MOS",
    "BLER_UL",
    "BLER_DL",
    "CQI",
    "RLC_retransmissions",
    "hour",
    "issue_type",
    "severity",
]


def finalize_pipeline_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_pipeline_issue_labels(df)
    keep = [c for c in PIPELINE_KEEP_COLS if c in df.columns]
    return df[keep]
