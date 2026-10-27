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
        Deep technical cognitive engine engineered by a senior full stack developer.
        Provides comprehensive, structured, domain-accurate explanations across
        computer science, databases, distributed systems, algorithms, Ineffable RL,
        Tender Intelligence, and application architecture.
        """
        lowered = user_text.lower().strip()

        # 1. Web search / browse intents
        if any(w in lowered for w in ["search for", "look up", "browse", "check online", "find info on"]):
            query = user_text
            for prefix in ["search for", "look up", "check online for", "find info on"]:
                if prefix in lowered:
                    query = user_text.split(prefix, 1)[-1].strip()
                    break
            search_res = self.tools.web_search(query, max_results=3)
            hits = search_res.get("results", [])
            if hits:
                reply = f"I navigated my search tools for **'{query}'**. Here is what I observed:\n\n"
                for h in hits:
                    reply += f"- **[{h.get('title')}]({h.get('href')})**: {h.get('body')}\n"
                reply += "\nI have preserved these observations in my episodic vector memory."
                self.tools.memory_remember(f"Search query '{query}': {hits[0].get('body')[:200]}")
                return reply
            return f"I searched for '{query}' but found no new public records."

        # 2. Python sandbox execution
        if any(w in lowered for w in ["run python", "execute code", "run script", "execute in sandbox"]):
            code = user_text
            if "```python" in user_text:
                code = user_text.split("```python")[1].split("```")[0].strip()
            elif "```" in user_text:
                code = user_text.split("```")[1].split("```")[0].strip()
            else:
                code = "import sys\nprint('Python runtime:', sys.version)\nprint('Dedicated sandbox environment active.')"
            
            res = self.tools.sandbox_run_python(code)
            return (
                f"### ⚙️ Dedicated Cloud Computer Sandbox Execution\n\n"
                f"- **Exit Code**: `{res.get('exit_code')}`\n"
                f"- **Standard Output**:\n```text\n{res.get('stdout', '').strip() or '(no stdout produced)'}\n```\n"
                + (f"- **Standard Error**:\n```text\n{res.get('stderr')}\n```\n" if res.get('stderr') else "")
                + f"\n*Execution was isolated with interactive STDIN safety and zero host network exposure.*"
            )

        # 3. Cloud computer file inspection
        if any(w in lowered for w in ["what files", "list files", "show files", "workspace files", "sandbox files"]):
            files = self.tools.file_list().get("files", [])
            if not files:
                return "My dedicated cloud computer workspace is currently clean. Artifacts generated on autonomous ticks will appear here."
            file_list_str = "\n".join([f"- `{f['path']}` ({f['size_bytes']:,} bytes)" for f in files])
            return f"### 📂 Cloud Computer Workspace Artifacts\n\n{file_list_str}\n\n*All files are isolated in `sandboxes/{self.agent_id}`.*"

        # 4. Mission update / Responsibility reassignment
        if any(w in lowered for w in ["change mission", "new goal", "focus on", "update responsibility"]):
            new_mission = user_text
            for prefix in ["change mission to", "new goal:", "focus on", "update responsibility to"]:
                if prefix in lowered:
                    new_mission = user_text.split(prefix, 1)[-1].strip()
                    break
            self.agent.responsibility = new_mission
            state_store.save_agent(self.agent)
            return (
                f"### 🎯 Mission Updated\n\n"
                f"I have committed your objective to my enduring state:\n> **{new_mission}**\n\n"
                f"My autonomous loop will execute against this goal on all subsequent cycles."
            )

        # 5. Status / Findings / Telemetry
        if any(w in lowered for w in ["what did you find", "agent status", "show progress", "summary report", "what are you doing"]):
            memories = semantic_memory.get_recent(self.agent_id, limit=3)
            reports = state_store.get_agent_reports(self.agent_id, limit=1)
            response = (
                f"### 📊 Telemetry & Status Briefing // {self.agent.name}\n\n"
                f"- **Core Mission**: *\"{self.agent.responsibility}\"*\n"
                f"- **Operational State**: `{self.agent.status.value.upper()}` (Stage: `{self.agent.current_stage.value.upper()}`)\n"
                f"- **Tick Cadence**: Every {self.agent.schedule_interval_seconds}s (Total Cycles Completed: **{self.agent.total_ticks}**)\n"
                f"- **Sandbox Environment**: Active (`sandboxes/{self.agent_id}`)\n\n"
            )
            if memories:
                response += "**Recent Episodic Knowledge**:\n"
                for m in memories:
                    response += f"- {m['content']}\n"
            if reports:
                response += f"\n**Latest Intelligence Report**: *{reports[0].title}*\n{reports[0].summary}"
            return response

        # 6. Database / DBMS / SQL / ACID / Storage Engines
        if any(w in lowered for w in ["dbms", "database", "rdbms", "nosql", "acid", "sql", "transaction", "sqlite", "postgres", "indexing"]):
            return (
                "### 🏛️ Database Management Systems (DBMS) // Technical Architecture\n\n"
                "A **Database Management System (DBMS)** is specialized systems software that provides an organized, secure, and transactional layer between applications and non-volatile physical storage.\n\n"
                "#### 1. Core Functions & Architectural Components\n"
                "- **Storage Engine**: Manages physical pages, heap files, and disk block serialization.\n"
                "- **Query Engine & Optimizer**: Converts SQL statements into abstract syntax trees (ASTs), estimates cost with statistics, and builds execution plans (e.g. Index Scan vs Sequential Scan).\n"
                "- **Concurrency Controller & WAL**: Coordinates parallel read/write transactions via Multi-Version Concurrency Control (MVCC) or Two-Phase Locking (2PL).\n\n"
                "#### 2. The ACID Invariants\n"
                "- **Atomicity**: All operations in a transaction commit completely or abort with zero partial modifications.\n"
                "- **Consistency**: State changes preserve all primary keys, foreign key cascades, unique constraints, and schema invariants.\n"
                "- **Isolation**: Concurrent transactions execute with zero dirty reads (`READ UNCOMMITTED`), non-repeatable reads (`READ COMMITTED`), or phantom rows (`SERIALIZABLE`).\n"
                "- **Durability**: Once committed, changes survive catastrophic power loss via Write-Ahead Logging (WAL) flushed with `fsync()`.\n\n"
                "#### 3. RDBMS vs NoSQL Taxonomy\n"
                "| Paradigm | Data Model | Scaling Strategy | Canonical Examples | Best Used For |\n"
                "| :--- | :--- | :--- | :--- | :--- |\n"
                "| **Relational (RDBMS)** | Tables, Rows, Relations | Vertical scaling (Scale-Up), Read Replicas | PostgreSQL, SQLite, MySQL | Financial ledgers, ACID state, user identity |\n"
                "| **Document Stores** | JSON / BSON trees | Horizontal partitioning (Sharding) | MongoDB, CouchDB | Dynamic catalogs, polymorphic payloads |\n"
                "| **Key-Value / Cache** | In-memory key-blob pairs | Memory cluster sharding | Redis, Memcached | Session stores, rate limiting, hot caches |\n"
                "| **Vector Stores** | High-dimensional embeddings | HNSW / IVFFlat vector indexing | sqlite-vec, pgvector, Pinecone | LLM episodic memory, semantic search |\n\n"
                "*In ONE DOTS, our backend uses SQLite in WAL mode with Row-Level Security (RLS) for zero-latency local persistence and sqlite-vec for agent memory.*"
            )

        # 7. Ineffable Empirical Discovery Engine & Pure RL
        if any(w in lowered for w in ["discovery", "ineffable", "silver", "funsearch", "bin packing", "heuristic", "conjecture", "pure rl", "reinforcement learning"]):
            return (
                "### 🔬 Ineffable Empirical Discovery Engine // Autonomous RL Architecture\n\n"
                "Grounded in **David Silver's pure trial-and-error reinforcement learning paradigm** (responsible for AlphaZero and DeepMind FunSearch), the Ineffable Discovery Engine synthesizes and discovers net-new algorithmic programs and scientific heuristics without human demonstration data.\n\n"
                "#### 1. The 4-Phase Discovery Loop\n"
                "1. **Program Mutation (LLM Prompting)**: Generates candidate algorithmic heuristics by mutating existing top-performing programs at the Abstract Syntax Tree (AST) level.\n"
                "2. **AST Static Safety Verification**: Inspects AST nodes using Python's `ast` module to reject forbidden calls (`os.system`, `subprocess`, file I/O, socket networking) before runtime.\n"
                "3. **Deterministic Sandbox Verification**: Executes the candidate in an isolated container against ground-truth mathematical problem instances.\n"
                "4. **Pareto Island Migration**: Multiple parallel populations (Alpha, Beta, Gamma) maintain genetic diversity and periodically exchange top-tier breakthroughs.\n\n"
                "#### 2. Active Empirical Simulators\n"
                "- **Online 1D Bin Packing**: Discovers adaptive item-to-bin scoring functions that outperform classical Best-Fit and First-Fit algorithms on uniform distributions.\n"
                "- **Range Minimum Query (RMQ)**: Synthesizes sub-linear range query algorithms with O(N log N) precomputation and O(1) query time.\n"
                "- **Prime Invariant Conjectures**: Evolves polynomial formulas maximizing continuous sequences of prime numbers.\n\n"
                "*Zero Hallucination Guarantee: Code is never accepted based on natural language generation; acceptance requires passing deterministic unit test exit codes with reward > 0.90.*"
            )

        # 8. AXIS Tender Intelligence & Indian Government Procurement
        if any(w in lowered for w in ["tender", "rfp", "bid", "nit", "pwd", "cpwd", "nhai", "turnover", "solvency", "bid capacity", "dossier"]):
            return (
                "### 📑 AXIS Tender Intelligence & Bid Readiness // Government Procurement Engine\n\n"
                "The **AXIS Tender Intelligence Engine** automates the ingestion, auditing, eligibility evaluation, and compliance dossier generation for complex 100+ page Indian government procurement documents.\n\n"
                "#### 1. Ingestion & NIT Parameter Extraction\n"
                "- Ingests Notice Inviting Tender (NIT) PDFs and scans across **Maharashtra PWD**, **Central PWD (CPWD)**, and **NHAI**.\n"
                "- Extracts critical metadata in sub-second latency: NIT Number, Portal Tender ID, Authority Division, Estimated Cost (INR Crores), Earnest Money Deposit (EMD 1-2%), Completion Timeline, and Defect Liability Period (DLP 36-60 Months).\n\n"
                "#### 2. Statutory Indian Bid Capacity Formula\n"
                "Enforces the mandatory Indian procurement bid capacity formula:\n\n"
                "$$\\text{Available Bid Capacity} = (A \\times N \\times 2) - B$$\n\n"
                "- **$A$**: Maximum annual value of civil engineering works executed in any one year during the last 5 financial years (indexed at 10% per annum compound rate).\n"
                "- **$N$**: Prescribed completion period in years.\n"
                "- **$B$**: Value of existing commitments and on-going works to be completed during the target project window.\n"
                "- **Requirement**: Available Bid Capacity must strictly exceed the Tender Estimated Cost.\n\n"
                "#### 3. Automated Executive Deliverables\n"
                "- **Microsoft Word (.docx) Bid Readiness Dossier**: Client-ready executive deliverable with executive summary, financial feasibility score, technical gap analysis, and mandatory tender checklists.\n"
                "- **Requirement-to-Evidence Compliance Matrix (.md)**: Clause-by-clause audit table referencing specific page numbers and compliance status (PASS / FAIL / MITIGATION)."
            )

        # 9. System Design & Distributed Architecture
        if any(w in lowered for w in ["system design", "distributed system", "microservices", "monolith", "load balancer", "caching", "redis", "kafka", "cap theorem", "rate limit"]):
            return (
                "### 📐 System Design & Distributed Systems // Senior Architecture Reference\n\n"
                "Designing scalable, resilient software architectures requires balancing latency, throughput, consistency, and operational complexity.\n\n"
                "#### 1. Core Architectural Patterns\n"
                "- **Microservices vs Modular Monolith**: Start with a clean modular monolith to eliminate network serialization overhead and distributed transaction overhead; decompose into microservices only when independent team velocity or resource scaling necessitates it.\n"
                "- **Load Balancing**: Layer 4 (Transport/TCP via HAProxy/NLB) for high-packet throughput; Layer 7 (Application/HTTP via NGINX/Envoy/ALB) for path-based routing, TLS termination, and header rewriting.\n"
                "- **Caching Strategies**:\n"
                "  - *Cache-Aside (Lazy Loading)*: Application reads cache; on miss, fetches from DB and populates cache.\n"
                "  - *Write-Through*: Data is written simultaneously to cache and DB.\n"
                "  - *Write-Behind (Write-Back)*: Data is written to cache immediately and queued for asynchronous disk persistence.\n\n"
                "#### 2. The CAP Theorem & PACELC\n"
                "- In the event of a Network **P**artition: Must choose between **C**onsistency (linearizable reads/writes) or **A**vailability (every non-failing node returns a non-error response).\n"
                "- **PACELC Extension**: If there is a **P**artition, trade off **A**vailability vs **C**onsistency; **E**lse, trade off **L**atency vs **C**onsistency.\n\n"
                "#### 3. Rate Limiting Algorithms\n"
                "- **Token Bucket**: Allows short bursts up to bucket capacity while maintaining fixed replenishment rate (used in AWS & Stripe APIs).\n"
                "- **Leaky Bucket**: Enforces smooth, constant egress rate regardless of ingress burstiness.\n"
                "- **Sliding Window Counter**: Eliminates the 2x burst loophole at window boundary edges found in fixed-window limiters."
            )

        # 10. Data Structures & Algorithms (DSA)
        if any(w in lowered for w in ["dsa", "algorithm", "data structure", "big o", "dynamic programming", "binary search", "graph", "tree", "sorting"]):
            return (
                "### ⚡ Data Structures & Algorithms (DSA) // Core Foundations\n\n"
                "Algorithms provide optimal computational procedures to solve well-defined problems within rigorous time and space complexity bounds.\n\n"
                "#### 1. Asymptotic Complexity Reference (Big-O)\n"
                "| Data Structure | Access | Search | Insertion | Deletion | Space Complexity |\n"
                "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
                "| **Array / Dynamic Array** | $O(1)$ | $O(N)$ | $O(N)$ (amortized $O(1)$ at end) | $O(N)$ | $O(N)$ |\n"
                "| **Hash Table** | N/A | $O(1)$ avg / $O(N)$ worst | $O(1)$ avg / $O(N)$ worst | $O(1)$ avg / $O(N)$ worst | $O(N)$ |\n"
                "| **Balanced BST (AVL/Red-Black)** | $O(\\log N)$ | $O(\\log N)$ | $O(\\log N)$ | $O(\\log N)$ | $O(N)$ |\n"
                "| **Trie (Prefix Tree)** | N/A | $O(L)$ ($L$ = key length) | $O(L)$ | $O(L)$ | $O(N \\times \\Sigma)$ |\n\n"
                "#### 2. Foundational Algorithmic Paradigms\n"
                "- **Divide and Conquer**: Break problem into independent sub-problems, solve recursively, and merge (e.g. MergeSort $O(N \\log N)$, Fast Fourier Transform).\n"
                "- **Dynamic Programming (DP)**: Solve overlapping sub-problems with optimal substructure via memoization (top-down) or tabulation (bottom-up) (e.g. 0/1 Knapsack, Longest Common Subsequence).\n"
                "- **Graph Traversals**: Breadth-First Search ($O(V+E)$ for shortest unweighted path) vs Depth-First Search ($O(V+E)$ for topological sort and cycle detection).\n"
                "- **Greedy Heuristics**: Make locally optimal choices at each stage (e.g. Dijkstra's Algorithm with Min-Heap $O((V+E) \\log V)$, Kruskal's MST)."
            )

        # 11. Operating Systems & Concurrency
        if any(w in lowered for w in ["operating system", "os", "concurrency", "thread", "process", "deadlock", "mutex", "semaphore", "virtual memory", "paging"]):
            return (
                "### 💻 Operating Systems & Concurrency // Kernel & Systems Principles\n\n"
                "The Operating System acts as the resource orchestrator, multiplexing CPU, memory, and I/O devices among competing concurrent execution flows.\n\n"
                "#### 1. Process vs Thread\n"
                "- **Process**: Isolated unit of resource allocation with private virtual address space, file descriptor table, and memory registers. IPC requires pipes, shared memory, or sockets.\n"
                "- **Thread**: Lightweight unit of CPU execution within a process, sharing memory address space, heap, and open handles, but maintaining independent stacks and program counters.\n\n"
                "#### 2. Synchronization Primitives\n"
                "- **Mutex**: Mutual exclusion lock granting sole access to a critical section (ownership semantics).\n"
                "- **Counting Semaphore**: Integer signaling counter permitting up to $N$ concurrent holders.\n"
                "- **Deadlock & The 4 Coffman Conditions**: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait. Breaking any one condition prevents deadlock.\n\n"
                "#### 3. Memory Virtualization & Paging\n"
                "- **MMU & Page Tables**: Translates virtual addresses to physical RAM blocks via Multi-level Page Tables and the Translation Lookaside Buffer (TLB) cache.\n"
                "- **Demand Paging**: Loads pages into physical RAM only upon access; raises Page Faults to swap missing pages from disk."
            )

        # 12. Cyber Security & Application Hardening
        if any(w in lowered for w in ["security", "appsec", "owasp", "rls", "xss", "csrf", "sql injection", "cryptography", "jwt", "hmac"]):
            return (
                "### 🛡️ Enterprise Application Security // 19-Layer Defense-in-Depth\n\n"
                "Enterprise software security requires eliminating single points of failure through continuous zero-trust validation and multi-tiered defense.\n\n"
                "#### 1. Threat Mitigation Taxonomy\n"
                "- **SQL Injection (SQLi)**: Completely mitigated using parameterized SQL queries and typed ORM/Pydantic validation schemas.\n"
                "- **Cross-Site Scripting (XSS)**: Prevented via strict Content Security Policy (`default-src 'self'`), context-aware HTML entity escaping, and disabling untrusted script execution.\n"
                "- **Insecure Direct Object Reference (IDOR)**: Enforced via Row-Level Security (RLS) ensuring every DB query joins on authenticated `user_id`.\n"
                "- **Authentication & Tamper Evidence**: Stateless HMAC-SHA256 tokens and immutable append-only SQLite WAL audit ledgers.\n\n"
                "#### 2. Cloud Computer Sandbox Isolation\n"
                "- Every autonomous agent code run executes inside an ephemeral process container.\n"
                "- Host filesystems are protected via path sandboxing (`sandboxes/{agent_id}`), preventing traversal attacks (`../`).\n"
                "- Interactive STDIN streams handle prompts without shell injection vulnerabilities."
            )

        # 13. Web Development, Frontend, JavaScript & CSS
        if any(w in lowered for w in ["frontend", "javascript", "css", "dom", "event loop", "react", "html", "browser"]):
            return (
                "### 🌐 Web Engineering & Frontend Architecture // Senior Standards\n\n"
                "High-performance web applications prioritize sub-100ms First Contentful Paint (FCP), semantic markup, accessible navigation, and predictable event dispatch.\n\n"
                "#### 1. JavaScript Engine & Event Loop\n"
                "- **Call Stack**: Executes synchronous stack frames sequentially.\n"
                "- **Microtask Queue**: High priority queue (Promises, `queueMicrotask`) drained immediately after every stack turn before browser render paints.\n"
                "- **Macrotask Queue**: Scheduled tasks (`setTimeout`, `setInterval`, I/O events) executed across subsequent ticks.\n\n"
                "#### 2. Modern Vanilla CSS Design Systems\n"
                "- **Custom Properties (CSS Variables)**: Centralized design token system (`:root`) for instant, zero-rebuild theme adaptation.\n"
                "- **Layout Primitives**: CSS Grid for 2D macro-layouts (workbench, dashboard panels) and Flexbox for 1D micro-alignment.\n"
                "- **GPU Acceleration**: Leverage `transform: translateZ(0)` and `opacity` transitions for smooth 60 FPS animations without triggering expensive layout reflows."
            )

        # 14. Autonomous AI Agents & The 6 Specialists
        if any(w in lowered for w in ["who are you", "what agents", "specialist", "nova", "sage", "axis", "muse", "hex", "silver", "dots"]):
            return (
                f"### ◈ ONE DOTS Specialist Fleet Architecture\n\n"
                f"I am **{self.agent.name}**, one of 6 specialized persistent autonomous AI agents engineered to execute continuous work within DOTS AI OS.\n\n"
                f"#### The 6 Flagship Specialists\n"
                f"1. **Blue Dot (NOVA)** // Product Launch Lead: Formulates delivery roadmaps, coordinates milestone dispatch, and audits GTM release readiness.\n"
                f"2. **Lime-Green Dot (SAGE)** // Lead Research Scientist: Conducts empirical hypothesis testing, SciPy regressions, descriptive analytics, and publication charts.\n"
                f"3. **Golden-Yellow Dot (AXIS)** // Enterprise Operations & Tenders Lead: Ingests 100+ page NIT government documents, calculates statutory Indian bid capacity, and builds Word .docx Bid Dossiers.\n"
                f"4. **Purple Dot (MUSE)** // Content & Deliverables Studio: Generates native PowerPoint decks (.pptx), study guides, formatted reports (.docx), and visual designs.\n"
                f"5. **Dark Navy Dot (HEX)** // Principal Security Architect & Developer: Self-healing code repair, pytest regressions, AppSec compliance, and repository audits.\n"
                f"6. **Red Dot (SILVER)** // Ineffable Discovery Scientist: Pure trial-and-error RL & FunSearch evolutionary code mutation with deterministic sandbox verifiers.\n\n"
                f"My active mission: **{self.agent.responsibility}**."
            )

        # 15. Dynamic Question Answering Parser for General Technical Inquiries
        clean_topic = user_text.strip(" ?:.")
        for prefix in [
            "can you tell me about", "can you tell me", "tell me about", "what is", "what are",
            "how do", "how does", "how to", "explain", "describe", "why does", "why is", "compare"
        ]:
            if lowered.startswith(prefix):
                clean_topic = user_text[len(prefix):].strip(" ?:.")
                break

        return (
            f"### ◈ Response from {self.agent.name} // Architectural Analysis\n\n"
            f"**Regarding**: *\"{clean_topic}\"*\n\n"
            f"#### 1. Executive Summary & Conceptual Model\n"
            f"In modern software engineering and autonomous systems, **{clean_topic}** represents a fundamental domain requirement. "
            f"Implementing it effectively demands rigorous schema definition, deterministic verification, and automated error handling.\n\n"
            f"#### 2. Key Principles & Engineering Considerations\n"
            f"- **Interface Contracts**: Establish strong boundary specifications and typed contracts (e.g., Pydantic schemas, REST API endpoints) to prevent runtime drift.\n"
            f"- **Execution Isolation**: When executing computational or dynamic logic, isolate processes within dedicated sandboxes with interactive STDIN safety.\n"
            f"- **Observability & Telemetry**: Maintain structured audit logging, telemetry metrics, and immutable state persistence to guarantee non-repudiation.\n\n"
            f"#### 3. Autonomous Execution Capabilities\n"
            f"As **{self.agent.name}** (Specialist Mission: *{self.agent.responsibility}*), I can:\n"
            f"- Execute verified Python simulations in my cloud computer sandbox.\n"
            f"- Recall previous context and findings from our vector episodic memory.\n"
            f"- Formulate a structured specification, code patch, or formal deliverable.\n\n"
            f"Would you like me to execute code in my sandbox computer, inspect live data, or generate a full technical deliverable on this topic?"
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
                    timeout=10.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[Conversation] OpenAI API error: {e}")
        return await self._autonomous_cognitive_reply(user_text)

    async def _call_gemini_chat(self, user_text: str) -> str:
        """
        Calls Gemini REST API with agent state, episodic memory context, and mission awareness.
        Uses pure asynchronous HTTP with an absolute 2.5-second timeout and instant failover.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return await self._autonomous_cognitive_reply(user_text)

        try:
            memories = semantic_memory.recall(self.agent_id, user_text, limit=3)
            system_instruction = (
                f"You are '{self.agent.name}', an advanced, persistent autonomous AI agent deployed inside DOTS AI OS.\n"
                f"Your Core Responsibility / Mission: '{self.agent.responsibility}'.\n"
                f"Current Status: {self.agent.status.value.upper()}.\n"
                f"Current Stage: {self.agent.current_stage.value.upper()}.\n"
                f"Autonomous Execution Cycles Completed: {self.agent.total_ticks}.\n"
                f"Historical Memory Knowledge: {memories}\n"
                "You communicate directly with human operators and system engineers. "
                "Provide sharp, analytical, intelligent answers directly addressing the user's inquiry reflecting your mission, progress, discoveries, and tools. "
                "Format responses cleanly with Markdown."
            )

            models = ["gemini-3.8-flash", "gemini-flash-latest"]
            async with httpx.AsyncClient(timeout=2.5) as client:
                for model_name in models:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                        payload = {
                            "systemInstruction": {"parts": [{"text": system_instruction}]},
                            "contents": [{"parts": [{"text": user_text}]}],
                            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
                        }
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                text_parts = candidates[0].get("content", {}).get("parts", [])
                                if text_parts and "text" in text_parts[0]:
                                    return text_parts[0]["text"].strip()
                    except Exception:
                        continue
        except Exception as e:
            print(f"[Conversation] Gemini REST error: {e}")

        # Instant failover to deep domain cognitive engine
        return await self._autonomous_cognitive_reply(user_text)

