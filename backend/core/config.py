"""Paths and tunables for QoS Buddy backend."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

UNIFIED_FILLED_CSV = BACKEND_DIR / "unified_telecom_dataset_FILLED.csv"
PROCESSED_FALLBACK_CSV = REPO_ROOT / "data" / "processed" / "network_kpis_full.csv"

# Optional per-BO slices: backend/data/bo/BO1.csv, BO2.json, etc. — same schema as FILLED when possible.
BO_DATA_DIR = BACKEND_DIR / "data" / "bo"

ENRICHMENT_DIR = BACKEND_DIR / "data" / "enrichment"
SCRAPED_CATALOG_JSON = ENRICHMENT_DIR / "scraped_catalog.json"
SCRAPER_SEEDS_JSON = ENRICHMENT_DIR / "scraper_seeds.json"
UCI_SEEDS_JSON = ENRICHMENT_DIR / "uci_telecom_seeds.json"

MODELS_DIR = REPO_ROOT / "models"
MODEL_VERSIONS_DIR = REPO_ROOT / "outputs" / "versions"
ML_RUNTIME_META_JSON = MODELS_DIR / "ml_runtime_metadata.json"

# Scraping
SCRAPER_REQUEST_TIMEOUT_SEC = 25
SCRAPER_MIN_DELAY_SEC = float(os.getenv("SCRAPER_MIN_DELAY_SEC", "0.6"))
TELECOM_RELEVANCE_THRESHOLD = float(os.getenv("TELECOM_RELEVANCE_THRESHOLD", "0.35"))

# data.gov CKAN
DATAGOV_CKAN_API = os.getenv(
    "DATAGOV_CKAN_API",
    "https://catalog.data.gov/api/3/action/package_search",
)

# EU data discovery (REST search)
EU_DATA_API = os.getenv(
    "EU_DATA_API",
    "https://data.europa.eu/api/hub/search/datasets",
)

# Alerts persist to SQLite by default
ENABLE_DB_ALERTS = os.getenv("ENABLE_DB_ALERTS", "true").lower() == "true"

# CORS
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if o.strip()
]

# JWT Authentication
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-to-a-random-secret-string")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ──────────────────────────────────────────────
# KPI Thresholds (used by DiagnosticAgent)
# Externalized here so they can be tuned without
# editing detection logic.
# ──────────────────────────────────────────────
KPI_THRESHOLDS = {
    "RSRP": {"critical": -110, "poor": -100, "fair": -90, "good": -80},
    "SINR": {"critical": 5, "poor": 10, "fair": 15, "good": 20},
    "PRB": {"normal": 70, "moderate": 85, "high": 95},
    "MOS": {"bad": 2.5, "poor": 3.0, "fair": 3.5, "good": 4.0},
    "throughput_DL": {"critical": 10, "poor": 25, "fair": 50},
    "latency_ms": {"good": 40, "fair": 80, "poor": 150},
    "call_drop_rate": {"normal": 1, "moderate": 3, "high": 5},
    "handover_success_rate": {"critical": 85, "poor": 90, "fair": 95, "good": 98},
    "BLER": {"normal": 2, "moderate": 5, "high": 10},
}

# Busy-hour range used by capacity issue detector
BUSY_HOURS = list(range(17, 22))  # 17h–21h
