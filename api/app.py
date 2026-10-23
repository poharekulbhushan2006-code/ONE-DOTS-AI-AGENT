"""
DOTS: Always-On Autonomous AI Agent System
Dedicated Standalone FastAPI Management API & Webhook Ingress
"""

import os
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
    ChatMessage,
)
from memory.state_store import state_store
from memory.semantic_memory import semantic_memory
from core.orchestrator import AgentOrchestrator
from core.heartbeat import heartbeat
from hil.approval_gate import approval_gate
from core.conversation import AgentConversationEngine
from sandbox.executor import SandboxEnvironment


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch continuous heartbeat
    await heartbeat.start()
    print("[DOTS] Autonomous Agent Heartbeat Scheduler started.")
    yield
    # Shutdown: Stop heartbeat cleanly
    await heartbeat.stop()
    print("[DOTS] Autonomous Agent Heartbeat Scheduler stopped.")


app = FastAPI(
    title="ONE DOTS",
    version=settings.VERSION,
    description="Always-On Autonomous AI Agent Platform powered by Google Gemini and Dedicated Cloud Computers",
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


class UserChatRequest(BaseModel):
    message: str


class ExecuteCodeRequest(BaseModel):
    code: str
    language: str = "python"  # python or bash
    stdin: Optional[str] = None


class WriteFileRequest(BaseModel):
    path: str
    content: str


class ToggleIntegrationRequest(BaseModel):
    integration_id: str
    enabled: bool


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


@app.delete("/api/agents/{agent_id}")
def delete_agent(agent_id: str):
    agent = state_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    state_store.delete_agent(agent_id)
    semantic_memory.clear_agent(agent_id)
    return {"success": True, "message": f"Agent '{agent_id}' deleted successfully"}


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


# ------------------ CONVERSATION & CATCH-UP BRIEFING ------------------

@app.get("/api/agents/{agent_id}/briefing")
def get_agent_briefing(agent_id: str):
    agent = state_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    engine = AgentConversationEngine(agent_id)
    return engine.get_catchup_briefing()


@app.get("/api/agents/{agent_id}/chat", response_model=List[ChatMessage])
def get_chat_history(agent_id: str, limit: int = 50):
    return state_store.get_chat_history(agent_id, limit=limit)


@app.post("/api/agents/{agent_id}/chat", response_model=ChatMessage)
async def send_chat_message(agent_id: str, req: UserChatRequest):
    agent = state_store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    engine = AgentConversationEngine(agent_id)
    response_msg = await engine.chat(req.message)
    return response_msg


# ------------------ CLOUD COMPUTER FILES & SANDBOX ------------------

@app.get("/api/agents/{agent_id}/files")
def list_agent_sandbox_files(agent_id: str):
    sandbox = SandboxEnvironment(agent_id)
    files = sandbox.list_files()
    return {"files": files}


@app.get("/api/agents/{agent_id}/files/content")
def get_agent_sandbox_file_content(agent_id: str, path: str):
    sandbox = SandboxEnvironment(agent_id)
    try:
        content = sandbox.read_file(path)
        return {"path": path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/agents/{agent_id}/execute")
def execute_in_agent_sandbox(agent_id: str, req: ExecuteCodeRequest):
    sandbox = SandboxEnvironment(agent_id)
    if req.language == "bash":
        result = sandbox.run_command(req.code, stdin=req.stdin)
    else:
        result = sandbox.run_python(req.code, stdin=req.stdin)
    return result


@app.post("/api/agents/{agent_id}/files/write")
def write_agent_sandbox_file(agent_id: str, req: WriteFileRequest):
    sandbox = SandboxEnvironment(agent_id)
    msg = sandbox.write_file(req.path, req.content)
    return {"success": True, "message": msg, "path": req.path}


@app.delete("/api/agents/{agent_id}/files")
def delete_agent_sandbox_file(agent_id: str, path: str):
    sandbox = SandboxEnvironment(agent_id)
    deleted = sandbox.delete_file(path)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")
    return {"success": True, "message": f"File '{path}' deleted from sandbox"}


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


# ------------------ COMMERCIAL FLEET TELEMETRY & INTEGRATIONS ------------------

# In-memory store for active enterprise integrations
_INTEGRATIONS_CONFIG = {
    "slack": {"name": "Slack", "icon": "💬", "category": "Team Chat", "status": "connected", "details": "Monitoring #product and #bugs channels"},
    "teams": {"name": "Microsoft Teams & Agent 365", "icon": "💼", "category": "Enterprise Chat", "status": "connected", "details": "Active governance & compliance policy"},
    "github": {"name": "GitHub", "icon": "🐙", "category": "Code Review", "status": "connected", "details": "Autonomous PR creation & CI status tracking"},
    "google": {"name": "Google Workspace & Gmail", "icon": "📧", "category": "Productivity", "status": "standby", "details": "Draft launch emails & sync calendars"},
    "notion": {"name": "Notion & Linear", "icon": "📑", "category": "Project Tracking", "status": "connected", "details": "Bi-directional task & roadmap updates"},
    "webhooks": {"name": "Custom Enterprise Webhooks", "icon": "🔗", "category": "Ingress / Egress", "status": "connected", "details": "HTTP event stream & webhook automation"},
}


@app.get("/api/integrations")
def get_integrations():
    return {"integrations": _INTEGRATIONS_CONFIG}


@app.post("/api/integrations/toggle")
def toggle_integration(req: ToggleIntegrationRequest):
    if req.integration_id not in _INTEGRATIONS_CONFIG:
        raise HTTPException(status_code=404, detail="Integration not found")
    _INTEGRATIONS_CONFIG[req.integration_id]["status"] = "connected" if req.enabled else "disconnected"
    return {"success": True, "integration": _INTEGRATIONS_CONFIG[req.integration_id]}


@app.get("/api/system/stats")
def get_system_stats():
    import psutil
    agents = state_store.list_agents()
    pending = state_store.list_pending_decisions()
    total_ticks = sum(a.total_ticks for a in agents)
    
    cpu_percent = psutil.cpu_percent() if hasattr(psutil, "cpu_percent") else 12.5
    mem = psutil.virtual_memory() if hasattr(psutil, "virtual_memory") else None
    mem_used_mb = round(mem.used / (1024 * 1024), 1) if mem else 420.0
    mem_total_mb = round(mem.total / (1024 * 1024), 1) if mem else 16384.0

    return {
        "status": "healthy",
        "platform": "ONE DOTS Commercial Platform",
        "model": settings.DEFAULT_MODEL,
        "llm_provider": settings.LLM_PROVIDER,
        "subscription_tier": "Business Premium",
        "monthly_cycle_allowance": 25000,
        "monthly_cycles_used": total_ticks,
        "active_dots": len(agents),
        "total_ticks": total_ticks,
        "pending_decisions": len(pending),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_used_mb": mem_used_mb,
            "memory_total_mb": mem_total_mb,
        }
    }


# ------------------ STATIC MOUNTS & LEARN DOCS ------------------

web_dir = settings.BASE_DIR / "web"
web_dir.mkdir(parents=True, exist_ok=True)

from fastapi.responses import FileResponse

@app.get("/learn", include_in_schema=False)
@app.get("/docs-portal", include_in_schema=False)
def serve_learn_docs():
    docs_file = web_dir / "docs.html"
    if docs_file.exists():
        return FileResponse(str(docs_file))
    return {"message": "Documentation portal initializing..."}

# Screenshots directory
if settings.SCREENSHOTS_DIR.exists():
    app.mount("/screenshots", StaticFiles(directory=str(settings.SCREENSHOTS_DIR)), name="screenshots")

# Dashboard UI directory (OpenAI Dot-style workstation dashboard)
app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

