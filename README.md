# ◈ ONE: Persistent, Always-On Autonomous AI Agent System

> **Give an AI a responsibility — not just a one-off prompt.**  
> One goal. One environment. Always on.

---

## 💡 The Paradigm Shift

| Traditional Chatbot | ONE (Always-On Agent) |
| :--- | :--- |
| **"Do this now"** (Synchronous) | **"Own this responsibility and keep it moving"** (Asynchronous) |
| Ephemeral conversation session | Persistent cloud computer, sandbox & filesystem |
| Forgets context after session closes | Tri-tier persistent memory (working, episodic, state DB) |
| Passive: Waits for human input | Active: Heartbeat scheduler ticks automatically on cadence |
| Blind to web changes | Autonomous headless browser with vision & snapshotting |
| Halts or hallucinates on barriers | Escalate & pause: Requests human judgment when it matters |

---

## ⚡ The 6-Stage Autonomous Lifecycle

At every scheduled cadence (tick), each **ONE** unit navigates through:

```
[01 Research] ➔ [02 Analyze] ➔ [03 Build] ➔ [04 Monitor] ➔ [05 Report] ➔ [06 Adapt]
```

1. **Research**: Gathers live information using headless Chromium and web searches.
2. **Analyze**: Synthesizes newly discovered facts against historical episodic memory.
3. **Build**: Executes code, scripts, and transformations inside its dedicated sandbox computer.
4. **Monitor**: Assesses sandbox health, checks exit codes, and audits filesystem changes.
5. **Report**: Compiles and delivers structured intelligence digests and executive deliverables.
6. **Adapt**: Self-reflects on errors, handles human feedback, and tunes scheduling.

---

## 🚀 Quickstart

### 1. Set Up Environment
```powershell
# Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Run Self-Test Diagnostic
Verify that all subsystems (SQLite State DB, Sandbox Computer, Episodic Memory, Autonomous Browser, and Lifecycle Engine) are operational:
```powershell
.venv\Scripts\python.exe cli.py test
```

### 3. Launch Web Dashboard & Control Plane
```powershell
.venv\Scripts\python.exe cli.py server
```
Then open your browser to: **`http://127.0.0.1:8000`**

---

## 🛠️ CLI Reference

### Deploy a New ONE Unit
```powershell
.venv\Scripts\python.exe cli.py deploy --name "MarketRadar" --mission "Continuously monitor AI lab updates and track pricing shifts" --interval 180
```

### List Fleet Status
```powershell
.venv\Scripts\python.exe cli.py list
```

### Manually Trigger an Immediate Tick
```powershell
.venv\Scripts\python.exe cli.py tick --id <agent_id>
```

---

## 📡 REST API & Escalation Gate

- `POST /api/agents`: Deploy an agent with name, responsibility, and cadence.
- `GET /api/agents`: List all deployed agents and status.
- `POST /api/agents/{id}/tick`: Force an immediate execution cycle.
- `GET /api/agents/{id}/steps`: Fetch real-time telemetry steps.
- `GET /api/agents/{id}/reports`: Retrieve markdown intelligence reports.
- `GET /api/decisions/pending`: Inspect pending human escalations.
- `POST /api/decisions/{id}/approve`: Operator approval to resume blocked action.
- `POST /api/decisions/{id}/reject`: Operator rejection instructing agent to adapt.
