"""Pydantic DTOs for ML, enrichment, and orchestration APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Chat ──

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    include_live_insights: bool = True

    @field_validator("message")
    @classmethod
    def strip_message(cls, v: str) -> str:
        return v.strip()


class ChatResponse(BaseModel):
    answer: str
    context: List[str]
    success: bool
    timestamp: str
    intent: Optional[str] = None
    confidence: Optional[float] = None


class AnalyzeRequest(BaseModel):
    time_window_hours: int = Field(default=1, ge=1, le=168)


class BOOverviewRequest(BaseModel):
    time_window_hours: int = Field(default=24, ge=1, le=168)
    max_zones: int = Field(default=120, ge=1, le=500)


# ── Auth ──

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(..., description="User role: noc_engineer, network_planner, or executive")
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["noc_engineer", "network_planner", "executive"]
        if v.lower() not in valid_roles:
            raise ValueError(f"Role must be one of {valid_roles}")
        return v.lower()


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


# ── Simulator ──

class SimulatorControlRequest(BaseModel):
    interval_minutes: int = Field(default=5, ge=1, le=60)


class SimulatorStatusResponse(BaseModel):
    running: bool
    interval_minutes: Optional[int] = None
    last_run: Optional[str] = None
    total_runs: int = 0


class MLDetectRequest(BaseModel):
    time_window_hours: int = Field(default=24, ge=1, le=168)
    bo_filter: Optional[str] = Field(
        default=None,
        description="Filter rows where source_bo equals this value (e.g. BO1)",
    )
    include_rule_alerts: bool = True
    max_rows: int = Field(default=5000, ge=100, le=100000)


class IsolationForestResult(BaseModel):
    n_samples: int
    n_outliers: int
    outlier_ratio: float
    feature_columns: List[str]


class MLDetectResponse(BaseModel):
    success: bool
    timestamp: str
    time_window_hours: int
    isolation_forest: Optional[IsolationForestResult] = None
    anomaly_records: List[Dict[str, Any]] = Field(default_factory=list)
    rule_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    merged_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    message: Optional[str] = None


class MLPredictRequest(BaseModel):
    target: str = Field(default="latency_ms", description="Column to predict")
    time_window_hours: int = Field(default=48, ge=1, le=336)
    bo_filter: Optional[str] = None
    max_train_rows: int = Field(default=20000, ge=500, le=200000)
    retrain: bool = Field(default=False, description="Force refit on this request")


class MLPredictResponse(BaseModel):
    success: bool
    timestamp: str
    target: str
    model: str
    metrics: Dict[str, Optional[float]] = Field(default_factory=dict)
    predictions: List[Dict[str, Any]] = Field(default_factory=list)
    message: Optional[str] = None


class MLOrchestrateRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=2000)
    bo_filter: Optional[str] = Field(
        default=None,
        description="Filter rows where source_bo equals this value (e.g. BO1)",
    )
    detect_time_window_hours: int = Field(default=24, ge=1, le=168)
    predict_time_window_hours: int = Field(default=72, ge=1, le=336)
    include_rule_alerts: bool = True
    max_detect_rows: int = Field(default=8000, ge=100, le=100000)
    max_train_rows: int = Field(default=25000, ge=500, le=200000)
    retrain: bool = Field(default=True, description="Force model refit for prediction")
    confirm: bool = Field(
        default=False,
        description="When true, execute proposed action; otherwise return only routing proposal",
    )

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, v: str) -> str:
        return v.strip()


class MLOrchestrateResponse(BaseModel):
    success: bool
    timestamp: str
    action: Optional[str] = Field(default=None, description="Selected action: detect or predict")
    intent: str = Field(description="Intent inferred from prompt")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    executed: bool = False
    needs_confirmation: bool = False
    message: Optional[str] = None
    detect_result: Optional[MLDetectResponse] = None
    predict_result: Optional[MLPredictResponse] = None


class MLModelsStatusResponse(BaseModel):
    timestamp: str
    diagnostic_joblib: Dict[str, bool] = Field(default_factory=dict)
    runtime: Dict[str, Any] = Field(default_factory=dict)
    data_manager: Dict[str, Any] = Field(default_factory=dict)


class DataRefreshResponse(BaseModel):
    success: bool
    timestamp: str
    rows: int
    source_path: str
    mtime: Optional[str] = None


class ExternalDatasetRecord(BaseModel):
    title: str
    source_portal: str
    url: str
    description: Optional[str] = None
    license: Optional[str] = None
    telecom_tags: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    fetched_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class EnrichmentCatalogResponse(BaseModel):
    success: bool
    total: int
    offset: int
    limit: int
    records: List[ExternalDatasetRecord] = Field(default_factory=list)


class EnrichmentScrapeResponse(BaseModel):
    success: bool
    timestamp: str
    added: int
    total_in_catalog: int
    errors: List[str] = Field(default_factory=list)
