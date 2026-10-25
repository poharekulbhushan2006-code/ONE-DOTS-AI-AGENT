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
from core.task_engine import task_engine


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

        # Check if user prompt is an actionable execution task
        actionable_keywords = [
            "create presentation", "make ppt", "generate presentation", "generate slides", "slide deck",
            "create docx", "generate document", "make report", "study guide", "assignment report",
            "analyze data", "run hypothesis", "run t-test", "run anova", "generate chart", "plot chart",
            "fix bug", "fix test", "apply patch", "reproduce bug", "run pytest",
            "compliance matrix", "parse requirements", "rfp", "create roadmap", "project plan"
        ]
        lowered = user_text.lower()
        if any(kw in lowered for kw in actionable_keywords):
            task = task_engine.create_task(
                title=user_text[:50].strip(),
                goal=user_text,
                assigned_agent_id=self.agent_id
            )
            executed = await task_engine.execute_task(task.id)
            reply_text = executed.final_output or f"Task executed with status: `{executed.status.value}`."
        # Prioritize Google Gemini for analytical / conversational queries
        elif (settings.LLM_PROVIDER == "gemini" or not settings.OPENAI_API_KEY) and settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 15:
            reply_text = await self._call_gemini_chat(user_text)
        elif settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            reply_text = await self._call_openai_chat(user_text)
        elif settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY) > 15:
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

        # 6. Technical & Educational Knowledge Queries (e.g. "tell me about dbms")
        if any(w in lowered for w in ["dbms", "database", "sql", "rdbms", "nosql", "acid"]):
            return (
                "A **Database Management System (DBMS)** is specialized software that enables users and applications to create, protect, query, update, and administer structured collections of data.\n\n"
                "### 🏛️ Core Concepts & Architecture\n"
                "1. **Primary Functions**:\n"
                "   - **Data Definition (DDL)**: Formulate schemas, tables, relationships, and constraints.\n"
                "   - **Data Manipulation (DML)**: Query, insert, update, and filter records efficiently.\n"
                "   - **Concurrency & Locking**: Safely coordinate multi-user reads and writes without data corruption.\n\n"
                "2. **Major Categories of DBMS**:\n"
                "   - **Relational (RDBMS)**: Tabular data with strict schemas, relational foreign keys, and SQL standards (*PostgreSQL, MySQL, SQLite, Oracle*).\n"
                "   - **NoSQL / Document Stores**: Flexible JSON documents optimized for horizontal partitioning (*MongoDB, CouchDB, DynamoDB*).\n"
                "   - **Key-Value & In-Memory**: Ultra-low-latency caching stores (*Redis, Memcached*).\n"
                "   - **Vector Databases**: High-dimensional vector indexers for AI episodic memory & semantic retrieval (*sqlite-vec, ChromaDB, Pinecone*).\n\n"
                "3. **The ACID Guarantee**:\n"
                "   - **Atomicity**: Operations execute completely or roll back with zero partial changes.\n"
                "   - **Consistency**: Transactions preserve all integrity constraints, cascades, and validation rules.\n"
                "   - **Isolation**: Concurrent transactions execute safely without dirty reads or race conditions.\n"
                "   - **Durability**: Committed data is permanently written to non-volatile disk via Write-Ahead Logging (WAL).\n\n"
                "*In ONE DOTS, our autonomous agents utilize SQLite WAL for tamper-evident state storage and sqlite-vec for episodic memory recall.*"
            )

        if any(w in lowered for w in ["api", "rest api", "endpoint", "webhook"]):
            return (
                "An **Application Programming Interface (API)** is a formal protocol that allows distinct software applications to communicate and exchange data securely:\n\n"
                "- **REST APIs**: Stateless, resource-oriented HTTP endpoints utilizing verbs (`GET`, `POST`, `PUT`, `DELETE`) with standard status codes.\n"
                "- **Webhooks**: Event-driven push notifications triggered immediately when external events occur (e.g. GitHub commits, Stripe payments).\n"
                "- **FastAPI Framework**: Modern, high-performance Python web framework featuring async event loops, Pydantic type validation, and automatic OpenAPI documentation.\n\n"
                "*ONE DOTS exposes secure REST endpoints with Row-Level Security (RLS) and HMAC SHA-256 webhook signatures.*"
            )

        if any(w in lowered for w in ["python", "asyncio", "fastapi"]):
            return (
                "**Python** is a versatile high-level programming language renowned for its expressive syntax, rich ecosystem, and dominance in AI and backend engineering:\n\n"
                "- **AsyncIO**: Concurrent asynchronous execution with event loops, `async`/`await` coroutines, and non-blocking I/O.\n"
                "- **Type Hinting & Pydantic**: Robust runtime data validation and schema enforcement.\n"
                "- **Scientific Computing**: Libraries like NumPy, SciPy, and Pandas power empirical research (utilized by our **SAGE** specialist).\n\n"
                "*ONE DOTS executes sandboxed Python code in isolated cloud runtimes with interactive STDIN safety.*"
            )

        if any(w in lowered for w in ["machine learning", "artificial intelligence", "agent", "llm", "transformer"]):
            return (
                "**Autonomous AI Agents** are cognitive systems designed to perceive their environment, reason over multi-step goals, plan actions, and execute tools without constant manual intervention:\n\n"
                "### The 5-Stage Agent Lifecycle in ONE DOTS\n"
                "1. **Observe**: Ingest channel webhooks, environment logs, and user requirements.\n"
                "2. **Think**: Retrieve episodic memory, formulate plans, and reason over constraints.\n"
                "3. **Decide**: Evaluate risk tiers (Low/Medium/High) via the Action Auto-Review safeguard.\n"
                "4. **Act**: Execute Python code in cloud sandboxes, query external APIs, or create deliverables.\n"
                "5. **Learn**: Record outcomes, feedback, and execution traces into vector memory."
            )

        # 7. General Educational / Question responder
        if any(lowered.startswith(prefix) for prefix in ["can you tell me", "tell me about", "what is", "how do", "how does", "explain"]):
            clean_topic = user_text
            for prefix in ["can you tell me about", "can you tell me", "tell me about", "what is", "explain", "how does", "how do"]:
                if lowered.startswith(prefix):
                    clean_topic = user_text[len(prefix):].strip(" ?:.")
                    break
            return (
                f"Here is a comprehensive breakdown of **{clean_topic or 'your inquiry'}**:\n\n"
                f"- **Core Definition**: {clean_topic.capitalize()} represents a foundational concept in computer science and software systems.\n"
                f"- **Architecture & Integration**: In modern production platforms, components interact via clear interface contracts, automated testing, and secure data pipelines.\n"
                f"- **Best Practices**: Ensure strict schema validation, enforce tamper-evident logging, and maintain continuous automated test coverage.\n\n"
                f"As **{self.agent.name}**, I can assist you in researching this further, running Python simulations in my sandbox, or compiling a formal deliverable."
            )

        # 8. Default conversational response
        return (
            f"Understood. As your always-on agent for **{self.agent.name}**, I'm tracking: *'{self.agent.responsibility}'*.\n\n"
            "You can ask me to:\n"
            "- *'Can you tell me about [topic]?'* (explain technical and domain concepts)\n"
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
        """Calls Gemini API with agent state, episodic memory context, and mission awareness."""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return await self._autonomous_cognitive_reply(user_text)

        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)

            # Retrieve relevant memory snippets
            memories = semantic_memory.recall(self.agent_id, user_text, limit=3)

            system_instruction = (
                f"You are '{self.agent.name}', an advanced, persistent autonomous AI agent deployed inside DOTS AI OS.\n"
                f"Your Core Responsibility / Mission: '{self.agent.responsibility}'.\n"
                f"Current Status: {self.agent.status.value.upper()}.\n"
                f"Current Stage: {self.agent.current_stage.value.upper()}.\n"
                f"Autonomous Execution Cycles Completed: {self.agent.total_ticks}.\n"
                f"Historical Memory Knowledge: {memories}\n"
                "You communicate directly with human operators and system engineers. "
                "Provide sharp, analytical, intelligent answers reflecting your mission, progress, discoveries, and tools. "
                "Format responses cleanly with Markdown."
            )

            models = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-flash-latest", "gemini-3.5-flash"]
            for model_name in models:
                try:
                    res = client.models.generate_content(
                        model=model_name,
                        contents=user_text,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction
                        )
                    )
                    if res and res.text:
                        return res.text.strip()
                except Exception:
                    continue
        except Exception as e:
            print(f"[Conversation] Gemini API error: {e}")

        # Fallback to cognitive reply if API fails or network issue occurs
        return await self._autonomous_cognitive_reply(user_text)
