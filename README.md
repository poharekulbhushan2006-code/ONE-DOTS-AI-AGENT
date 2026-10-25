# ◈ ONE DOTS: Always-On Frontier Intelligence & Autonomous Agent Platform

> **Dots are remarkably capable, always-on agents built to handle everything.**  
> They’re a whole new way to work with AI—one that gets to know what matters to you, is always working on your behalf, and takes important work off your plate so you get more of your time and attention back.  
> Powered by **Google Gemini** (`gemini-3.5-flash-lite` / `gemini-3.8-flash`) with dedicated cloud computers, proactive research, 24/7 background cadences, and conversational Voice Calling.

---

## 🌟 The Vision: Dots Have Your Back

ONE DOTS brings frontier intelligence that has your back. Each Dot has its own cloud computer sandbox, learns from feedback over time, and works towards your goals 24/7. Through an ecosystem of integrations, they connect with over 4,000 apps and provide a unified experience combining:
1. **Flagship Product Showcase**: Official OpenAI-style launch experience with live cinematic film preview, department archetypes, and commercial pricing.
2. **Autonomous Agent Workstation**: Real-time fleet management, interactive Gemini chat, live REPL cloud computer with safe STDIN support, and file studio.
3. **Docs & Learn Knowledge Hub**: In-depth architecture guides modeled on `learn.chatgpt.com/docs`, with search, interactive code samples, and an embedded AI Docs assistant.

Your dot is always within reach. You can ask questions, explore ideas, give feedback, or hop on a **live voice call** when you need to talk something out. The more you work together, the more your dot learns your preferences, how you think, and what good looks like to you.

---

## 🤖 The 5 Specialist Dot Archetypes

Built directly into the CLI, REST API, and Conversational Workstation UI:

| Dot | Archetype | Mission & Capabilities |
|---|---|---|
| 🔵 **Blue Dot** | **NOVA** (Product Launch Lead) | *Strategy & Project Planning*: Turns ideas into milestones and dependencies, identifies positioning, conducts web research, tracks Linear/GitHub tasks, and performs change-impact analysis when requirements shift. |
| 🟢 **Green Dot** | **SAGE** (Research Scientist) | *Research & Empirical Analysis*: Parses CSV/XLSX datasets, executes NumPy/pandas/SciPy statistical modeling (Welch's t-test, ANOVA), generates publication-grade Matplotlib charts, and formulates sourced research reports. |
| 🟡 **Yellow Dot** | **AXIS** (Enterprise Specialist) | *Business & Technical Documentation*: Analyzes customer RFP and tender documents (PDF/DOCX), generates Requirement-to-Evidence compliance matrices, identifies gaps, and drafts commercial proposals. |
| 🟣 **Purple Dot** | **MUSE** (Content & Media Studio) | *Deliverable Production Studio*: Generates genuine, downloadable PowerPoint presentation decks (`.pptx`), Word reports/study guides (`.docx`), summaries, and platform-specific content variants. |
| 🛡️ **Dev Dot** | **HEX** (Autonomous Developer) | *Coding & Verified Execution*: Inspects repositories, maps dependencies, reproduces bugs, writes atomic patches in isolated sandboxes, executes pytest test suites, and generates verified code diffs. |


---

## 🛡️ Built-In Safeguards & Proactive Research

- **Isolated Cloud Computer Sandbox**: Each dot operates inside its own dedicated sandbox workspace (`data/sandboxes/<agent_id>`). It can write files, execute Python scripts, and run shell commands in complete isolation.
- **Proactive Research**: When not actively conversing, dots perform background research across live web sources using read-only tools that cannot alter external system content without consent.
- **Action Review & Human Approval Gate**: Sensitive or high-risk tasks are automatically held in the approval queue (`/api/decisions/pending`) for operator sign-off before proceeding.
- **Tri-Tier Persistent Memory**:
  - *Working Memory*: Active task execution context.
  - *Episodic Semantic Memory*: SQLite database (`data/episodic_memory.db`) with token scoring, WAL mode, and fast recall.
  - *Durable State Store*: Relational database (`data/one_state.db`) with WAL mode tracking steps, reports, checkpoints, and chat histories.

---

## 🎙️ Live Conversational Voice Call

- **Hop on a Call**: Click the **📞 Voice Call** button in the dashboard to speak directly with your dot.
- **Speech Recognition**: Listens in real-time via `webkitSpeechRecognition`.
- **Speech Synthesis**: Speaks replies with natural speech audio using `window.speechSynthesis`.
- **Audio Soundwave**: Visual pulsating glow reflects your dot's voice and thoughts in real-time.

---

## ⚡ Architecture Overview

```
DOTS AI AGENT/
├── .env                  # Google Gemini API Key & model routing
├── app.py                # Fast root server launcher (runs uvicorn api.app:app)
├── cli.py                # Command-Line Management Tool (server, deploy, list, tick, delete, test)
├── requirements.txt      # Project dependencies (FastAPI, Google GenAI, Playwright, etc.)
├── run.bat               # One-click Windows launch script
├── test_gemini.py        # Live Google Gemini API connectivity verifier
│
├── api/
│   └── app.py            # FastAPI REST backend & dashboard static mount
│
├── core/
│   ├── orchestrator.py   # 6-Stage Autonomous Lifecycle Engine (Research ➔ Analyze ➔ Build ➔ Monitor ➔ Report ➔ Adapt)
│   ├── heartbeat.py      # Background cadence scheduler with in-flight lock protection
│   ├── conversation.py   # Google Gemini conversational cognitive engine & catch-up digest
│   └── models.py         # Pydantic schemas (OneAgent, TaskStep, ChatMessage, Decision, Report)
│
├── memory/
│   ├── state_store.py    # SQLite relational state store (WAL mode, timeout=30s)
│   └── semantic_memory.py # Episodic semantic memory store (WAL mode, timeout=30s)
│
├── sandbox/
│   └── executor.py       # Isolated cloud computer subprocess execution environment
│
├── browser/
│   └── controller.py     # Headless Chromium Playwright automation & snapshot capture
│
├── tools/
│   └── registry.py       # Integrated tools: web search, browser inspect, sandbox runner, memory recall
│
├── hil/
│   └── approval_gate.py  # Human-in-the-loop action review and approval gate
│
├── web/                  # OpenAI Dot-style Conversational Workstation UI
│   ├── index.html        # Glassmorphic UI with Voice Call, 5 Specialist Dots, Cloud Computer Inspector
│   ├── app.js            # Real-time state synchronization, SpeechRecognition, chat stream
│   └── style.css         # Modern dark-mode glassmorphic aesthetics
│
├── tests/
│   └── test_dots_agents.py # Automated test suite for DOTS AI AGENT
│
└── data/                 # Persistent state databases, sandboxes, screenshots, reports
```

---

## 🚀 Quickstart & How to Run

### 1. Launch with One Click
Double-click `run.bat` or run in terminal:
```powershell
.\run.bat
```

### 2. Launch via Python
```powershell
# Activate virtual environment
.venv\Scripts\activate

# Launch the server
python app.py
```
Or via the CLI:
```powershell
python cli.py server
```

Then open your browser at:
* **Conversational Workstation UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🛠️ CLI Commands

```powershell
# List all active dots in your fleet
python cli.py list

# Deploy a Specialist Dot template
python cli.py deploy --template felipe   # Blue Dot (Felipe - Product Launch)
python cli.py deploy --template todd     # Green Dot (Todd - Research Scientist)
python cli.py deploy --template alfred   # Yellow Dot (Alfred - Enterprise Sales)
python cli.py deploy --template jojo     # Purple Dot (Jojo - Content Creator)
python cli.py deploy --template dev      # Dev Dot (Sentry - PR & Bug Fixer)

# Deploy a custom dot
python cli.py deploy --name "MarketRadar" --mission "Monitor AI models and track pricing shifts" --interval 180

# Trigger an immediate autonomous cycle
python cli.py tick --id <agent_id>

# Retire and delete an agent
python cli.py delete --id <agent_id>

# Run core subsystem self-test
python cli.py test
```

---

## 🧪 Automated Testing

Run the automated test suite:
```powershell
.venv\Scripts\python.exe -m pytest tests -v
```

Verify live Google Gemini connectivity:
```powershell
.venv\Scripts\python.exe test_gemini.py
```

---

## 📡 REST API Summary

- **Fleet Management**: `POST /api/agents`, `GET /api/agents`, `GET /api/agents/{id}`, `DELETE /api/agents/{id}`
- **Execution Cycles**: `POST /api/agents/{id}/tick`, `POST /api/agents/{id}/pause`, `POST /api/agents/{id}/resume`
- **Telemetry & Deliverables**: `GET /api/agents/{id}/steps`, `GET /api/agents/{id}/reports`
- **Conversational AI**: `POST /api/agents/{id}/chat`, `GET /api/agents/{id}/chat`, `GET /api/agents/{id}/briefing`
- **Cloud Computer Workspace**: `GET /api/agents/{id}/files`, `GET /api/agents/{id}/files/content`, `POST /api/agents/{id}/execute`
- **Human Escalation Gate**: `GET /api/decisions/pending`, `POST /api/decisions/{id}/approve`, `POST /api/decisions/{id}/reject`
