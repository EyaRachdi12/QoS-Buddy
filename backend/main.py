"""
FastAPI Backend for QoS Buddy
Thin app factory — business logic lives in routes/ and services/.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import os

from core.config import CORS_ORIGINS, ENABLE_DB_ALERTS
from database import init_db
from routes import deps
from routes.chat import router as chat_router
from routes.diagnostics import router as diagnostics_router
from routes.ml import router as ml_router
from routes.data import router as data_router
from routes.auth import router as auth_router
from routes.simulator import router as simulator_router

app = FastAPI(
    title="QoS Buddy API",
    description="Multi-Agent Telecom Network Diagnostic System",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(diagnostics_router)
app.include_router(ml_router)
app.include_router(data_router)
app.include_router(simulator_router)


@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup."""
    print("=" * 70)
    print("INITIALIZING QoS BUDDY BACKEND v2.0")
    print("=" * 70)

    agent1 = None
    agent2 = None
    orchestrator = None

    try:
        print("\n[0/3] Initializing database tables...")
        init_db()
        print("  Database schema ready")
    except Exception as e:
        print(f"  Database init warning: {e}")

    try:
        print("\n[1/3] Initializing orchestrator + Data Manager...")
        from services.orchestrator import QoSOrchestrator

        orchestrator = QoSOrchestrator()
        orchestrator.refresh_data()
        print("  Orchestrator ready")
    except Exception as e:
        print(f"  Orchestrator initialization failed: {e}")

    try:
        print("\n[2/3] Initializing Agent 1 (Chatbot Advisor)...")
        from agent1_chatbot import TelecomAdvisorAgent

        agent1 = TelecomAdvisorAgent()
        agent1.initialize_vector_db()
        if orchestrator:
            agent1.set_insights_provider(orchestrator.live_insights_snapshot)
            orchestrator.wire_agent1(agent1)
        print("  Agent 1 ready")
    except Exception as e:
        print(f"  Agent 1 initialization failed: {e}")

    try:
        print("\n[3/3] Initializing Agent 2 (Diagnostic Worker)...")
        from agent2_diagnostic import DiagnosticAgent

        agent2 = DiagnosticAgent()
        print("  Agent 2 ready")
    except Exception as e:
        print(f"  Agent 2 initialization failed: {e}")

    # Wire globals so route modules can access agents
    deps.set_globals(agent1, agent2, orchestrator)

    print("\n" + "=" * 70)
    print("QoS BUDDY BACKEND READY")
    print(f"  DB alerts: {'enabled' if ENABLE_DB_ALERTS else 'disabled'}")
    print(f"  CORS origins: {CORS_ORIGINS}")
    print(f"  API docs: http://localhost:8000/docs")
    print("=" * 70 + "\n")


@app.get("/")
async def root():
    return {
        "service": "QoS Buddy API",
        "version": "2.0.0",
        "status": "online",
        "agents": {
            "agent1_chatbot": deps.get_agent1() is not None,
            "agent2_diagnostic": deps.get_agent2() is not None,
            "orchestrator": deps.get_orchestrator() is not None,
        },
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "agent1": "online" if deps.get_agent1() else "offline",
            "agent2": "online" if deps.get_agent2() else "offline",
            "orchestrator": "online" if deps.get_orchestrator() else "offline",
        },
    }


if __name__ == "__main__":
    print("\nStarting QoS Buddy Backend Server...")
    use_reload = os.getenv("DEV_MODE", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=use_reload,
        reload_excludes=["../data/*", "*.db", "*.sqlite"] if use_reload else None,
        log_level="info",
    )
