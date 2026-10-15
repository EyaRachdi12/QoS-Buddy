"""
Lightweight profile of the unified FILLED CSV: counts per source_bo (BO1, BO2, BO3).
Cached on file mtime so dashboard users see real splits without rescanning every request.
"""

from __future__ import annotations

import csv
from collections import Counter
from functools import lru_cache
from pathlib import Path


def _unified_csv_path() -> Path:
    return Path(__file__).resolve().parent.parent / "unified_telecom_dataset_FILLED.csv"


@lru_cache(maxsize=8)
def _counts_for_mtime(mtime: float) -> dict[str, int]:
    path = _unified_csv_path()
    c: Counter[str] = Counter()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row.get("source_bo") or "").strip() or "(empty)"
            c[key] += 1
    return dict(c)


def invalidate_source_bo_cache() -> None:
    """Call after replacing unified CSV on disk so counts rescan."""
    _counts_for_mtime.cache_clear()


def get_source_bo_distribution() -> dict:
    path = _unified_csv_path()
    if not path.exists():
        return {
            "dataset": None,
            "counts": {},
            "total_rows": 0,
            "error": "unified_telecom_dataset_FILLED.csv not found",
        }
    mtime = path.stat().st_mtime
    counts = _counts_for_mtime(mtime)
    total = sum(counts.values())
    return {
        "dataset": path.name,
        "counts": counts,
        "total_rows": total,
        "file_mtime": mtime,
    }
