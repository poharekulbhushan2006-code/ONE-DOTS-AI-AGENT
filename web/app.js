/**
 * ONE: Always-On Autonomous AI Agent System
 * Frontend Application & Real-time Telemetry Dashboard
 */

let selectedAgentId = null;
let cachedAgents = [];
let pendingDecisions = [];

document.addEventListener('DOMContentLoaded', () => {
    initUI();
    fetchFleetData();
    setInterval(fetchFleetData, 3000); // 3-second real-time heartbeat polling
});

function initUI() {
    // Tabs Navigation
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const target = btn.getAttribute('data-tab');
            const targetEl = document.getElementById(target);
            if (targetEl) targetEl.classList.add('active');
        });
    });

    // Create Agent Modal
    const modal = document.getElementById('create-modal');
    document.getElementById('btn-open-create-modal').addEventListener('click', () => {
        modal.classList.add('open');
    });
    document.getElementById('btn-close-modal').addEventListener('click', () => {
        modal.classList.remove('open');
    });
    document.getElementById('btn-cancel-modal').addEventListener('click', () => {
        modal.classList.remove('open');
    });

    // Create Agent Form Submit
    document.getElementById('create-agent-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('agent-name-input').value.trim();
        const responsibility = document.getElementById('agent-mission-input').value.trim();
        const interval = parseInt(document.getElementById('agent-schedule-input').value, 10);

        if (!name || !responsibility) return;

        try {
            const res = await fetch('/api/agents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    responsibility,
                    schedule_interval_seconds: interval,
                })
            });
            if (res.ok) {
                const newAgent = await res.json();
                modal.classList.remove('open');
                document.getElementById('create-agent-form').reset();
                await fetchFleetData();
                selectAgent(newAgent.id);
            }
        } catch (err) {
            console.error('Failed to create agent:', err);
        }
    });

    // Force Tick Button
    document.getElementById('btn-force-tick').addEventListener('click', async () => {
        if (!selectedAgentId) return;
        const btn = document.getElementById('btn-force-tick');
        btn.disabled = true;
        btn.innerText = '⚡ Running Tick...';
        try {
            await fetch(`/api/agents/${selectedAgentId}/tick`, { method: 'POST' });
            await fetchFleetData();
        } catch (err) {
            console.error('Error triggering tick:', err);
        } finally {
            btn.disabled = false;
            btn.innerText = '⚡ Force Tick';
        }
    });

    // Toggle Pause/Resume Button
    document.getElementById('btn-toggle-pause').addEventListener('click', async () => {
        if (!selectedAgentId) return;
        const agent = cachedAgents.find(a => a.id === selectedAgentId);
        if (!agent) return;

        const action = agent.status === 'paused' ? 'resume' : 'pause';
        await fetch(`/api/agents/${selectedAgentId}/${action}`, { method: 'POST' });
        await fetchFleetData();
    });
}

async function fetchFleetData() {
    try {
        const [agentsRes, decisionsRes] = await Promise.all([
            fetch('/api/agents'),
            fetch('/api/decisions/pending'),
        ]);

        if (agentsRes.ok) {
            cachedAgents = await agentsRes.json();
            renderFleetSidebar(cachedAgents);
            updateTopMetrics(cachedAgents, pendingDecisions);
        }

        if (decisionsRes.ok) {
            pendingDecisions = await decisionsRes.json();
            renderDecisions(pendingDecisions);
            updateTopMetrics(cachedAgents, pendingDecisions);
        }

        // If an agent is selected, refresh its details
        if (selectedAgentId) {
            const current = cachedAgents.find(a => a.id === selectedAgentId);
            if (current) {
                renderAgentDetailHeader(current);
                renderLifecycleStage(current.current_stage);
                fetchAgentSteps(selectedAgentId);
                fetchAgentReports(selectedAgentId);
            }
        } else if (cachedAgents.length > 0) {
            selectAgent(cachedAgents[0].id);
        }
    } catch (err) {
        console.error('Error polling fleet data:', err);
    }
}

function updateTopMetrics(agents, decisions) {
    document.getElementById('metric-active-agents').innerText = agents.length;
    const totalTicks = agents.reduce((acc, a) => acc + (a.total_ticks || 0), 0);
    document.getElementById('metric-total-ticks').innerText = totalTicks;

    const pendingCount = decisions.length;
    document.getElementById('metric-pending-decisions').innerText = pendingCount;
    const tabBadge = document.getElementById('tab-badge-decisions');
    if (pendingCount > 0) {
        tabBadge.innerText = pendingCount;
        tabBadge.style.display = 'inline-block';
    } else {
        tabBadge.style.display = 'none';
    }
}

function renderFleetSidebar(agents) {
    const listEl = document.getElementById('agent-list');
    if (!agents || agents.length === 0) {
        listEl.innerHTML = `
            <div class="empty-state">
                <p>No autonomous units deployed yet.</p>
                <p style="margin-top: 8px;">Click <b>+ Assign New Responsibility</b> above to give an AI its first mission.</p>
            </div>
        `;
        return;
    }

    listEl.innerHTML = agents.map(agent => `
        <div class="agent-card ${agent.id === selectedAgentId ? 'active' : ''}" onclick="selectAgent('${agent.id}')">
            <div class="agent-card-header">
                <span class="agent-name">${escapeHtml(agent.name)}</span>
                <span class="status-badge ${agent.status}">${agent.status}</span>
            </div>
            <p class="agent-card-mission">${escapeHtml(agent.responsibility)}</p>
            <div class="agent-card-footer">
                <span>Ticks: ${agent.total_ticks}</span>
                <span>Stage: ${agent.current_stage}</span>
            </div>
        </div>
    `).join('');
}

function selectAgent(agentId) {
    selectedAgentId = agentId;
    const agent = cachedAgents.find(a => a.id === agentId);
    if (!agent) return;

    renderFleetSidebar(cachedAgents);
    renderAgentDetailHeader(agent);
    renderLifecycleStage(agent.current_stage);
    fetchAgentSteps(agentId);
    fetchAgentReports(agentId);
}

function renderAgentDetailHeader(agent) {
    document.getElementById('agent-controls').style.display = 'flex';
    document.getElementById('active-agent-name').innerText = agent.name;
    const statusEl = document.getElementById('active-agent-status');
    statusEl.innerText = agent.status;
    statusEl.className = `status-badge ${agent.status}`;
    document.getElementById('active-agent-responsibility').innerText = agent.responsibility;

    const pauseBtn = document.getElementById('btn-toggle-pause');
    if (agent.status === 'paused') {
        pauseBtn.innerText = '▶ Resume';
    } else {
        pauseBtn.innerText = '⏸ Pause';
    }
}

function renderLifecycleStage(stageName) {
    const stages = ['research', 'analyze', 'build', 'monitor', 'report', 'adapt'];
    const stageElements = document.querySelectorAll('.stage-step');

    stageElements.forEach(el => {
        const s = el.getAttribute('data-stage');
        if (s === stageName) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });
}

async function fetchAgentSteps(agentId) {
    try {
        const res = await fetch(`/api/agents/${agentId}/steps?limit=30`);
        if (!res.ok) return;
        const steps = await res.json();
        renderSteps(steps);
        renderScreenshotsFromSteps(steps);
    } catch (err) {
        console.error('Error fetching steps:', err);
    }
}

function renderSteps(steps) {
    const container = document.getElementById('steps-container');
    if (!steps || steps.length === 0) {
        container.innerHTML = `<div class="empty-state">No execution steps yet. Trigger a tick to start.</div>`;
        return;
    }

    container.innerHTML = steps.map(step => `
        <div class="step-card">
            <div class="step-card-header">
                <span class="step-stage-tag">${step.stage}</span>
                <span class="step-time">${new Date(step.timestamp).toLocaleTimeString()}</span>
            </div>
            <div class="step-action">${escapeHtml(step.action)}</div>
            ${step.output ? `<div class="step-io">${escapeHtml(JSON.stringify(step.output, null, 2))}</div>` : ''}
        </div>
    `).join('');
}

function renderScreenshotsFromSteps(steps) {
    const container = document.getElementById('browser-vision-container');
    const screenshots = [];

    steps.forEach(s => {
        if (s.output && s.output.screenshot) {
            screenshots.push(s.output.screenshot);
        }
    });

    if (screenshots.length === 0) {
        container.innerHTML = `<div class="empty-state">No browser screenshots captured yet. When the agent researches the web, browser snapshots will appear here.</div>`;
        return;
    }

    container.innerHTML = `
        <div class="screenshot-grid">
            ${screenshots.map(filename => `
                <div class="screenshot-item">
                    <a href="/screenshots/${filename}" target="_blank">
                        <img src="/screenshots/${filename}" alt="Browser Snapshot" loading="lazy">
                    </a>
                    <div class="screenshot-meta">${filename}</div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderDecisions(decisions) {
    const container = document.getElementById('decisions-container');
    if (!decisions || decisions.length === 0) {
        container.innerHTML = `<div class="empty-state">No pending decisions. The agent is operating safely within its bounds.</div>`;
        return;
    }

    container.innerHTML = decisions.map(d => `
        <div class="decision-card">
            <div class="decision-header">
                <span class="decision-title">⚠️ Decision Checkpoint: ${escapeHtml(d.action_type)}</span>
                <span class="status-badge waiting_approval">${d.risk_level.toUpperCase()} RISK</span>
            </div>
            <p>${escapeHtml(d.description)}</p>
            <div class="step-io">${escapeHtml(JSON.stringify(d.proposed_payload, null, 2))}</div>
            <div class="decision-actions">
                <button class="btn btn-success" onclick="resolveDecision('${d.id}', true)">✓ Approve & Proceed</button>
                <button class="btn btn-danger" onclick="resolveDecision('${d.id}', false)">✕ Reject & Adapt</button>
            </div>
        </div>
    `).join('');
}

async function resolveDecision(decisionId, isApproved) {
    const action = isApproved ? 'approve' : 'reject';
    try {
        await fetch(`/api/decisions/${decisionId}/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: isApproved ? 'Approved by operator via dashboard' : 'Rejected by operator' }),
        });
        await fetchFleetData();
    } catch (err) {
        console.error('Failed to resolve decision:', err);
    }
}

async function fetchAgentReports(agentId) {
    try {
        const res = await fetch(`/api/agents/${agentId}/reports`);
        if (!res.ok) return;
        const reports = await res.json();
        renderReports(reports);
    } catch (err) {
        console.error('Error fetching reports:', err);
    }
}

function renderReports(reports) {
    const container = document.getElementById('reports-container');
    if (!reports || reports.length === 0) {
        container.innerHTML = `<div class="empty-state">No reports generated yet. Reports are delivered upon cycle completion.</div>`;
        return;
    }

    container.innerHTML = reports.map(r => `
        <div class="report-card">
            <div class="report-title">${escapeHtml(r.title)}</div>
            <div style="font-size: 11px; color: var(--text-dim);">${new Date(r.created_at).toLocaleString()}</div>
            <div class="report-body">${escapeHtml(r.content)}</div>
        </div>
    `).join('');
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
