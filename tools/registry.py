"""
ONE: Always-On Autonomous AI Agent System
Tool Registry & Execution Subsystem
"""

import json
from typing import Any, Callable, Dict, List, Optional
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from config.settings import settings
from sandbox.executor import SandboxEnvironment
from browser.controller import AgentBrowser
from memory.semantic_memory import semantic_memory
from memory.state_store import state_store
from core.models import DecisionRequest, RiskLevel, DecisionStatus, ReportItem


class ToolRegistry:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.sandbox = SandboxEnvironment(agent_id)
        self.browser = AgentBrowser(agent_id)

    # 1. Search Tool
    def web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search the live web for facts, competitor info, and recent updates."""
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title"),
                        "href": r.get("href"),
                        "body": r.get("body"),
                    })
            return {"success": True, "query": query, "results": results}
        except Exception as e:
            return {"success": False, "query": query, "error": str(e), "results": []}

    # 2. Browser Tool
    async def browser_inspect(self, url: str, take_screenshot: bool = True) -> Dict[str, Any]:
        """Visit a web page, extract readable text, retrieve links, and take a screenshot."""
        return await self.browser.navigate_and_extract(url, take_screenshot=take_screenshot)

    # 3. Sandbox Python Runner
    def sandbox_run_python(self, code: str) -> Dict[str, Any]:
        """Run Python code inside the dedicated sandbox workspace."""
        return self.sandbox.run_python(code)

    # 4. Sandbox Shell Command Runner
    def sandbox_run_bash(self, command: str) -> Dict[str, Any]:
        """Execute a shell command inside the dedicated sandbox workspace."""
        return self.sandbox.run_command(command)

    # 5. File Operations
    def file_write(self, filename: str, content: str) -> Dict[str, Any]:
        """Create or update a file in the agent sandbox."""
        try:
            msg = self.sandbox.write_file(filename, content)
            return {"success": True, "message": msg, "filename": filename}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def file_read(self, filename: str) -> Dict[str, Any]:
        """Read a file from the agent sandbox."""
        try:
            content = self.sandbox.read_file(filename)
            return {"success": True, "filename": filename, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def file_list(self) -> Dict[str, Any]:
        """List all files in the agent sandbox."""
        try:
            files = self.sandbox.list_files()
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 6. Memory Tools
    def memory_remember(self, content: str, category: str = "finding", source: Optional[str] = None) -> Dict[str, Any]:
        """Store knowledge in long-term episodic memory for future runs."""
        mid = semantic_memory.remember(self.agent_id, content, category=category, source=source)
        return {"success": True, "memory_id": mid, "message": "Remembered for future cycles"}

    def memory_recall(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Recall relevant insights and previous findings."""
        memories = semantic_memory.recall(self.agent_id, query, limit=limit)
        return {"success": True, "query": query, "memories": memories}

    # 7. Escalation Tool
    def request_human_approval(
        self,
        action_type: str,
        tool_name: str,
        description: str,
        payload: Dict[str, Any],
        risk_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        Escalates high-stakes decisions or ambiguous checkpoints to the human supervisor.
        """
        level = RiskLevel.MEDIUM
        if risk_level.lower() == "high":
            level = RiskLevel.HIGH
        elif risk_level.lower() == "low":
            level = RiskLevel.LOW

        req = DecisionRequest(
            agent_id=self.agent_id,
            action_type=action_type,
            tool_name=tool_name,
            description=description,
            proposed_payload=payload,
            risk_level=level,
            status=DecisionStatus.PENDING,
        )
        saved = state_store.create_decision_request(req)
        return {
            "success": True,
            "escalated": True,
            "decision_id": saved.id,
            "message": f"Paused action: Waiting for human approval on decision '{saved.id}'. Description: {description}",
        }

    # 8. Report Publishing
    def publish_report(self, title: str, summary: str, content: str, format: str = "markdown") -> Dict[str, Any]:
        """Deliver an executive status report or deliverable."""
        report = ReportItem(
            agent_id=self.agent_id,
            title=title,
            summary=summary,
            content=content,
            format=format,
        )
        saved = state_store.save_report(report)
        
        # Also write report file to disk for easy viewing
        report_file = settings.REPORTS_DIR / f"{self.agent_id}_{saved.id}.md"
        report_file.write_text(f"# {title}\n\n**Summary**: {summary}\n\n---\n\n{content}", encoding="utf-8")

        return {
            "success": True,
            "report_id": saved.id,
            "file_path": str(report_file),
            "message": f"Report '{title}' successfully published and stored.",
        }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns tool schema definitions for LLM function calling."""
        return [
            {
                "name": "web_search",
                "description": "Search the web for real-time information, competitor updates, and research data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"},
                        "max_results": {"type": "integer", "description": "Max search results (default 5)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "browser_inspect",
                "description": "Navigate to a URL using a headless browser, extract clean readable text, and capture a screenshot.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The full HTTP/HTTPS URL"},
                        "take_screenshot": {"type": "boolean", "description": "Whether to save screenshot"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "sandbox_run_python",
                "description": "Execute Python code inside the dedicated sandbox workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python source code to execute"}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "sandbox_run_bash",
                "description": "Execute a shell command inside the dedicated sandbox workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "file_write",
                "description": "Write or overwrite a file in the agent sandbox directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Relative filename"},
                        "content": {"type": "string", "description": "File text content"}
                    },
                    "required": ["filename", "content"]
                }
            },
            {
                "name": "file_read",
                "description": "Read a file from the agent sandbox directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Relative filename to read"}
                    },
                    "required": ["filename"]
                }
            },
            {
                "name": "memory_remember",
                "description": "Save critical findings or rules into long-term episodic memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Insight or finding"},
                        "category": {"type": "string", "description": "Category (finding, rule, observation)"},
                        "source": {"type": "string", "description": "URL or source identifier"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "memory_recall",
                "description": "Query long-term memory for relevant past findings.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query for memory recall"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "request_human_approval",
                "description": "Pause execution and request human operator judgment before proceeding.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action_type": {"type": "string", "description": "Type of action"},
                        "tool_name": {"type": "string", "description": "Tool intended to be executed"},
                        "description": {"type": "string", "description": "Explanation of why approval is needed"},
                        "payload": {"type": "object", "description": "Proposed action payload"},
                        "risk_level": {"type": "string", "enum": ["low", "medium", "high"]}
                    },
                    "required": ["action_type", "tool_name", "description", "payload"]
                }
            },
            {
                "name": "publish_report",
                "description": "Deliver an executive summary report for human consumption.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Report title"},
                        "summary": {"type": "string", "description": "Executive summary paragraph"},
                        "content": {"type": "string", "description": "Detailed markdown report content"}
                    },
                    "required": ["title", "summary", "content"]
                }
            }
        ]
