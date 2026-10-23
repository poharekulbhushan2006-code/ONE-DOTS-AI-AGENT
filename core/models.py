"""
ONE: Always-On Autonomous AI Agent System
Data Models & State Definitions
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class LifecycleStage(str, Enum):
    RESEARCH = "research"    # Gathering data, browsing, scraping, reading
    ANALYZE = "analyze"      # Correlating, anomaly detection, reasoning
    BUILD = "build"          # Writing code, updating DBs, generating outputs
    MONITOR = "monitor"      # Checking health, tracking metrics, inspecting changes
    REPORT = "report"        # Formulating user deliverables, summaries, digests
    ADAPT = "adapt"          # Self-healing, reflecting on errors, refining strategy


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    SLEEPING = "sleeping"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class RiskLevel(str, Enum):
    LOW = "low"          # Read-only, web search, scratchpad notes
    MEDIUM = "medium"    # Code execution in sandbox, file writing in sandbox
    HIGH = "high"        # External emails, public posting, destructive modifications


class DecisionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DecisionRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_id: str
    action_type: str
    tool_name: str
    description: str
    proposed_payload: Dict[str, Any]
    risk_level: RiskLevel = RiskLevel.MEDIUM
    status: DecisionStatus = DecisionStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: Optional[datetime] = None
    human_notes: Optional[str] = None


class TaskStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    stage: LifecycleStage
    action: str
    tool: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    output: Optional[Any] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReportItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_id: str
    title: str
    summary: str
    content: str
    format: str = "markdown"  # markdown, json, html
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OneAgent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    responsibility: str  # Enduring mission / goal
    status: AgentStatus = AgentStatus.IDLE
    current_stage: LifecycleStage = LifecycleStage.RESEARCH
    
    # Scheduling & Cadence
    schedule_interval_seconds: int = 180  # Default: tick every 3 minutes
    last_tick_at: Optional[datetime] = None
    next_tick_at: Optional[datetime] = None
    
    # State tracking & counters
    total_ticks: int = 0
    successful_cycles: int = 0
    pending_approval_id: Optional[str] = None
    
    # Metadata & Config
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_id: str
    sender: str  # "user", "agent", "system"
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
