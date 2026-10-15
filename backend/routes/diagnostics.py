"""Agent 2: Diagnostic routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from core.schemas import AnalyzeRequest
from routes.deps import get_agent2, get_orchestrator, get_current_user_optional

router = APIRouter(prefix="/api", tags=["diagnostics"])


@router.get("/diagnostics/latest")
async def get_latest_diagnostics(limit: int = 20, _user=Depends(get_current_user_optional)):
    agent2 = get_agent2()
    if not agent2:
        raise HTTPException(status_code=503, detail="Agent 2 (Diagnostic) not available")

    try:
        alerts = agent2.get_latest_alerts(n=limit)
        return {"alerts": alerts, "count": len(alerts), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic error: {str(e)}")


@router.post("/diagnostics/analyze")
async def trigger_analysis(request: AnalyzeRequest, _user=Depends(get_current_user_optional)):
    agent2 = get_agent2()
    if not agent2:
        raise HTTPException(status_code=503, detail="Agent 2 (Diagnostic) not available")

    try:
        df = agent2.load_data()
        if df is None:
            raise HTTPException(status_code=404, detail="No data available for analysis")

        alerts = agent2.analyze_batch(df, time_window_hours=request.time_window_hours)
        return {
            "alerts": alerts,
            "count": len(alerts),
            "time_window_hours": request.time_window_hours,
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.get("/kpis/realtime")
async def get_realtime_kpis(limit: int = 100, _user=Depends(get_current_user_optional)):
    agent2 = get_agent2()
    if not agent2:
        raise HTTPException(status_code=503, detail="Agent 2 not available")

    try:
        kpis = agent2.get_realtime_kpis(limit=limit)
        return {"kpis": kpis, "count": len(kpis), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI retrieval error: {str(e)}")


@router.get("/cells/{cell_id}/status")
async def get_cell_status(cell_id: str, _user=Depends(get_current_user_optional)):
    agent2 = get_agent2()
    if not agent2:
        raise HTTPException(status_code=503, detail="Agent 2 not available")

    try:
        status = agent2.get_cell_status(cell_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/cells/list")
async def list_cells(_user=Depends(get_current_user_optional)):
    agent2 = get_agent2()
    if not agent2:
        raise HTTPException(status_code=503, detail="Agent 2 not available")

    import pandas as pd

    try:
        df = agent2.load_data()
        if df is None:
            raise HTTPException(status_code=404, detail="No data available")
        cells = df["cell_id"].unique().tolist()
        return {"cells": cells, "count": len(cells)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/summary")
async def get_summary(_user=Depends(get_current_user_optional)):
    agent2 = get_agent2()
    if not agent2:
        raise HTTPException(status_code=503, detail="Agent 2 not available")

    try:
        summary = agent2.generate_summary_report()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary error: {str(e)}")


@router.get("/bo/overview")
async def get_bo_overview(
    time_window_hours: int = 24,
    max_zones: int = 120,
    bo_filter: Optional[str] = None,
    _user=Depends(get_current_user_optional),
):
    agent2 = get_agent2()
    if not agent2:
        raise HTTPException(status_code=503, detail="Agent 2 not available")

    try:
        overview = agent2.get_bo_integrated_overview(
            time_window_hours=time_window_hours,
            max_zones=max_zones,
            bo_filter=bo_filter,
        )
        if "error" in overview:
            raise HTTPException(status_code=404, detail=overview["error"])
        return overview
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BO overview error: {str(e)}")


@router.get("/bo/dashboard-bundle")
async def get_bo_dashboard_bundle(
    bo_filter: Optional[str] = None,
    time_window_hours: int = 24,
    _user=Depends(get_current_user_optional),
):
    orchestrator = get_orchestrator()
    agent2 = get_agent2()
    if not orchestrator or not agent2:
        raise HTTPException(status_code=503, detail="Orchestrator or Agent 2 not available")

    from services.bo_data_source import bo_dashboard_bundle

    try:
        return bo_dashboard_bundle(
            orchestrator.data_manager,
            agent2,
            bo_filter,
            time_window_hours=time_window_hours,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BO bundle error: {str(e)}")
