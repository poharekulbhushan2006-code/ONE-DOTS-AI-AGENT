/**
 * ONE: Always-On Autonomous AI Agent System
 * Frontend Application & OpenAI Dot-style Conversational Workstation
 */

let selectedAgentId = null;
let cachedAgents = [];
let pendingDecisions = [];

document.addEventListener('DOMContentLoaded', () => {
    initUI();
    fetchFleetData();
    setInterval(fetchFleetData, 3000); // 3-second continuous real-time refresh
});

function initUI() {
    // Inspector Tabs Navigation
    const tabButtons = document.querySelectorAll('.inspector-tabs .tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.inspector-content').forEach(c => c.classList.remove('active'));

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

    // Dismiss Catch-up Briefing
    document.getElementById('btn-dismiss-briefing').addEventListener('click', () => {
        document.getElementById('catchup-briefing').style.display = 'none';
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

    // Force Autonomous Tick (Step Progress)
    document.getElementById('btn-force-tick').addEventListener('click', async () => {
        if (!selectedAgentId) return;
        const btn = document.getElementById('btn-force-tick');
        btn.disabled = true;
        btn.innerText = '⚡ Ticking...';
        try {
            await fetch(`/api/agents/${selectedAgentId}/tick`, { method: 'POST' });
            await fetchFleetData();
            loadCatchupBriefing(selectedAgentId);
            fetchAgentChat(selectedAgentId);
        } catch (err) {
            console.error('Error triggering tick:', err);
        } finally {
            btn.disabled = false;
            btn.innerText = '⚡ Step Progress';
        }
    });

    // Toggle Pause/Resume
    document.getElementById('btn-toggle-pause').addEventListener('click', async () => {
        if (!selectedAgentId) return;
        const agent = cachedAgents.find(a => a.id === selectedAgentId);
        if (!agent) return;

        const action = agent.status === 'paused' ? 'resume' : 'pause';
        await fetch(`/api/agents/${selectedAgentId}/${action}`, { method: 'POST' });
        await fetchFleetData();
    });

    // Chat Message Form Submit
    document.getElementById('chat-input-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text || !selectedAgentId) return;

        input.value = '';
        appendChatMessage('user', text);

        try {
            const res = await fetch(`/api/agents/${selectedAgentId}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            if (res.ok) {
                const data = await res.json();
                appendChatMessage('agent', data.content);
                // Also refresh files and memory
                fetchSandboxFiles(selectedAgentId);
            }
        } catch (err) {
            console.error('Error sending chat:', err);
        }
    });

    // Refresh Files Button
    document.getElementById('btn-refresh-files').addEventListener('click', () => {
        if (selectedAgentId) fetchSandboxFiles(selectedAgentId);
    });

    // Run Code in Sandbox Button
    document.getElementById('btn-run-sandbox').addEventListener('click', async () => {
        if (!selectedAgentId) return;
        const code = document.getElementById('sandbox-code-input').value.trim();
        const lang = document.getElementById('sandbox-lang-select').value;
        const outputEl = document.getElementById('sandbox-run-output');

        if (!code) return;
        outputEl.style.display = 'block';
        outputEl.innerText = 'Executing in sandbox cloud computer...';

        try {
            const res = await fetch(`/api/agents/${selectedAgentId}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language: lang })
            });
            if (res.ok) {
                const data = await res.json();
                outputEl.innerText = `Exit Code: ${data.exit_code}\n${data.stdout || ''}${data.stderr ? '\nStderr: ' + data.stderr : ''}`;
                fetchSandboxFiles(selectedAgentId);
            }
        } catch (err) {
            outputEl.innerText = `Execution error: ${err}`;
        }
    });
}

function sendQuickPrompt(promptText) {
    const input = document.getElementById('chat-input');
    input.value = promptText;
    document.getElementById('chat-input-form').dispatchEvent(new Event('submit'));
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
            updateTopMetrics(cachedAgents, pendingDecisions);
        }

        if (selectedAgentId) {
            const current = cachedAgents.find(a => a.id === selectedAgentId);
            if (current) {
                renderDotHeader(current);
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
    document.getElementById('metric-total-ticks').innerText = `${totalTicks} ticks`;

    const pendingCount = decisions.length;
    document.getElementById('metric-pending-decisions').innerText = pendingCount;
}

function renderFleetSidebar(agents) {
    const listEl = document.getElementById('agent-list');
    if (!agents || agents.length === 0) {
        listEl.innerHTML = `
            <div class="empty-state">
                <p>No active Dots.</p>
                <p style="margin-top: 6px;">Click <b>+ Assign New Responsibility</b> above to give an AI its first mission.</p>
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
            <div style="font-size: 10px; color: var(--text-dim); display: flex; justify-content: space-between;">
                <span>Ticks: ${agent.total_ticks}</span>
                <span>${agent.schedule_interval_seconds}s cadence</span>
            </div>
        </div>
    `).join('');
}

function selectAgent(agentId) {
    selectedAgentId = agentId;
    const agent = cachedAgents.find(a => a.id === agentId);
    if (!agent) return;

    renderFleetSidebar(cachedAgents);
    renderDotHeader(agent);

    document.getElementById('chat-input-form').style.display = 'flex';
    document.getElementById('prompt-pills').style.display = 'flex';
    document.getElementById('agent-controls').style.display = 'flex';

    loadCatchupBriefing(agentId);
    fetchAgentChat(agentId);
    fetchSandboxFiles(agentId);
    fetchAgentSteps(agentId);
    fetchAgentReports(agentId);
}

function renderDotHeader(agent) {
    document.getElementById('active-agent-name').innerText = agent.name;
    const statusEl = document.getElementById('active-agent-status');
    statusEl.innerText = agent.status;
    statusEl.className = `status-badge ${agent.status}`;
    document.getElementById('active-agent-responsibility').innerText = `"${agent.responsibility}"`;

    const pauseBtn = document.getElementById('btn-toggle-pause');
    if (agent.status === 'paused') {
        pauseBtn.innerText = '▶ Resume';
    } else {
        pauseBtn.innerText = '⏸ Pause';
    }
}

async function loadCatchupBriefing(agentId) {
    try {
        const res = await fetch(`/api/agents/${agentId}/briefing`);
        if (!res.ok) return;
        const data = await res.json();
        const briefingCard = document.getElementById('catchup-briefing');
        const textEl = document.getElementById('briefing-text');
        textEl.innerText = data.briefing;
        briefingCard.style.display = 'flex';
    } catch (err) {
        console.error('Error loading briefing:', err);
    }
}

async function fetchAgentChat(agentId) {
    try {
        const res = await fetch(`/api/agents/${agentId}/chat`);
        if (!res.ok) return;
        const messages = await res.json();
        renderChatMessages(messages);
    } catch (err) {
        console.error('Error fetching chat history:', err);
    }
}

function renderChatMessages(messages) {
    const container = document.getElementById('chat-messages-container');
    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No chat history yet with this Dot.</p>
                <p style="margin-top: 6px;">Say hello or click a prompt pill below to collaborate!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = messages.map(m => `
        <div class="chat-bubble ${m.sender}">
            <span class="bubble-sender">${m.sender === 'user' ? 'You' : 'Dot'}</span>
            <div class="bubble-content">${escapeHtml(m.content)}</div>
        </div>
    `).join('');
    container.scrollTop = container.scrollHeight;
}

function appendChatMessage(sender, text) {
    const container = document.getElementById('chat-messages-container');
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    bubble.innerHTML = `
        <span class="bubble-sender">${sender === 'user' ? 'You' : 'Dot'}</span>
        <div class="bubble-content">${escapeHtml(text)}</div>
    `;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

async function fetchSandboxFiles(agentId) {
    try {
        const res = await fetch(`/api/agents/${agentId}/files`);
        if (!res.ok) return;
        const data = await res.json();
        const tree = document.getElementById('file-tree');
        const files = data.files || [];

        if (files.length === 0) {
            tree.innerHTML = `<div class="empty-state">Cloud computer workspace is empty.</div>`;
            return;
        }

        tree.innerHTML = files.map(f => `
            <div class="file-item" onclick="viewFileContent('${escapeHtml(f.path)}')">
                <span>📄 ${escapeHtml(f.path)}</span>
                <span style="color: var(--text-dim); font-size: 10px;">${f.size_bytes} B</span>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error fetching sandbox files:', err);
    }
}

async function viewFileContent(filePath) {
    if (!selectedAgentId) return;
    try {
        const res = await fetch(`/api/agents/${selectedAgentId}/files/content?path=${encodeURIComponent(filePath)}`);
        if (!res.ok) return;
        const data = await res.json();
        const viewerSection = document.getElementById('file-viewer-section');
        document.getElementById('file-viewer-filename').innerText = `📄 ${data.path}`;
        document.getElementById('file-viewer-content').innerText = data.content;
        viewerSection.style.display = 'flex';
    } catch (err) {
        console.error('Error reading file:', err);
    }
}

async function fetchAgentSteps(agentId) {
    try {
        const res = await fetch(`/api/agents/${agentId}/steps?limit=30`);
        if (!res.ok) return;
        const steps = await res.json();
        renderSteps(steps);
        renderScreenshotsFromSteps(steps);
        renderMemoriesFromSteps(steps);
    } catch (err) {
        console.error('Error fetching steps:', err);
    }
}

function renderSteps(steps) {
    const container = document.getElementById('steps-container');
    if (!steps || steps.length === 0) {
        container.innerHTML = `<div class="empty-state">No execution steps yet.</div>`;
        return;
    }

    container.innerHTML = steps.map(step => `
        <div class="step-card" style="padding: 10px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: 6px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: var(--accent-cyan);">
                <b>${step.stage.toUpperCase()}</b>
                <span style="color: var(--text-dim);">${new Date(step.timestamp).toLocaleTimeString()}</span>
            </div>
            <div style="font-size: 11px; margin-top: 4px;">${escapeHtml(step.action)}</div>
            ${step.output ? `<pre style="font-size: 10px; background: rgba(0,0,0,0.4); padding: 6px; margin-top: 4px; border-radius: 4px; max-height: 80px; overflow-y: auto;">${escapeHtml(JSON.stringify(step.output, null, 2))}</pre>` : ''}
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
        container.innerHTML = `<div class="empty-state">No browser screenshots captured yet.</div>`;
        return;
    }

    container.innerHTML = `
        <div class="screenshot-grid">
            ${screenshots.map(filename => `
                <div class="screenshot-item">
                    <a href="/screenshots/${filename}" target="_blank">
                        <img src="/screenshots/${filename}" alt="Browser Snapshot" loading="lazy">
                    </a>
                    <div style="padding: 4px 6px; font-size: 9px; color: var(--text-dim);">${filename}</div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderMemoriesFromSteps(steps) {
    const container = document.getElementById('memory-list');
    const memorySteps = steps.filter(s => s.action.includes('Researched') || s.action.includes('Analyzed'));

    if (memorySteps.length === 0) {
        container.innerHTML = `<div class="empty-state">No observations recorded in memory bank yet.</div>`;
        return;
    }

    container.innerHTML = memorySteps.map(s => `
        <div class="memory-card">
            <div class="memory-meta">
                <span>Stage: ${s.stage}</span>
                <span>${new Date(s.timestamp).toLocaleTimeString()}</span>
            </div>
            <div>${escapeHtml(s.action)}</div>
        </div>
    `).join('');
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
        container.innerHTML = `<div class="empty-state">No reports generated yet.</div>`;
        return;
    }

    container.innerHTML = reports.map(r => `
        <div style="padding: 12px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: 6px; margin-bottom: 10px;">
            <div style="font-size: 13px; font-weight: 700;">${escapeHtml(r.title)}</div>
            <div style="font-size: 10px; color: var(--text-dim); margin-top: 2px;">${new Date(r.created_at).toLocaleString()}</div>
            <pre style="font-size: 11px; color: #cbd5e1; margin-top: 8px; white-space: pre-wrap; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px;">${escapeHtml(r.content)}</pre>
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
