# ◈ ONE DOTS: Always-On Frontier Intelligence Platform

> **Autonomous AI dots that learn through continuous execution, proactive research, and trial-and-error discovery.**  
> Powered by **Google Gemini** (`gemini-3.5-flash-lite` / `gemini-3.8-flash`) with dedicated cloud computer sandboxes, real-time voice calls, and empirical discovery environments.

---

## 🌟 Overview

ONE DOTS provides a unified platform combining always-on autonomous agents, enterprise intelligence, and pure reinforcement learning discovery:

1. **Autonomous Workstation**: Real-time agent fleet management, Gemini-powered conversational streaming, cloud sandboxes, and file studio.
2. **Ineffable Intelligence Discovery Studio**: Pure trial-and-error discovery engine (inspired by David Silver & DeepMind FunSearch) discovering algorithmic heuristics and mathematical invariants in isolated execution sandboxes.
3. **Conversational Voice Calling**: Hands-free voice interface with real-time speech recognition, natural synthesis, and animated audio soundwaves.
4. **Docs & Knowledge Portal**: Architectural guides, interactive code samples, and embedded AI documentation assistant.

---

## 🤖 The 6 Specialist Dot Archetypes

| Dot | Archetype | Domain & Core Capabilities |
|---|---|---|
| 🔵 **Blue Dot** | **NOVA** | *Product Launch Lead*: Milestone planning, positioning, task tracking, and change-impact analysis. |
| 🟢 **Green Dot** | **SAGE** | *Research Scientist*: Dataset analysis, NumPy/SciPy statistical modeling, and publication-ready charts. |
| 🟡 **Yellow Dot** | **AXIS** | *Enterprise Tender Specialist*: RFP & tender clause extraction, compliance matrices, and proposal drafting. |
| 🟣 **Purple Dot** | **MUSE** | *Content Studio*: Generation of genuine Word documents (`.docx`), presentation decks (`.pptx`), and platform content. |
| 🛡️ **Dev Dot** | **HEX** | *Autonomous Developer*: Codebase inspection, dependency mapping, atomic sandbox patching, and pytest verification. |
| 🔴 **Red Dot** | **SILVER / AURA** | *Ineffable Intelligence Engine*: Autonomous trial-and-error discovery system. Discovers algorithmic optimizations, combinatorial heuristics, and mathematical conjectures verified in isolated sandboxes. |

---

## 🔬 Ineffable Intelligence: Empirical Discovery Engine

Inspired by David Silver's pure trial-and-error reinforcement learning paradigm and DeepMind FunSearch, the Discovery Engine learns from its own attempts rather than static training datasets:

- **Isolated Sandbox Verification**: Executes program candidates in air-gapped runtimes with deterministic evaluation, timeouts, and memory constraints.
- **Island Model Evolution**: Multi-island population pool prevents premature convergence and periodically migrates elite candidate solutions.
- **Verifiable Benchmarks**:
  - `bin_packing`: Combinatorial online bin-packing heuristic discovery (OR-Library).
  - `algorithm_opt`: Runtime speedup optimizations for sorting and search algorithms.
  - `math_conjecture`: Extremal graph invariants and counterexample search for mathematical conjectures.
- **Persistent Experience Store**: SQLite database recording trial code, execution metrics, reward progressions, and negative constraint reflections.

---

## ⚡ Project Structure

```
DOTS AI AGENT/
├── api/
│   ├── app.py            # FastAPI REST backend & static workstation mount
│   └── index.py          # Vercel serverless entrypoint
├── core/
│   ├── orchestrator.py   # 6-Stage Autonomous Lifecycle Engine
│   ├── conversation.py   # Google Gemini conversational cognitive engine
│   └── discovery/        # Ineffable Intelligence Engine
│       ├── discovery_engine.py  # Autonomous trial-and-error search loop
│       ├── island_pool.py       # Multi-island evolutionary candidate pool
│       ├── experience_store.py  # SQLite trial & breakthrough store
│       └── verifiers/           # Benchmarks (Bin Packing, Algo Opt, Math Conjectures)
├── memory/               # SQLite state store & episodic semantic memory
├── sandbox/              # Isolated cloud computer subprocess runtime
├── tools/                # Web search, browser inspection, tender intelligence
├── web/                  # Glassmorphic Workstation & Discovery Studio UI
└── tests/                # Automated pytest validation suite (51 passing tests)
```

---

## 🚀 Quickstart

### 1. Launch with One Click (Windows)
```powershell
.\run.bat
```

### 2. Manual Launch
```powershell
.venv\Scripts\activate
python app.py
```

Open:
- **Workstation & Discovery Studio**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ☁️ Deployment (Vercel & Cloud)

Configured for zero-config serverless deployment via `vercel.json`:
- **Frontend**: Pre-compiled static assets served with strict CSP security headers.
- **Backend API**: Python serverless runtime routed through `api/index.py`.

Continuous deployment is triggered automatically on push:
```bash
git push origin master
```

---

## 🧪 Testing

Run the full automated test suite:
```powershell
.venv\Scripts\python.exe -m pytest tests -v
```

---

## 📡 Key REST Endpoints

- **Fleet Management**: `GET /api/agents` • `POST /api/agents` • `DELETE /api/agents/{id}`
- **Conversational Chat**: `POST /api/agents/{id}/chat` • `GET /api/agents/{id}/briefing`
- **Discovery Studio**: `GET /api/discovery/benchmarks` • `POST /api/discovery/start` • `GET /api/discovery/status/{id}` • `POST /api/discovery/stop/{id}`
- **Tender Intelligence**: `POST /api/tenders/upload` • `GET /api/tenders/benchmarks`
- **Cloud Sandbox**: `POST /api/agents/{id}/execute` • `GET /api/agents/{id}/files`
