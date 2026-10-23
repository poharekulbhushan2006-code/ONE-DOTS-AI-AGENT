"""
ONE: Always-On Autonomous AI Agent System
Human-in-the-Loop (HIL) Escalation Gate & Multi-Channel Dispatcher
"""

import httpx
from datetime import datetime
from typing import Any, Dict, Optional

from config.settings import settings
from memory.state_store import state_store
from core.models import DecisionRequest, DecisionStatus, RiskLevel


class ApprovalGate:
    """
    Manages human approvals, decision routing, and notification broadcasts.
    """

    @staticmethod
    async def notify_escalation(request: DecisionRequest):
        """
        Dispatches notification across configured channels (Webhooks, Slack, Telegram).
        """
        message_text = (
            f"🚨 *[ONE AGENT APPROVAL REQUIRED]*\n"
            f"Agent: `{request.agent_id}`\n"
            f"Action: `{request.action_type}` ({request.tool_name})\n"
            f"Risk Level: *{request.risk_level.value.upper()}*\n"
            f"Details: {request.description}\n"
            f"Decision ID: `{request.id}`\n"
            f"Approve via Dashboard or API: POST /api/agents/{request.agent_id}/decisions/{request.id}/resolve"
        )

        # 1. Slack Webhook
        if settings.SLACK_WEBHOOK_URL:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        settings.SLACK_WEBHOOK_URL,
                        json={"text": message_text},
                        timeout=5.0
                    )
            except Exception as e:
                print(f"[ApprovalGate] Slack notification failed: {e}")

        # 2. Generic Webhook
        if settings.WEBHOOK_ALERT_URL:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        settings.WEBHOOK_ALERT_URL,
                        json={
                            "event": "agent_escalation",
                            "decision_id": request.id,
                            "agent_id": request.agent_id,
                            "risk_level": request.risk_level.value,
                            "description": request.description,
                        },
                        timeout=5.0
                    )
            except Exception as e:
                print(f"[ApprovalGate] Alert webhook failed: {e}")

    @staticmethod
    def approve(decision_id: str, human_notes: Optional[str] = None) -> Optional[DecisionRequest]:
        return state_store.resolve_decision(decision_id, DecisionStatus.APPROVED, human_notes)

    @staticmethod
    def reject(decision_id: str, human_notes: Optional[str] = None) -> Optional[DecisionRequest]:
        return state_store.resolve_decision(decision_id, DecisionStatus.REJECTED, human_notes)

    @staticmethod
    def should_escalate(tool_name: str, payload: Dict[str, Any], risk_level: RiskLevel) -> bool:
        """
        Determines whether an action must be paused for human review.
        """
        if risk_level == RiskLevel.HIGH:
            return True

        # Check for dangerous bash commands
        if tool_name == "sandbox_run_bash":
            cmd = str(payload.get("command", "")).lower()
            dangerous_tokens = ["rm -rf", "drop", "truncate", "format", "curl | bash", "shutdown"]
            if any(t in cmd for t in dangerous_tokens):
                return True

        return False


approval_gate = ApprovalGate()
