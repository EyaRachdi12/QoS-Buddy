"""Data Drift Detection: compare incoming data distribution against training baseline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# KPI columns to monitor for drift
DRIFT_FEATURES = [
    "RSRP", "SINR", "PRB_DL", "PRB_UL", "throughput_DL",
    "latency_ms", "MOS", "BLER_DL", "handover_success_rate",
]

# Population Stability Index thresholds
PSI_THRESHOLD_WARNING = 0.10
PSI_THRESHOLD_CRITICAL = 0.25


class DriftDetector:
    """Detects distribution drift between a reference (training) dataset and new data."""

    def __init__(self):
        self._reference_stats: Optional[Dict[str, Dict[str, float]]] = None
        self._reference_histograms: Optional[Dict[str, np.ndarray]] = None
        self._bins: Optional[Dict[str, np.ndarray]] = None

    def set_reference(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute and store reference distributions from the training dataset."""
        stats = {}
        histograms = {}
        bins = {}

        cols = [c for c in DRIFT_FEATURES if c in df.columns]
        for col in cols:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) < 20:
                continue
            stats[col] = {
                "mean": float(s.mean()),
                "std": float(s.std()),
                "median": float(s.median()),
                "q25": float(s.quantile(0.25)),
                "q75": float(s.quantile(0.75)),
                "min": float(s.min()),
                "max": float(s.max()),
                "n": int(len(s)),
            }
            hist, bin_edges = np.histogram(s, bins=20)
            histograms[col] = hist.astype(float) / hist.sum()
            bins[col] = bin_edges

        self._reference_stats = stats
        self._reference_histograms = histograms
        self._bins = bins
        return {"features_tracked": list(stats.keys()), "reference_rows": len(df)}

    def check_drift(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compare new data against reference distributions. Returns per-feature drift report."""
        if not self._reference_stats or not self._reference_histograms:
            return {"error": "No reference set. Call set_reference() first."}

        results = {}
        drifted_features: List[str] = []

        for col, ref_hist in self._reference_histograms.items():
            if col not in df.columns:
                continue

            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) < 10:
                results[col] = {"status": "insufficient_data", "n": int(len(s))}
                continue

            # Compute histogram using same bins as reference
            new_hist, _ = np.histogram(s, bins=self._bins[col])
            new_hist = new_hist.astype(float) / max(new_hist.sum(), 1)

            # PSI (Population Stability Index)
            psi = self._compute_psi(ref_hist, new_hist)

            # Simple stat comparison
            ref = self._reference_stats[col]
            mean_shift = abs(float(s.mean()) - ref["mean"]) / max(ref["std"], 1e-6)

            status = "ok"
            if psi > PSI_THRESHOLD_CRITICAL:
                status = "critical"
                drifted_features.append(col)
            elif psi > PSI_THRESHOLD_WARNING:
                status = "warning"
                drifted_features.append(col)

            results[col] = {
                "status": status,
                "psi": round(psi, 4),
                "mean_shift_sigma": round(mean_shift, 2),
                "ref_mean": ref["mean"],
                "new_mean": round(float(s.mean()), 4),
                "ref_std": ref["std"],
                "new_std": round(float(s.std()), 4),
                "n": int(len(s)),
            }

        overall = "ok"
        if any(r.get("status") == "critical" for r in results.values()):
            overall = "critical"
        elif any(r.get("status") == "warning" for r in results.values()):
            overall = "warning"

        return {
            "overall_status": overall,
            "features": results,
            "drifted_features": drifted_features,
            "total_checked": len(results),
        }

    @staticmethod
    def _compute_psi(expected: np.ndarray, actual: np.ndarray, epsilon: float = 1e-6) -> float:
        """Population Stability Index between two distributions."""
        expected = np.clip(expected, epsilon, None)
        actual = np.clip(actual, epsilon, None)
        psi = np.sum((actual - expected) * np.log(actual / expected))
        return float(psi)

    def has_reference(self) -> bool:
        return self._reference_stats is not None
