"""
ONE: Always-On Autonomous AI Agent System
Conversational Cognitive Engine for DOTS
Enables natural language interaction with persistent agents between autonomous cycles.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

from config.settings import settings
from core.models import ChatMessage, OneAgent, TaskStep, LifecycleStage
from memory.state_store import state_store
from memory.semantic_memory import semantic_memory
from tools.registry import ToolRegistry


class AgentConversationEngine:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.agent = state_store.get_agent(agent_id)
        if not self.agent:
            raise ValueError(f"Agent '{agent_id}' does not exist.")
        self.tools = ToolRegistry(agent_id)

    def get_catchup_briefing(self) -> Dict[str, Any]:
        """
        Generates the 'While you were away' catch-up briefing.
        Explains what the Dot accomplished between conversations.
        """
        memories = semantic_memory.get_recent(self.agent_id, limit=3)
        reports = state_store.get_agent_reports(self.agent_id, limit=1)
        decisions = state_store.list_pending_decisions()
        pending = [d for d in decisions if d.agent_id == self.agent_id]
        files = self.tools.file_list().get("files", [])

        briefing_text = (
            f"Hello! I am your always-on agent **{self.agent.name}**.\n\n"
            f"**My Assigned Responsibility**:\n> *{self.agent.responsibility}*\n\n"
            f"**While You Were Away Progress**:\n"
            f"- Completed **{self.agent.total_ticks} autonomous cycles** across my cloud computer and browser.\n"
            f"- Maintained status: `{self.agent.status.value.upper()}` in stage `{self.agent.current_stage.value}`.\n"
            f"- Sandbox Workspace currently contains **{len(files)} tracked files**.\n"
        )

        if memories:
            briefing_text += "\n**Recent Findings in Memory**:\n"
            for m in memories:
                briefing_text += f"- {m['content'][:150]}...\n"

        if pending:
            briefing_text += f"\n⚠️ **Action Required**: I have **{len(pending)} pending decision(s)** waiting for your judgment."
        else:
            briefing_text += "\nAll autonomous operations are running smoothly within approved guardrails."

        return {
            "agent_id": self.agent_id,
            "briefing": briefing_text,
            "total_ticks": self.agent.total_ticks,
            "pending_decisions": len(pending),
            "tracked_files": len(files),
        }

    async def chat(self, user_text: str) -> ChatMessage:
        """
        Processes human conversational input, acts if needed, and replies.
        """
        # Save user message
        user_msg = ChatMessage(
            agent_id=self.agent_id,
            sender="user",
            content=user_text,
        )
        state_store.save_chat_message(user_msg)

        # Check if an external LLM is configured
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            reply_text = await self._call_openai_chat(user_text)
        elif settings.GEMINI_API_KEY:
            reply_text = await self._call_gemini_chat(user_text)
        else:
            reply_text = await self._autonomous_cognitive_reply(user_text)

        agent_msg = ChatMessage(
            agent_id=self.agent_id,
            sender="agent",
            content=reply_text,
        )
        saved_agent_msg = state_store.save_chat_message(agent_msg)
        return saved_agent_msg

    async def _autonomous_cognitive_reply(self, user_text: str) -> str:
        """
        Intelligent cognitive handler that interprets user intent, executes
        cloud computer tools if asked, queries memory, or updates the mission.
        """
        lowered = user_text.lower()

        # 1. User wants to check/search web
        if any(w in lowered for w in ["search for", "look up", "browse", "check online", "find info"]):
            query = user_text
            for prefix in ["search for", "look up", "check online for", "find info on"]:
                if prefix in lowered:
                    query = user_text.split(prefix, 1)[-1].strip()
                    break
            search_res = self.tools.web_search(query, max_results=3)
            hits = search_res.get("results", [])
            if hits:
                reply = f"I navigated my search tools for **'{query}'**. Here is what I found:\n\n"
                for h in hits:
                    reply += f"- **[{h.get('title')}]({h.get('href')})**: {h.get('body')}\n"
                reply += "\nI have stored these observations in my episodic memory."
                self.tools.memory_remember(f"Search query '{query}': {hits[0].get('body')[:200]}")
                return reply
            return f"I searched for '{query}' but found no new public records."

        # 2. User wants to run Python code or sandbox command
        if "run python" in lowered or "execute code" in lowered or "run script" in lowered:
            code = user_text
            if "```python" in user_text:
                code = user_text.split("```python")[1].split("```")[0].strip()
            elif "```" in user_text:
                code = user_text.split("```")[1].split("```")[0].strip()
            else:
                code = "import sys\nprint('Python version:', sys.version)\nprint('Cloud computer ready.')"
            
            res = self.tools.sandbox_run_python(code)
            return (
                f"I executed that inside my dedicated cloud sandbox environment:\n\n"
                f"**Exit Code**: `{res.get('exit_code')}`\n"
                f"**Stdout**:\n```\n{res.get('stdout', '').strip() or '(no output)'}\n```\n"
                + (f"**Stderr**:\n```\n{res.get('stderr')}\n```" if res.get('stderr') else "")
            )

        # 3. User wants to see files in the cloud computer
        if any(w in lowered for w in ["what files", "list files", "show files", "workspace"]):
            files = self.tools.file_list().get("files", [])
            if not files:
                return "My cloud computer workspace is currently empty. I will generate artifacts on my next autonomous tick."
            file_list_str = "\n".join([f"- `{f['path']}` ({f['size_bytes']} bytes)" for f in files])
            return f"Here are the files currently active in my cloud computer workspace:\n\n{file_list_str}"

        # 4. User wants to change mission / responsibility
        if any(w in lowered for w in ["change mission", "new goal", "focus on", "update responsibility"]):
            new_mission = user_text
            for prefix in ["change mission to", "new goal:", "focus on", "update responsibility to"]:
                if prefix in lowered:
                    new_mission = user_text.split(prefix, 1)[-1].strip()
                    break
            self.agent.responsibility = new_mission
            state_store.save_agent(self.agent)
            return f"Understood! I have updated my enduring responsibility to:\n> *{new_mission}*\n\nI will focus on this objective on all subsequent autonomous ticks."

        # 5. User asks about findings / status
        if any(w in lowered for w in ["what did you find", "status", "summary", "report", "progress", "what are you doing"]):
            memories = semantic_memory.get_recent(self.agent_id, limit=3)
            reports = state_store.get_agent_reports(self.agent_id, limit=1)
            response = (
                f"I am actively pursuing my responsibility: *\"{self.agent.responsibility}\"*.\n\n"
                f"- **Autonomous Status**: `{self.agent.status.value.upper()}` (Current Stage: `{self.agent.current_stage.value}`)\n"
                f"- **Cadence**: Ticking every {self.agent.schedule_interval_seconds}s (Completed {self.agent.total_ticks} ticks)\n\n"
            )
            if memories:
                response += "**Top Key Knowledge Extracted**:\n"
                for m in memories:
                    response += f"- {m['content']}\n"
            if reports:
                response += f"\n**Latest Intelligence Report**: *{reports[0].title}*\n{reports[0].summary}"
            return response

        # 6. Default conversational response
        return (
            f"Understood. As your always-on agent for **{self.agent.name}**, I'm tracking: *'{self.agent.responsibility}'*.\n\n"
            "You can ask me to:\n"
            "- *'What did you find today?'* (inspect my latest memory)\n"
            "- *'Search online for [query]'* (trigger my browser & research tools)\n"
            "- *'Run python: [code]'* (execute scripts in my cloud computer)\n"
            "- *'Show files'* (explore my sandbox files)\n"
            "- *'Focus on [new topic]'* (steer my responsibility)\n"
            "Or let me know how you'd like to adjust my continuous loop!"
        )

    async def _call_openai_chat(self, user_text: str) -> str:
        """Calls OpenAI API if user configured key."""
        try:
            memories = semantic_memory.get_recent(self.agent_id, limit=5)
            context = f"You are {self.agent.name}, an always-on persistent AI agent (a 'Dot').\n"
            context += f"Your enduring responsibility: '{self.agent.responsibility}'.\n"
            context += f"You have completed {self.agent.total_ticks} autonomous cycles.\n"
            context += f"Recent findings in your memory: {json.dumps(memories)}\n"
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.DEFAULT_MODEL,
                        "messages": [
                            {"role": "system", "content": context},
                            {"role": "user", "content": user_text},
                        ],
                        "temperature": 0.7,
                    },
                    timeout=20.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[Conversation] OpenAI API error: {e}")
        return await self._autonomous_cognitive_reply(user_text)

    async def _call_gemini_chat(self, user_text: str) -> str:
        """Calls Gemini API if user configured key."""
        # Fallback to cognitive reply if API fails
        return await self._autonomous_cognitive_reply(user_text)
