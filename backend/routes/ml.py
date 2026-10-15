"""ML detection, prediction, and prompt orchestration routes."""

from datetime import datetime
from typing import Any, Dict, Optional
import re
import json  # <-- AJOUTE CA
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends

from core.config import ENABLE_DB_ALERTS
from core.schemas import (
    IsolationForestResult,
    MLDetectRequest,
    MLDetectResponse,
    MLPredictRequest,
    MLPredictResponse,
    MLModelsStatusResponse,
    MLOrchestrateRequest,
    MLOrchestrateResponse,
)
from routes.deps import get_agent2, get_orchestrator, get_current_user_optional

router = APIRouter(prefix="/api", tags=["ml"])

PREDICT_PATTERNS = [
    r"\bpredict(?:ion|ive)?\b",
    r"\bforecast(?:ing)?\b",
    r"\bpr(?:e|é)di(?:re|rai|ras|ra|rons|rez|ront|s|t|sons|sez|sent|ct|ction)\b",
    r"\bpr(?:e|é)vi(?:sion|oir|s|t|sons|sez|sent|endra|endront)\b",
    r"\bnext\b",
    r"\btomorrow\b",
    r"\bprochain(?:e|es)?\b",
    r"\b(latence|sla).*(futur|prochain)\b",
    r"\b(latency|sla).*(future|next)\b",
]

DETECT_PATTERNS = [
    r"\bdetect(?:ion)?\b",
    r"\bd(?:e|é)tect(?:er|ion|e|es|ons|ez|ent)?\b",
    r"\banomal(?:y|ies|ie|ies)\b",
    r"\bincident(?:s)?\b",
    r"\balert(?:s|e|es)?\b",
    r"\bd[ée]tection\b",
    r"\balerte(?:s)?\b",
    r"\boutlier(?:s)?\b",
]


def _infer_ml_action(prompt: str) -> Dict[str, Any]:
    text = (prompt or "").strip().lower()
    if not text:
        return {"action": None, "intent": "empty_prompt", "confidence": 0.0}

    for pattern in PREDICT_PATTERNS:
        if re.search(pattern, text):
            return {"action": "predict", "intent": "predict_keyword", "confidence": 0.9}

    for pattern in DETECT_PATTERNS:
        if re.search(pattern, text):
            return {"action": "detect", "intent": "detect_keyword", "confidence": 0.9}

    return {"action": None, "intent": "ambiguous", "confidence": 0.0}


@router.post("/ml/detect", response_model=MLDetectResponse)
async def ml_detect(request: MLDetectRequest, _user=Depends(get_current_user_optional)):
    orchestrator = get_orchestrator()
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    raw = orchestrator.run_detection(
        time_window_hours=request.time_window_hours,
        bo_filter=request.bo_filter,
        include_rule_alerts=request.include_rule_alerts,
        max_rows=request.max_rows,
    )
    ts = datetime.now().isoformat()
    if not raw.get("success"):
        return MLDetectResponse(
            success=False,
            timestamp=ts,
            time_window_hours=request.time_window_hours,
            message=raw.get("message", "No data"),
        )

    meta = raw.get("isolation_forest") or {}
    iso = None
    if meta and "n_samples" in meta:
        iso = IsolationForestResult(
            n_samples=int(meta["n_samples"]),
            n_outliers=int(meta.get("n_outliers", 0)),
            outlier_ratio=float(meta.get("outlier_ratio", 0.0)),
            feature_columns=list(meta.get("feature_columns", [])),
        )

    merged = raw.get("merged_alerts") or []
    if ENABLE_DB_ALERTS and merged:
        from database import SessionLocal

        db = SessionLocal()
        try:
            orchestrator.alerts.persist_alerts(db, merged)
        finally:
            db.close()

    return MLDetectResponse(
        success=True,
        timestamp=ts,
        time_window_hours=request.time_window_hours,
        isolation_forest=iso,
        anomaly_records=raw.get("anomaly_records") or [],
        rule_alerts=raw.get("rule_alerts") or [],
        merged_alerts=merged,
    )


@router.post("/ml/predict", response_model=MLPredictResponse)
async def ml_predict(request: MLPredictRequest, _user=Depends(get_current_user_optional)):
    orchestrator = get_orchestrator()
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    raw = orchestrator.run_predict(
        target=request.target,
        time_window_hours=request.time_window_hours,
        bo_filter=request.bo_filter,
        max_train_rows=request.max_train_rows,
        retrain=request.retrain,
    )
    ts = datetime.now().isoformat()
    if not raw.get("success"):
        return MLPredictResponse(
            success=False,
            timestamp=ts,
            target=request.target,
            model="RandomForestRegressor",
            message=raw.get("message", "Prediction failed"),
        )
    return MLPredictResponse(
        success=True,
        timestamp=ts,
        target=request.target,
        model=raw.get("model", "RandomForestRegressor"),
        metrics=raw.get("metrics") or {},
        predictions=raw.get("predictions") or [],
    )


@router.post("/ml/orchestrate", response_model=MLOrchestrateResponse)
async def ml_orchestrate(request: MLOrchestrateRequest, _user=Depends(get_current_user_optional)):
    orchestrator = get_orchestrator()
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    route = _infer_ml_action(request.prompt)
    action: Optional[str] = route["action"]
    ts = datetime.now().isoformat()

    if action is None:
        return MLOrchestrateResponse(
            success=False,
            timestamp=ts,
            action=None,
            intent=route["intent"],
            confidence=route["confidence"],
            executed=False,
            needs_confirmation=True,
            message="Je n’ai pas compris, veux-tu Detection ou Prediction ?",
        )

    if action == "predict":
        raw = orchestrator.run_predict(
            target="latency_ms",
            time_window_hours=request.predict_time_window_hours,
            bo_filter=request.bo_filter,
            max_train_rows=request.max_train_rows,
            retrain=request.retrain,
        )
        predict_payload = MLPredictResponse(
            success=bool(raw.get("success")),
            timestamp=ts,
            target="latency_ms",
            model=raw.get("model", "RandomForestRegressor"),
            metrics=raw.get("metrics") or {},
            predictions=raw.get("predictions") or [],
            message=raw.get("message"),
        )
        return MLOrchestrateResponse(
            success=predict_payload.success,
            timestamp=ts,
            action="predict",
            intent=route["intent"],
            confidence=route["confidence"],
            executed=True,
            needs_confirmation=False,
            message=predict_payload.message,
            predict_result=predict_payload,
        )

    raw = orchestrator.run_detection(
        time_window_hours=request.detect_time_window_hours,
        bo_filter=request.bo_filter,
        include_rule_alerts=request.include_rule_alerts,
        max_rows=request.max_detect_rows,
    )
    iso_raw = raw.get("isolation_forest") or {}
    iso = None
    if iso_raw and "n_samples" in iso_raw:
        iso = IsolationForestResult(
            n_samples=int(iso_raw["n_samples"]),
            n_outliers=int(iso_raw.get("n_outliers", 0)),
            outlier_ratio=float(iso_raw.get("outlier_ratio", 0.0)),
            feature_columns=list(iso_raw.get("feature_columns", [])),
        )
    detect_payload = MLDetectResponse(
        success=bool(raw.get("success")),
        timestamp=ts,
        time_window_hours=request.detect_time_window_hours,
        isolation_forest=iso,
        anomaly_records=raw.get("anomaly_records") or [],
        rule_alerts=raw.get("rule_alerts") or [],
        merged_alerts=raw.get("merged_alerts") or [],
        message=raw.get("message"),
    )
    return MLOrchestrateResponse(
        success=detect_payload.success,
        timestamp=ts,
        action="detect",
        intent=route["intent"],
        confidence=route["confidence"],
        executed=True,
        needs_confirmation=False,
        message=detect_payload.message,
        detect_result=detect_payload,
    )


@router.get("/ml/drift")
async def ml_drift_check(
    time_window_hours: int = 24,
    bo_filter: str = None,
    _user=Depends(get_current_user_optional),
):
    """Check data drift against training reference distribution."""
    orchestrator = get_orchestrator()
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    return orchestrator.check_drift(time_window_hours=time_window_hours, bo_filter=bo_filter)


@router.get("/ml/models/status", response_model=MLModelsStatusResponse)
async def ml_models_status(_user=Depends(get_current_user_optional)):
    agent2 = get_agent2()
    orchestrator = get_orchestrator()
    ts = datetime.now().isoformat()

    diag = {k: False for k in ["anomaly_detector", "sla_predictor", "zone_scorer"]}
    if agent2:
        for k in diag:
            diag[k] = k in agent2.models

    runtime: Dict[str, Any] = {}
    if orchestrator:
        runtime = orchestrator.prediction.status()

    dm: Dict[str, Any] = {}
    if orchestrator:
        p = orchestrator.data_manager.resolved_path()
        dm = {
            "path": str(p),
            "exists": p.exists(),
            "last_refresh": orchestrator.data_manager.get_last_refresh(),
            "enrichment_count": orchestrator.data_manager.enrichment_catalog_count(),
        }

    return MLModelsStatusResponse(
        timestamp=ts,
        diagnostic_joblib=diag,
        runtime=runtime,
        data_manager=dm,
    )
@router.get("/ml/metrics")
async def get_training_metrics(_user=Depends(get_current_user_optional)):
    """
    Récupère les métriques des vrais modèles (ROC-AUC, Hyperparamètres)
    générées par le script train_real_models.py
    """
    metrics_path = Path(__file__).resolve().parent.parent / "models" / "metrics.json"
    
    if not metrics_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="Fichier metrics.json introuvable. Assurez-vous d'avoir lancé train_real_models.py"
        )
    
    with open(metrics_path, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
        
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "models": metrics
    }