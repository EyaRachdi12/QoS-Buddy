"""
Data Manager Agent: load unified FILLED dataset, transform, cache, optional BO filter.
Enrichment metadata is read-only sidecar (never merges into KPI rows).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from core.config import (
    PROCESSED_FALLBACK_CSV,
    SCRAPED_CATALOG_JSON,
    UNIFIED_FILLED_CSV,
)
from core.filled_transform import apply_filled_column_mapping, finalize_diagnostic_dataframe


class DataManagerAgent:
    def __init__(self, data_path: Optional[Path] = None):
        self._path = Path(data_path) if data_path else self._default_path()
        self._df: Optional[pd.DataFrame] = None
        self._raw_mtime: Optional[float] = None
        self._last_refresh: Optional[datetime] = None

    def _default_path(self) -> Path:
        if UNIFIED_FILLED_CSV.exists():
            return UNIFIED_FILLED_CSV
        if PROCESSED_FALLBACK_CSV.exists():
            return PROCESSED_FALLBACK_CSV
        return UNIFIED_FILLED_CSV

    def resolved_path(self) -> Path:
        return self._path

    def get_last_refresh(self) -> Optional[str]:
        if self._last_refresh is None:
            return None
        return self._last_refresh.isoformat()

    def refresh(self, force: bool = False) -> Tuple[Optional[pd.DataFrame], str]:
        """Reload CSV from disk if missing cache or file changed."""
        path = self._path
        if not path.exists():
            self._df = None
            return None, f"Data file not found: {path}"

        mtime = path.stat().st_mtime
        if not force and self._df is not None and self._raw_mtime == mtime:
            return self._df, "cache_hit"

        raw = pd.read_csv(path)
        filled_cols = set(raw.columns)
        is_filled = (
            "risk_tier" in filled_cols
            or "RSRP_dBm" in filled_cols
            or "signal_strength_dbm" in filled_cols
        )
        if is_filled:
            raw = apply_filled_column_mapping(raw)
            self._df = finalize_diagnostic_dataframe(raw)
        else:
            df = raw.copy()
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            self._df = df

        self._raw_mtime = mtime
        self._last_refresh = datetime.utcnow()
        return self._df, "loaded"

    def get_working_frame(
        self,
        time_window_hours: Optional[int] = None,
        bo_filter: Optional[str] = None,
        max_rows: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        self.refresh()
        if self._df is None or self._df.empty:
            return None
        df = self._df
        if bo_filter and "source_bo" in df.columns:
            df = df[df["source_bo"].astype(str) == str(bo_filter)]

        if time_window_hours is not None and "timestamp" in df.columns:
            latest = df["timestamp"].max()
            if pd.notna(latest):
                cutoff = latest - timedelta(hours=time_window_hours)
                df = df[df["timestamp"] >= cutoff]

        if max_rows is not None and len(df) > max_rows:
            df = df.sort_values("timestamp").tail(max_rows)

        return df.copy()

    def enrichment_catalog_records(self) -> List[Dict[str, Any]]:
        if not SCRAPED_CATALOG_JSON.exists():
            return []
        try:
            data = json.loads(SCRAPED_CATALOG_JSON.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "records" in data:
                return list(data["records"])
        except (json.JSONDecodeError, OSError):
            pass
        return []

    def enrichment_catalog_count(self) -> int:
        return len(self.enrichment_catalog_records())