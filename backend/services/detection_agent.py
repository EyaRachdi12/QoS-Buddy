"""Detection Agent: Isolation Forest + simple statistical flags on QoS features."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer

IF_FEATURES = [
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
]


class DetectionAgent:
    def __init__(self, contamination: float = 0.06, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state

    def _build_feature_matrix(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        cols = [c for c in IF_FEATURES if c in df.columns]
        if not cols:
            return pd.DataFrame(), []
        X = df[cols].apply(pd.to_numeric, errors="coerce")
        imputer = SimpleImputer(strategy="median")
        X_vals = imputer.fit_transform(X)
        return pd.DataFrame(X_vals, columns=cols, index=df.index), cols

    def detect(
        self, df: pd.DataFrame, max_anomaly_records: int = 200
    ) -> Tuple[Optional[IsolationForest], Dict[str, Any], List[Dict[str, Any]]]:
        """
        Fit IsolationForest on df rows; return model meta + top anomaly records with score.
        """
        if df is None or df.empty:
            return None, {"error": "empty_frame"}, []

        X, cols = self._build_feature_matrix(df)
        if X.empty or not cols:
            return None, {"error": "no_feature_columns"}, []

        clf = IsolationForest(
            contamination=min(self.contamination, 0.5),
            random_state=self.random_state,
            n_estimators=120,
        )
        clf.fit(X)
        scores = clf.decision_function(X)
        pred = clf.predict(X)

        df_out = df.copy()
        df_out["_if_score"] = scores
        df_out["_if_outlier"] = pred == -1

        outliers = df_out[df_out["_if_outlier"]].copy()
        outliers = outliers.sort_values("_if_score")

        meta = {
            "n_samples": int(len(df_out)),
            "n_outliers": int(df_out["_if_outlier"].sum()),
            "outlier_ratio": float(df_out["_if_outlier"].mean()),
            "feature_columns": cols,
        }

        records: List[Dict[str, Any]] = []
        tail = outliers.head(max_anomaly_records)
        for _, row in tail.iterrows():
            rec = {
                "cell_id": row.get("cell_id"),
                "timestamp": str(row["timestamp"]) if "timestamp" in row and pd.notna(row["timestamp"]) else None,
                "if_score": float(row["_if_score"]),
                "kpis": {
                    k: float(row[k])
                    for k in cols
                    if k in row and pd.notna(row[k])
                },
            }
            if "source_bo" in row and pd.notna(row["source_bo"]):
                rec["source_bo"] = str(row["source_bo"])
            records.append(rec)

        return clf, meta, records

    @staticmethod
    def zscore_flags(df: pd.DataFrame, col: str, z: float = 3.5) -> pd.Series:
        if col not in df.columns:
            return pd.Series(False, index=df.index)
        s = pd.to_numeric(df[col], errors="coerce")
        m = s.mean()
        std = s.std()
        if std is None or std == 0 or np.isnan(std):
            return pd.Series(False, index=df.index)
        return (s - m).abs() > z * std
