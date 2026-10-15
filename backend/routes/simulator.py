"""Agent Simulator: periodic autonomous diagnostic runs."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from core.schemas import SimulatorControlRequest, SimulatorStatusResponse
from routes.deps import get_current_user_optional

router = APIRouter(prefix="/api/simulator", tags=["simulator"])

# Module-level state for the simulator
_simulator_state = {
    "running": False,
    "interval_minutes": 5,
    "last_run": None,
    "total_runs": 0,
    "scheduler": None,
}


def _run_simulation_cycle():
    """Execute one simulation cycle: diagnostic scan + alert generation."""
    from routes.deps import get_agent2, get_orchestrator

    agent2 = get_agent2()
    orchestrator = get_orchestrator()
    if not agent2:
        return

    try:
        df = agent2.load_data()
        if df is not None:
            alerts = agent2.analyze_batch(df, time_window_hours=1)
            _simulator_state["last_run"] = datetime.now().isoformat()
            _simulator_state["total_runs"] += 1
            print(f"[Simulator] Cycle #{_simulator_state['total_runs']}: {len(alerts)} alerts")

            if orchestrator and alerts:
                from core.config import ENABLE_DB_ALERTS
                if ENABLE_DB_ALERTS:
                    from database import SessionLocal
                    db = SessionLocal()
                    try:
                        orchestrator.alerts.persist_alerts(db, alerts)
                    finally:
                        db.close()
    except Exception as e:
        print(f"[Simulator] Error: {e}")


@router.post("/start", response_model=SimulatorStatusResponse)
async def start_simulator(
    request: SimulatorControlRequest,
    _user=Depends(get_current_user_optional),
):
    if _simulator_state["running"]:
        raise HTTPException(status_code=400, detail="Simulator already running")

    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _run_simulation_cycle,
        trigger=IntervalTrigger(minutes=request.interval_minutes),
        id="simulator_cycle",
        name="Agent Simulator Cycle",
        replace_existing=True,
    )
    scheduler.start()

    _simulator_state["scheduler"] = scheduler
    _simulator_state["running"] = True
    _simulator_state["interval_minutes"] = request.interval_minutes

    # Run first cycle immediately
    _run_simulation_cycle()

    print(f"[Simulator] Started with {request.interval_minutes}min interval")

    return SimulatorStatusResponse(
        running=True,
        interval_minutes=request.interval_minutes,
        last_run=_simulator_state["last_run"],
        total_runs=_simulator_state["total_runs"],
    )


@router.post("/stop", response_model=SimulatorStatusResponse)
async def stop_simulator(_user=Depends(get_current_user_optional)):
    if not _simulator_state["running"]:
        raise HTTPException(status_code=400, detail="Simulator not running")

    scheduler = _simulator_state.get("scheduler")
    if scheduler:
        scheduler.shutdown(wait=False)

    _simulator_state["running"] = False
    _simulator_state["scheduler"] = None
    print("[Simulator] Stopped")

    return SimulatorStatusResponse(
        running=False,
        interval_minutes=_simulator_state["interval_minutes"],
        last_run=_simulator_state["last_run"],
        total_runs=_simulator_state["total_runs"],
    )


@router.get("/status", response_model=SimulatorStatusResponse)
async def simulator_status(_user=Depends(get_current_user_optional)):
    return SimulatorStatusResponse(
        running=_simulator_state["running"],
        interval_minutes=_simulator_state["interval_minutes"],
        last_run=_simulator_state["last_run"],
        total_runs=_simulator_state["total_runs"],
    )
