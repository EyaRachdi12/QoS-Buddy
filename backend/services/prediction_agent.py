"""Prediction Agent: RandomForest regressor with cross-validation and model versioning."""

from __future__ import annotations

import json
import joblib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.model_selection import train_test_split, cross_val_score

from core.config import ML_RUNTIME_META_JSON, MODEL_VERSIONS_DIR

DEFAULT_FEATURES = [
    "RSRP",
    "SINR",
    "PRB_UL",
    "PRB_DL",
    "throughput_DL",
    "throughput_UL",
    "MOS",
    "BLER_UL",
    "BLER_DL",
    "CQI",
    "RLC_retransmissions",
    "handover_success_rate",
    "hour",
]


class PredictionAgent:
    def __init__(self):
        self._model: Optional[RandomForestRegressor] = None
        self._imputer: Optional[SimpleImputer] = None
        self._feature_cols: List[str] = []
        self._target: Optional[str] = None
        self._last_metrics: Dict[str, Optional[float]] = {}
        self._last_fit_at: Optional[str] = None
        self._version: int = 0
        self._training_stats: Optional[Dict[str, Any]] = None

    def _next_version_dir(self, target: str) -> Path:
        """Create versioned output directory: outputs/versions/prediction/{target}/vN/"""
        base = MODEL_VERSIONS_DIR / "prediction" / target
        base.mkdir(parents=True, exist_ok=True)
        existing = sorted(base.glob("v*"), key=lambda p: p.name)
        next_num = 1
        if existing:
            try:
                next_num = int(existing[-1].name.lstrip("v")) + 1
            except ValueError:
                next_num = len(existing) + 1
        version_dir = base / f"v{next_num}"
        version_dir.mkdir(parents=True, exist_ok=True)
        self._version = next_num
        return version_dir

    def _persist_meta(self, extra: Dict[str, Any]) -> None:
        ML_RUNTIME_META_JSON.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "prediction": {
                "target": self._target,
                "feature_cols": self._feature_cols,
                "metrics": self._last_metrics,
                "fit_at": self._last_fit_at,
                "version": self._version,
                **extra,
            }
        }
        if ML_RUNTIME_META_JSON.exists():
            try:
                existing = json.loads(ML_RUNTIME_META_JSON.read_text(encoding="utf-8"))
                if isinstance(existing, dict):
                    existing.update(payload)
                    payload = existing
            except (json.JSONDecodeError, OSError):
                pass
        ML_RUNTIME_META_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _save_versioned_model(self, target: str) -> str:
        """Save model, imputer, and metadata to a versioned directory."""
        vdir = self._next_version_dir(target)
        joblib.dump(self._model, vdir / "model.pkl")
        joblib.dump(self._imputer, vdir / "imputer.pkl")

        meta = {
            "target": self._target,
            "features": self._feature_cols,
            "metrics": self._last_metrics,
            "fit_at": self._last_fit_at,
            "version": self._version,
        }
        if self._training_stats:
            meta["training_stats"] = self._training_stats

        (vdir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"  Model saved: {vdir}")
        return str(vdir)

    def fit(
        self,
        df: pd.DataFrame,
        target: str = "latency_ms",
        max_train_rows: int = 20000,
        cv_folds: int = 5,
    ) -> Dict[str, Optional[float]]:
        if target not in df.columns:
            raise ValueError(f"Target column '{target}' not in dataframe")

        feat = [c for c in DEFAULT_FEATURES if c in df.columns]
        if not feat:
            raise ValueError("No feature columns available")

        sub = df[feat + [target]].copy()
        sub = sub.apply(pd.to_numeric, errors="coerce")
        sub = sub.dropna(subset=[target])
        sub = sub[np.isfinite(sub[target])]
        if len(sub) < 50:
            raise ValueError("Not enough rows with valid target for training")

        if len(sub) > max_train_rows:
            sub = sub.sample(n=max_train_rows, random_state=42)

        X = sub[feat]
        y = sub[target]

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.15, random_state=42
        )
        imputer = SimpleImputer(strategy="median")
        X_train_t = imputer.fit_transform(X_train)
        X_val_t = imputer.transform(X_val)

        model = RandomForestRegressor(
            n_estimators=80,
            max_depth=12,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train_t, y_train)
        pred_val = model.predict(X_val_t)
        mae = float(mean_absolute_error(y_val, pred_val))
        r2 = float(r2_score(y_val, pred_val))
        rmse = float(np.sqrt(mean_squared_error(y_val, pred_val)))

        # K-fold cross-validation for robust metrics
        X_all_t = imputer.transform(X)
        cv_scores = cross_val_score(
            model, X_all_t, y, cv=min(cv_folds, len(X) // 10), scoring="r2"
        )
        cv_r2_mean = float(cv_scores.mean())
        cv_r2_std = float(cv_scores.std())

        self._model = model
        self._imputer = imputer
        self._feature_cols = feat
        self._target = target
        self._last_metrics = {
            "mae": mae,
            "r2": r2,
            "rmse": rmse,
            "cv_r2_mean": cv_r2_mean,
            "cv_r2_std": cv_r2_std,
            "n_train": float(len(X_train)),
            "n_val": float(len(X_val)),
        }
        self._last_fit_at = datetime.utcnow().isoformat() + "Z"

        # Feature importance
        importances = dict(zip(feat, [float(x) for x in model.feature_importances_]))
        self._training_stats = {
            "feature_importances": importances,
            "cv_folds": min(cv_folds, len(X) // 10),
            "cv_scores": [float(s) for s in cv_scores],
        }

        self._persist_meta({"rows_used": len(sub)})
        self._save_versioned_model(target)
        return self._last_metrics

    def predict_latest(
        self, df: pd.DataFrame, n: int = 50
    ) -> List[Dict[str, Any]]:
        if self._model is None or self._imputer is None or not self._feature_cols or not self._target:
            raise RuntimeError("Model not trained; call fit() first")
        if self._target not in df.columns:
            raise ValueError("Target not in prediction frame")

        tail = df.sort_values("timestamp").tail(n) if "timestamp" in df.columns else df.tail(n)
        tail = tail.reset_index(drop=True)
        X = tail[self._feature_cols].apply(pd.to_numeric, errors="coerce")
        X_t = self._imputer.transform(X)
        y_hat = self._model.predict(X_t)
        y_true = pd.to_numeric(tail[self._target], errors="coerce").values

        out: List[Dict[str, Any]] = []
        for i in range(len(tail)):
            row = tail.iloc[i]
            pred = float(y_hat[i])
            actual = float(y_true[i]) if i < len(y_true) and np.isfinite(y_true[i]) else None
            err_pct = None
            if actual not in (None, 0.0) and np.isfinite(actual):
                err_pct = abs(pred - actual) / max(abs(actual), 1e-6) * 100.0
            rec: Dict[str, Any] = {
                "cell_id": row.get("cell_id"),
                "timestamp": str(row["timestamp"]) if "timestamp" in row else None,
                "predicted": pred,
                "actual": actual,
                "error_pct": round(err_pct, 2) if err_pct is not None else None,
            }
            out.append(rec)
        return out

    def status(self) -> Dict[str, Any]:
        return {
            "trained": self._model is not None,
            "target": self._target,
            "features": self._feature_cols,
            "metrics": self._last_metrics,
            "fit_at": self._last_fit_at,
            "version": self._version,
            "training_stats": self._training_stats,
        }
