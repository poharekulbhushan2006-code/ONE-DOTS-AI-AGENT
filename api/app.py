"""
ONE: Always-On Autonomous AI Agent System
FastAPI Application, Management API & Webhook Ingress
"""

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.settings import settings
from core.models import (
    OneAgent,
    AgentStatus,
    LifecycleStage,
    DecisionRequest,
    DecisionStatus,
    TaskStep,
    ReportItem,
)
from memory.state_store import state_store
from core.orchestrator import AgentOrchestrator
from core.heartbeat import heartbeat
from hil.approval_gate import approval_gate


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch continuous heartbeat
    await heartbeat.start()
    yield
    # Shutdown: Stop heartbeat cleanly
    await heartbeat.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.TAGLINE,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Models
class CreateAgentRequest(BaseModel):
    name: str
    responsibility: str
    schedule_interval_seconds: int = 180
    context: Optional[Dict[str, Any]] = None


class ResolveDecisionRequest(BaseModel):
    notes: Optional[str] = None


# ------------------ AGENT ENDPOINTS ------------------

@app.post("/api/agents", response_model=OneAgent)
def create_agent(req: CreateAgentRequest):
    agent = OneAgent(
        name=req.name,
        responsibility=req.responsibility,
        schedule_interval_seconds=req.schedule_interval_seconds,
        context=req.context or {},
        status=AgentStatus.IDLE,
    )
    saved = state_store.save_agent(agent)
    return saved


@app.get("/api/agents", response_model=List[OneAgent])
def list_agents():
    return state_store.list_agents()


@app.get("/api/agents/{agent_id}", response_model=OneAgent)
def get_agent(agent_id: str):
    agent = state_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.post("/api/agents/{agent_id}/tick")
async def trigger_agent_tick(agent_id: str):
    agent = state_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    orchestrator = AgentOrchestrator(agent_id)
    result = await orchestrator.execute_tick()
    return result


@app.post("/api/agents/{agent_id}/pause")
def pause_agent(agent_id: str):
    agent = state_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = AgentStatus.PAUSED
    state_store.save_agent(agent)
    return {"success": True, "status": agent.status.value}


@app.post("/api/agents/{agent_id}/resume")
def resume_agent(agent_id: str):
    agent = state_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = AgentStatus.IDLE
    state_store.save_agent(agent)
    return {"success": True, "status": agent.status.value}


@app.get("/api/agents/{agent_id}/steps", response_model=List[TaskStep])
def get_agent_steps(agent_id: str, limit: int = 50):
    return state_store.get_agent_steps(agent_id, limit=limit)


@app.get("/api/agents/{agent_id}/reports", response_model=List[ReportItem])
def get_agent_reports(agent_id: str, limit: int = 20):
    return state_store.get_agent_reports(agent_id, limit=limit)


# ------------------ HUMAN ESCALATIONS ------------------

@app.get("/api/decisions/pending", response_model=List[DecisionRequest])
def list_pending_decisions():
    return state_store.list_pending_decisions()


@app.post("/api/decisions/{decision_id}/approve")
def approve_decision(decision_id: str, req: ResolveDecisionRequest):
    resolved = approval_gate.approve(decision_id, human_notes=req.notes)
    if not resolved:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {"success": True, "decision": resolved}


@app.post("/api/decisions/{decision_id}/reject")
def reject_decision(decision_id: str, req: ResolveDecisionRequest):
    resolved = approval_gate.reject(decision_id, human_notes=req.notes)
    if not resolved:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {"success": True, "decision": resolved}


# ------------------ STATIC MOUNTS ------------------

# Screenshots directory
if settings.SCREENSHOTS_DIR.exists():
    app.mount("/screenshots", StaticFiles(directory=str(settings.SCREENSHOTS_DIR)), name="screenshots")

# Dashboard UI directory
web_dir = settings.BASE_DIR / "web"
web_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
