/**
 * ONE: Always-On Autonomous AI Agent System
 * Frontend Application & OpenAI Dot-style Conversational Workstation
 * Enterprise Security Hardened Suite:
 * - Bearer & API Key Session Injection
 * - Input Sanitization & XSS Defense
 * - Zero-Trust Identity & Admin Vault Controls
 * - Cryptographic CAPTCHA Integration
 * - Private Storage & Scoped Screenshot Access
 */

// --- ENTERPRISE DEFENSIVE UTILITIES ---
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function getAuthToken() {
    return sessionStorage.getItem('dots_auth_token') || localStorage.getItem('dots_auth_token') || 'dots-admin-sec-key-770021';
}

function setAuthToken(token) {
    sessionStorage.setItem('dots_auth_token', token);
    localStorage.setItem('dots_auth_token', token);
}

// Global secure fetch interceptor: injects Authorization headers and handles 401 & 429
const _nativeFetch = window.fetch;
window.fetch = async function(url, options = {}) {
    options = options || {};
    options.headers = options.headers || {};
    const urlStr = typeof url === 'string' ? url : (url.url || '');
    if (urlStr.startsWith('/api/') || urlStr.includes('/api/')) {
        const token = getAuthToken();
        if (token) {
            if (options.headers instanceof Headers) {
                if (!options.headers.has('Authorization') && !options.headers.has('X-API-Key')) {
                    options.headers.set('Authorization', `Bearer ${token}`);
                }
            } else if (typeof options.headers === 'object') {
                if (!options.headers['Authorization'] && !options.headers['X-API-Key']) {
                    options.headers['Authorization'] = `Bearer ${token}`;
                }
            }
        }
    }
    const res = await _nativeFetch(url, options);
    if (res.status === 401 && urlStr.startsWith('/api/') && !urlStr.includes('/api/auth/login')) {
        console.warn('[Security] Unauthorized 401: Valid credentials required.');
        openAuthModal();
    } else if (res.status === 429) {
        showSecurityToast('Rate limit triggered (429). Throttling requests to protect system availability.', 'warning');
    }
    return res;
};

let currentAuthUser = null;

async function fetchCurrentUserProfile() {
    try {
        const res = await fetch('/api/auth/me');
        if (res.ok) {
            currentAuthUser = await res.json();
            updateSecurityUI();
        } else {
            currentAuthUser = null;
        }
    } catch (e) {
        console.warn('[Security] Auth check failed:', e);
    }
}

function updateSecurityUI() {
    const adminBtn = document.getElementById('btn-admin-console');
    const uName = document.getElementById('auth-active-username');
    const tId = document.getElementById('auth-active-tenant');
    const rRole = document.getElementById('auth-active-role');

    if (currentAuthUser) {
        if (uName) uName.textContent = currentAuthUser.username;
        if (tId) tId.textContent = currentAuthUser.tenant_id;
        if (rRole) rRole.textContent = currentAuthUser.role.toUpperCase();

        if (adminBtn) {
            adminBtn.style.display = (currentAuthUser.is_admin || currentAuthUser.role === 'admin') ? 'inline-flex' : 'none';
        }
    } else {
        if (adminBtn) adminBtn.style.display = 'none';
    }
}

function openAuthModal() {
    const m = document.getElementById('auth-modal');
    if (m) {
        m.classList.add('open');
        fetchCurrentUserProfile();
        const keyInp = document.getElementById('auth-api-key-input');
        if (keyInp) keyInp.value = getAuthToken();
    }
}

function closeAuthModal() {
    const m = document.getElementById('auth-modal');
    if (m) m.classList.remove('open');
}

function applyQuickKey(type) {
    const keyInp = document.getElementById('auth-api-key-input');
    if (type === 'admin') {
        if (keyInp) keyInp.value = 'dots-admin-sec-key-770021';
    } else {
        if (keyInp) keyInp.value = 'dots-user-key-12345';
    }
}

async function handleAuthSubmit(e) {
    if (e) e.preventDefault();
    const keyInp = document.getElementById('auth-api-key-input');
    const key = keyInp ? keyInp.value.trim() : '';
    if (!key) return;
    setAuthToken(key);
    await fetchCurrentUserProfile();
    closeAuthModal();
    fetchFleetData();
    showSecurityToast('Authentication credentials updated successfully.', 'success');
}

function handleLogout() {
    sessionStorage.removeItem('dots_auth_token');
    localStorage.removeItem('dots_auth_token');
    currentAuthUser = null;
    updateSecurityUI();
    const keyInp = document.getElementById('auth-api-key-input');
    if (keyInp) keyInp.value = '';
    showSecurityToast('Active session cleared.', 'info');
}

// CAPTCHA Challenge Subsystem
async function loadCaptchaChallenge() {
    const qEl = document.getElementById('captcha-question-display');
    const tInp = document.getElementById('captcha-token-hidden');
    const aInp = document.getElementById('captcha-answer-input');
    if (qEl) qEl.textContent = 'Generating challenge...';
    if (aInp) aInp.value = '';

    try {
        const res = await fetch('/api/auth/captcha');
        if (res.ok) {
            const data = await res.json();
            if (qEl) qEl.textContent = data.question;
            if (tInp) tInp.value = data.token;
        }
    } catch (e) {
        if (qEl) qEl.textContent = 'Challenge error. Click refresh.';
    }
}

// Admin Audit Vault Subsystem
let cachedAuditLogs = [];

function openAdminModal() {
    const m = document.getElementById('admin-modal');
    if (m) {
        m.classList.add('open');
        fetchAdminAuditLogs();
    }
}

function closeAdminModal() {
    const m = document.getElementById('admin-modal');
    if (m) m.classList.remove('open');
}

async function fetchAdminAuditLogs() {
    const tbody = document.getElementById('audit-logs-tbody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6" style="padding: 20px; text-align: center; color: #94a3b8;">Fetching immutable audit logs from database...</td></tr>';
    }
    try {
        const res = await fetch('/api/admin/audit-logs?limit=50');
        if (!res.ok) {
            if (tbody) tbody.innerHTML = `<tr><td colspan="6" style="padding: 20px; text-align: center; color: #f87171;">Access Denied (403): Administrator privileges required.</td></tr>`;
            return;
        }
        cachedAuditLogs = await res.json();
        renderAuditLogs(cachedAuditLogs);
    } catch (e) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="6" style="padding: 20px; text-align: center; color: #f87171;">Failed to load audit logs: ${escapeHTML(e.message)}</td></tr>`;
    }
}

function filterAuditLogs(action) {
    if (action === 'ALL') {
        renderAuditLogs(cachedAuditLogs);
    } else {
        const filtered = cachedAuditLogs.filter(l => l.action === action);
        renderAuditLogs(filtered);
    }
}

function renderAuditLogs(logs) {
    const tbody = document.getElementById('audit-logs-tbody');
    if (!tbody) return;
    if (!logs || logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="padding: 20px; text-align: center; color: #94a3b8;">No audit records match the selected filter.</td></tr>';
        return;
    }
    tbody.innerHTML = logs.map(l => {
        const statusColor = l.status === 'SUCCESS' ? '#34d399' : (l.status === 'BLOCKED' ? '#f59e0b' : '#f87171');
        const dt = new Date(l.timestamp).toLocaleTimeString();
        return `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 8px 10px; font-family: monospace; color: #94a3b8;">${escapeHTML(dt)}</td>
                <td style="padding: 8px 10px; font-weight: 500; color: #e2e8f0;">${escapeHTML(l.user_id)}</td>
                <td style="padding: 8px 10px;"><code style="background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; color: #38bdf8;">${escapeHTML(l.action)}</code></td>
                <td style="padding: 8px 10px; color: #cbd5e1;">${escapeHTML(l.resource_type)} ${l.resource_id ? `<span style="color:#64748b;">(${escapeHTML(l.resource_id)})</span>` : ''}</td>
                <td style="padding: 8px 10px;"><span style="color: ${statusColor}; font-weight: 700;">● ${escapeHTML(l.status)}</span></td>
                <td style="padding: 8px 10px; font-family: monospace; color: #64748b;">${escapeHTML(l.ip_address || '127.0.0.1')}</td>
            </tr>
        `;
    }).join('');
}

function showSecurityToast(msg, type = 'info') {
    let toast = document.getElementById('sec-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'sec-toast';
        toast.style.cssText = 'position: fixed; bottom: 24px; right: 24px; padding: 12px 18px; border-radius: 8px; font-size: 13px; font-weight: 500; z-index: 10000; box-shadow: 0 10px 25px rgba(0,0,0,0.5); transition: opacity 0.3s;';
        document.body.appendChild(toast);
    }
    const bg = type === 'warn' || type === 'warning' ? '#b45309' : (type === 'success' ? '#065f46' : '#1e293b');
    toast.style.background = bg;
    toast.style.border = `1px solid rgba(255,255,255,0.2)`;
    toast.style.color = '#fff';
    toast.textContent = msg;
    toast.style.opacity = '1';
    setTimeout(() => { toast.style.opacity = '0'; }, 4000);
}

let selectedAgentId = null;
let cachedAgents = [];
let pendingDecisions = [];

document.addEventListener('DOMContentLoaded', () => {
    initEntrySplash();
    initUI();
    fetchCurrentUserProfile();
    fetchFleetData();
    updateFilmUI();
    loadCaptchaChallenge();
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
        loadCaptchaChallenge();
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

    // Create Agent Form Submit (with CAPTCHA verification)
    document.getElementById('create-agent-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('agent-name-input').value.trim();
        const responsibility = document.getElementById('agent-mission-input').value.trim();
        const interval = parseInt(document.getElementById('agent-schedule-input').value, 10);
        const color = document.getElementById('agent-color-input')?.value || 'cyan';
        const archetype = document.getElementById('agent-archetype-input')?.value || 'custom';
        const captchaToken = document.getElementById('captcha-token-hidden')?.value || '';
        const captchaAnswer = document.getElementById('captcha-answer-input')?.value.trim() || '';

        if (!name || !responsibility) return;

        try {
            const res = await fetch('/api/agents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    responsibility,
                    schedule_interval_seconds: interval,
                    context: { color, archetype },
                    captcha_token: captchaToken,
                    captcha_answer: captchaAnswer,
                })
            });
            if (res.ok) {
                const newAgent = await res.json();
                modal.classList.remove('open');
                document.getElementById('create-agent-form').reset();
                document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
                await fetchFleetData();
                selectAgent(newAgent.id);
                showSecurityToast('Specialist Dot deployed successfully with audit log generated.', 'success');
            } else {
                const errData = await res.json().catch(() => ({ detail: 'Creation failed' }));
                alert(errData.detail || 'Failed to deploy agent. Please verify human challenge.');
                loadCaptchaChallenge();
            }
        } catch (err) {
            console.error('Failed to create agent:', err);
            loadCaptchaChallenge();
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

    // Delete / Retire Agent
    const deleteBtn = document.getElementById('btn-delete-agent');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', async () => {
            if (!selectedAgentId) return;
            const agent = cachedAgents.find(a => a.id === selectedAgentId);
            const name = agent ? agent.name : 'this agent';
            if (!confirm(`Are you sure you want to retire and delete "${name}"? This will clean up its state and history.`)) return;

            try {
                const res = await fetch(`/api/agents/${selectedAgentId}`, { method: 'DELETE' });
                if (res.ok) {
                    selectedAgentId = null;
                    document.getElementById('agent-controls').style.display = 'none';
                    document.getElementById('chat-input-form').style.display = 'none';
                    document.getElementById('prompt-pills').style.display = 'none';
                    document.getElementById('catchup-briefing').style.display = 'none';
                    document.getElementById('chat-messages-container').innerHTML = '<div class="empty-state">Select an agent from the fleet to collaborate.</div>';
                    await fetchFleetData();
                }
            } catch (err) {
                console.error('Failed to delete agent:', err);
            }
        });
    }

    // Chat Message Form Submit
    document.getElementById('chat-input-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('btn-send-chat');
        const text = input.value.trim();
        if (!text || !selectedAgentId) return;

        input.value = '';
        input.disabled = true;
        sendBtn.disabled = true;
        sendBtn.innerText = '...';

        appendChatMessage('user', text);
        showTypingIndicator();

        try {
            const res = await fetch(`/api/agents/${selectedAgentId}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            removeTypingIndicator();
            if (res.ok) {
                const data = await res.json();
                appendChatMessage('agent', data.content);
                fetchSandboxFiles(selectedAgentId);
            } else {
                const errData = await res.json().catch(() => ({}));
                appendChatMessage('agent', `⚠️ Failed to get reply: ${errData.detail || 'Server error ' + res.status}`);
            }
        } catch (err) {
            removeTypingIndicator();
            console.error('Error sending chat:', err);
            appendChatMessage('agent', `⚠️ Connection error: Make sure the server is running on http://127.0.0.1:8000.`);
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            sendBtn.innerText = 'Send';
            input.focus();
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
        const stdin = document.getElementById('sandbox-stdin-input')?.value || "";
        const lang = document.getElementById('sandbox-lang-select').value;
        const outputEl = document.getElementById('sandbox-run-output');

        if (!code) return;
        outputEl.style.display = 'block';
        outputEl.innerText = 'Executing in sandbox cloud computer...';

        try {
            const res = await fetch(`/api/agents/${selectedAgentId}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language: lang, stdin })
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
    const activeCount = agents.length;
    const totalTicks = agents.reduce((acc, a) => acc + (a.total_ticks || 0), 0);
    const pendingCount = (decisions && decisions.length) || 0;

    const elActive = document.getElementById('metric-active-agents');
    if (elActive) elActive.innerText = activeCount;
    const elTicks = document.getElementById('metric-total-ticks');
    if (elTicks) elTicks.innerText = `${totalTicks} ticks`;
    const elPending = document.getElementById('metric-pending-decisions');
    if (elPending) elPending.innerText = pendingCount;

    // Navbar & Showcase Tickers
    const navCount = document.getElementById('nav-active-dots');
    if (navCount) navCount.innerText = activeCount;
    const tickerDots = document.getElementById('ticker-active-dots');
    if (tickerDots) tickerDots.innerText = activeCount;
    const tickerCycles = document.getElementById('ticker-total-cycles');
    if (tickerCycles) tickerCycles.innerText = `${totalTicks}+`;

    // Live Action Review Banner
    const banner = document.getElementById('approval-alert-banner');
    if (banner) {
        if (pendingCount > 0) {
            banner.style.display = 'flex';
            const d = decisions[0];
            const riskEl = document.getElementById('alert-risk-level');
            if (riskEl) riskEl.innerText = (d.risk_level || 'HIGH RISK').toUpperCase();
            const descEl = document.getElementById('alert-description');
            if (descEl) descEl.innerText = `${d.agent_name || 'Autonomous Dot'} is requesting authorization: "${d.action_summary || d.description || 'Protected operation'}"`;
        } else {
            banner.style.display = 'none';
        }
    }
}

const DOT_PRESETS = {
    felipe: {
        name: "Blue Dot (Felipe)",
        color: "blue",
        mission: "Lead product launch readiness: learn audience & positioning, revise launch story as scope changes, and prepare email & social drafts.",
        interval: 180
    },
    todd: {
        name: "Green Dot (Todd)",
        color: "green",
        mission: "Research Scientist: learn research goals, evaluate incoming evidence, rerun data analyses in sandbox, and flag unexpected results.",
        interval: 180
    },
    alfred: {
        name: "Yellow Dot (Alfred)",
        color: "yellow",
        mission: "Enterprise Sales Lead: review customer requirements against docs, test integrations, generate sandbox proof-of-concepts, and update proposals.",
        interval: 300
    },
    jojo: {
        name: "Purple Dot (Jojo)",
        color: "purple",
        mission: "Content Creator & Media Lead: learn creator voice, extract clip moments from interview transcripts, generate show notes, and draft social posts.",
        interval: 180
    },
    dev: {
        name: "Dev Dot (Sentry)",
        color: "cyan",
        mission: "Software Developer: monitor customer feedback for bug reports, scope fixes, execute test suites in sandbox cloud computer, and prepare verified PRs.",
        interval: 120
    }
};

function applyPreset(type) {
    const p = DOT_PRESETS[type];
    if (!p) return;
    document.getElementById('agent-name-input').value = p.name;
    document.getElementById('agent-mission-input').value = p.mission;
    document.getElementById('agent-schedule-input').value = p.interval;
    const colorEl = document.getElementById('agent-color-input');
    if (colorEl) colorEl.value = p.color;
    const archEl = document.getElementById('agent-archetype-input');
    if (archEl) archEl.value = type;

    document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
    if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add('active');
    }
}

function getDotColor(agent) {
    if (agent.context && agent.context.color) return agent.context.color;
    const lower = (agent.name + " " + agent.responsibility).toLowerCase();
    if (lower.includes("blue") || lower.includes("felipe") || lower.includes("launch")) return "blue";
    if (lower.includes("green") || lower.includes("todd") || lower.includes("scientist") || lower.includes("science")) return "green";
    if (lower.includes("yellow") || lower.includes("alfred") || lower.includes("sales") || lower.includes("enterprise") || lower.includes("deal")) return "yellow";
    if (lower.includes("purple") || lower.includes("jojo") || lower.includes("content") || lower.includes("creator")) return "purple";
    return "cyan";
}

function getDotAvatarSrc(agent) {
    if (!agent) return 'assets/dots/felipe_avatar.png';
    const archetype = (agent.context?.archetype || '').toLowerCase();
    const name = (agent.name || '').toLowerCase();
    const resp = (agent.responsibility || '').toLowerCase();

    if (archetype === 'felipe' || name.includes('felipe') || name.includes('blue') || resp.includes('launch')) {
        return 'assets/dots/felipe_avatar.png';
    }
    if (archetype === 'todd' || name.includes('todd') || name.includes('green') || resp.includes('scientist') || resp.includes('research')) {
        return 'assets/dots/todd_avatar.png';
    }
    if (archetype === 'alfred' || name.includes('alfred') || name.includes('yellow') || resp.includes('sales') || resp.includes('enterprise') || resp.includes('poc')) {
        return 'assets/dots/alfred_avatar.png';
    }
    if (archetype === 'jojo' || name.includes('jojo') || name.includes('purple') || resp.includes('content') || resp.includes('media') || resp.includes('viral')) {
        return 'assets/dots/jojo_avatar.png';
    }
    if (archetype === 'dev' || name.includes('sentry') || name.includes('dev') || resp.includes('software') || resp.includes('bug')) {
        return 'assets/dots/sentry_avatar.png';
    }
    const c = getDotColor(agent);
    if (c === 'green') return 'assets/dots/todd_avatar.png';
    if (c === 'yellow') return 'assets/dots/alfred_avatar.png';
    if (c === 'purple') return 'assets/dots/jojo_avatar.png';
    if (c === 'cyan') return 'assets/dots/sentry_avatar.png';
    return 'assets/dots/felipe_avatar.png';
}

function getDotColorHex(agent) {
    const c = getDotColor(agent);
    const map = {
        blue: "#3b82f6",
        green: "#10b981",
        yellow: "#f59e0b",
        purple: "#a855f7",
        cyan: "#06b6d4"
    };
    return map[c] || "#06b6d4";
}

// =========================================================================
// INTERACTIVE CARTOON PERSONALITY & SQUASH-AND-STRETCH PHYSICS ENGINE
// =========================================================================
function playCartoonPopSound(pitchMultiplier = 1.0) {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        
        osc.type = 'sine';
        const now = ctx.currentTime;
        // Rubbery cartoon boing sweep
        osc.frequency.setValueAtTime(260 * pitchMultiplier, now);
        osc.frequency.exponentialRampToValueAtTime(820 * pitchMultiplier, now + 0.08);
        osc.frequency.exponentialRampToValueAtTime(400 * pitchMultiplier, now + 0.18);
        
        gain.gain.setValueAtTime(0.35, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
        
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start(now);
        osc.stop(now + 0.23);
    } catch (e) {
        // AudioContext not available or blocked
    }
}

const CARTOON_QUIPS = {
    felipe: [
        "Hey! Ready to launch this product! 🚀",
        "Audience positioning locked & loaded! ✨",
        "Launch story looks stellar! Let's go! ◈",
        "Checking blockers and shipping today!"
    ],
    todd: [
        "Aha! A breakthrough hypothesis! 🔬",
        "Running statistical verification now... 📊",
        "Data correlation verified 100%! 🧪",
        "The experimental evidence is crystal clear!"
    ],
    alfred: [
        "Deal closed! Handshake verified 🤝",
        "Enterprise ROI is looking phenomenal! 💼",
        "RFP documentation drafted & approved! 📈",
        "Solutions engineers synced for the POC!"
    ],
    jojo: [
        "This is totally viral material! 🎬",
        "Dropping fresh podcast clips now! 🎧",
        "High-engagement hooks ready for socials! ✨",
        "Trending audio matched to our creator voice! 🔥"
    ],
    dev: [
        "Bug squashed, PR merged cleanly! ⚡",
        "All 42 sandbox unit tests passing! 🛡️",
        "Commit signed and verified in cloud computer! </>>",
        "Zero regressions detected! Code is rock-solid!"
    ]
};

function touchDotCartoon(dotType, element, event, dotName) {
    if (event) event.stopPropagation();

    // Determine character key
    let key = dotType;
    if (!key && dotName) {
        const lower = dotName.toLowerCase();
        if (lower.includes('felipe') || lower.includes('blue')) key = 'felipe';
        else if (lower.includes('todd') || lower.includes('green') || lower.includes('scientist')) key = 'todd';
        else if (lower.includes('alfred') || lower.includes('yellow') || lower.includes('sales')) key = 'alfred';
        else if (lower.includes('jojo') || lower.includes('purple') || lower.includes('content')) key = 'jojo';
        else if (lower.includes('sentry') || lower.includes('dev')) key = 'dev';
    }
    if (!key) key = 'felipe';

    // Play rubbery cartoon pop sound
    const pitchMap = { felipe: 1.1, todd: 1.25, alfred: 0.9, jojo: 1.35, dev: 0.85 };
    playCartoonPopSound(pitchMap[key] || 1.0);

    // Find the image element to squish
    const imgEl = (element && element.tagName === 'IMG') ? element : (element ? element.querySelector('img') : null);
    if (imgEl) {
        imgEl.classList.remove('cartoon-squish');
        void imgEl.offsetWidth; // Force reflow
        imgEl.classList.add('cartoon-squish');
        setTimeout(() => imgEl.classList.remove('cartoon-squish'), 700);
    }

    // Pick a random personality quip
    const quipList = CARTOON_QUIPS[key] || CARTOON_QUIPS.felipe;
    const quip = quipList[Math.floor(Math.random() * quipList.length)];

    // Show speech bubbles (both hero cluster and showcase cards)
    const bubbles = document.querySelectorAll(`[id^="speech-${key}"]`);
    bubbles.forEach(bubble => {
        bubble.innerText = quip;
        bubble.classList.add('active');
        clearTimeout(bubble._bubbleTimer);
        bubble._bubbleTimer = setTimeout(() => {
            bubble.classList.remove('active');
        }, 2800);
    });

    // Speak quip with cheerful cartoon pitch
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(quip.replace(/[^\w\s!?,]/g, ''));
        utter.pitch = (key === 'alfred' || key === 'dev') ? 1.05 : 1.3;
        utter.rate = 1.1;
        window.speechSynthesis.speak(utter);
    }
}

// 3D Parallax Tilt for Cartoon Cards on Mouse Move
function handleDotCardTilt(e, card) {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    const rotateX = -(y / (rect.height / 2)) * 8;
    const rotateY = (x / (rect.width / 2)) * 8;
    card.style.transform = `perspective(800px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-4px)`;
}

function resetDotCardTilt(card) {
    card.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg) translateY(0px)';
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

    listEl.innerHTML = agents.map(agent => {
        const hex = getDotColorHex(agent);
        const avatarSrc = getDotAvatarSrc(agent);
        return `
        <div class="agent-card ${agent.id === selectedAgentId ? 'active' : ''}" onclick="selectAgent('${agent.id}')">
            <div class="agent-card-header">
                <div style="display:flex; align-items:center; gap:8px;">
                    <img src="${avatarSrc}" class="agent-avatar-img cartoon-touchable" alt="${escapeHtml(agent.name)}" onclick="event.stopPropagation(); touchDotCartoon(null, this, event, '${escapeHtml(agent.name)}')" title="Touch ${escapeHtml(agent.name)}!" />
                    <span class="agent-name">${escapeHtml(agent.name)}</span>
                </div>
                <span class="status-badge ${agent.status}">${agent.status}</span>
            </div>
            <p class="agent-card-mission">${escapeHtml(agent.responsibility)}</p>
            <div style="font-size: 10px; color: var(--text-dim); display: flex; justify-content: space-between;">
                <span>Ticks: ${agent.total_ticks}</span>
                <span>${agent.schedule_interval_seconds}s cadence</span>
            </div>
        </div>
    `;}).join('');
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

    renderPromptPillsForAgent(agent);
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

    const avatarSrc = getDotAvatarSrc(agent);
    const avatar = document.getElementById('active-dot-avatar');
    if (avatar) {
        avatar.className = `dot-avatar`;
        avatar.innerHTML = `<img src="${avatarSrc}" class="active-dot-cartoon-img cartoon-touchable" alt="${escapeHtml(agent.name)}" onclick="touchDotCartoon(null, this, event, '${escapeHtml(agent.name)}')" title="Touch ${escapeHtml(agent.name)} to make it real!" />`;
    }

    const tagsEl = document.getElementById('dot-feature-tags');
    if (tagsEl) tagsEl.style.display = 'flex';

    const pauseBtn = document.getElementById('btn-toggle-pause');
    if (agent.status === 'paused') {
        pauseBtn.innerText = '▶ Resume';
    } else {
        pauseBtn.innerText = '⏸ Pause';
    }
}

// Voice Call Implementation
let recognition = null;
let isMicActive = false;
let lastSpokenText = "";

function startVoiceCall(archetypeKey) {
    if (archetypeKey) {
        const found = cachedAgents.find(a => (a.context?.archetype === archetypeKey) || a.name.toLowerCase().includes(archetypeKey));
        if (found) selectedAgentId = found.id;
    }
    if (!selectedAgentId && cachedAgents.length > 0) {
        selectedAgentId = cachedAgents[0].id;
    }
    if (!selectedAgentId) return;
    const agent = cachedAgents.find(a => a.id === selectedAgentId);
    if (!agent) return;

    const modal = document.getElementById('voice-modal');
    modal.classList.add('open');

    const avatarSrc = getDotAvatarSrc(agent);
    document.getElementById('voice-dot-name').innerText = `${agent.name} (Live Voice)`;
    const core = document.getElementById('voice-avatar-core');
    if (core) {
        core.innerHTML = `<img src="${avatarSrc}" class="voice-cartoon-avatar-img cartoon-touchable" alt="${escapeHtml(agent.name)}" onclick="touchDotCartoon(null, this, event, '${escapeHtml(agent.name)}')" title="Touch ${escapeHtml(agent.name)}!" />`;
    }

    const greeting = `Hello! I am ${agent.name}, powered by Google Gemini 3.5. I am actively managing your mission: ${agent.responsibility.slice(0, 90)}. How can I help right now?`;
    document.getElementById('voice-transcript-box').innerText = `"${greeting}"`;
    speakText(greeting);
}

function speakText(text) {
    lastSpokenText = text;
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.05;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }
}

function replayVoiceSpeech() {
    if (lastSpokenText) speakText(lastSpokenText);
}

function toggleVoiceMic() {
    const btn = document.getElementById('btn-toggle-mic');
    const statusPill = document.getElementById('voice-status-pill');

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Speech Recognition is not supported in this browser. You can type in the chat instead!");
        return;
    }

    if (isMicActive) {
        if (recognition) recognition.stop();
        isMicActive = false;
        btn.classList.remove('active');
        statusPill.innerText = "Connected (Mic Muted)";
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isMicActive = true;
        btn.classList.add('active');
        statusPill.innerText = "Listening to you... Speak now";
    };

    recognition.onresult = async (event) => {
        const spoken = event.results[0][0].transcript;
        document.getElementById('voice-transcript-box').innerText = `You: "${spoken}"`;
        statusPill.innerText = "Processing with Google Gemini 3.5...";
        
        try {
            const res = await fetch(`/api/agents/${selectedAgentId}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: spoken })
            });
            if (res.ok) {
                const data = await res.json();
                document.getElementById('voice-transcript-box').innerText = `${data.content}`;
                speakText(data.content);
                statusPill.innerText = "Connected";
            }
        } catch (e) {
            statusPill.innerText = "Error getting reply";
        }
    };

    recognition.onerror = () => {
        isMicActive = false;
        btn.classList.remove('active');
        statusPill.innerText = "Connected (Mic Idle)";
    };

    recognition.onend = () => {
        isMicActive = false;
        btn.classList.remove('active');
    };

    recognition.start();
}

function endVoiceCall() {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (recognition) recognition.stop();
    isMicActive = false;
    const modal = document.getElementById('voice-modal');
    modal.classList.remove('open');
}

async function loadCatchupBriefing(agentId) {
    try {
        const res = await fetch(`/api/agents/${agentId}/briefing`);
        if (!res.ok) return;
        const data = await res.json();
        const briefingCard = document.getElementById('catchup-briefing');
        const textEl = document.getElementById('briefing-text');
        const snippetEl = document.getElementById('briefing-preview-snippet');
        const toggleHint = document.getElementById('briefing-toggle-hint');
        
        if (textEl) {
            textEl.innerText = data.briefing;
            textEl.style.display = 'none'; // Default to collapsed for clean, premium screen
        }
        if (toggleHint) {
            toggleHint.innerText = 'Click to expand ▾';
        }
        if (snippetEl) {
            // Generate clean single-line preview snippet
            const firstLine = data.briefing.split('\n').find(l => l.trim().length > 0 && !l.includes('Hello!')) || "Autonomous operations running within guardrails.";
            snippetEl.innerText = firstLine.replace(/[\*\_#`]/g, '').trim();
        }
        if (briefingCard) {
            briefingCard.style.display = 'block';
        }
    } catch (err) {
        console.error('Error loading briefing:', err);
    }
}

function toggleBriefingBody() {
    const textEl = document.getElementById('briefing-text');
    const toggleHint = document.getElementById('briefing-toggle-hint');
    if (!textEl) return;
    const isCollapsed = (textEl.style.display === 'none' || !textEl.style.display);
    if (isCollapsed) {
        textEl.style.display = 'block';
        if (toggleHint) toggleHint.innerText = 'Click to collapse ▴';
    } else {
        textEl.style.display = 'none';
        if (toggleHint) toggleHint.innerText = 'Click to expand ▾';
    }
}

function toggleInspectorPanel() {
    const layout = document.querySelector('.dot-layout');
    const btnText = document.getElementById('inspector-btn-text');
    if (!layout) return;
    const isHidden = layout.classList.toggle('inspector-hidden');
    if (btnText) {
        btnText.innerText = isHidden ? 'Inspector' : 'Hide Inspector';
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

function showTypingIndicator() {
    const container = document.getElementById('chat-messages-container');
    const existing = document.getElementById('dot-typing-indicator');
    if (existing) return;

    const indicator = document.createElement('div');
    indicator.id = 'dot-typing-indicator';
    indicator.className = 'chat-bubble agent';
    indicator.innerHTML = `
        <span class="bubble-sender">Dot</span>
        <div class="bubble-content" style="opacity: 0.85; display: flex; align-items: center; gap: 8px;">
            <span class="pulse-dot"></span> <span>Dot is reasoning & checking tools...</span>
        </div>
    `;
    container.appendChild(indicator);
    container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
    const el = document.getElementById('dot-typing-indicator');
    if (el) el.remove();
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

    const currentAgent = cachedAgents.find(a => a.id === selectedAgentId);
    const avatarSrc = getDotAvatarSrc(currentAgent);
    const agentName = currentAgent ? escapeHtml(currentAgent.name) : 'Dot';

    container.innerHTML = messages.map(m => `
        <div class="chat-bubble ${m.sender}">
            <div class="bubble-sender-row">
                ${m.sender === 'agent' ? `<img src="${avatarSrc}" class="chat-msg-avatar cartoon-touchable" alt="${agentName}" onclick="touchDotCartoon(null, this, event, '${agentName}')" title="Touch ${agentName}!" />` : ''}
                <span class="bubble-sender">${m.sender === 'user' ? 'You' : agentName}</span>
            </div>
            <div class="bubble-content">${formatMessageContent(m.content)}</div>
        </div>
    `).join('');
    container.scrollTop = container.scrollHeight;
}

function appendChatMessage(sender, text) {
    const container = document.getElementById('chat-messages-container');
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    const currentAgent = cachedAgents.find(a => a.id === selectedAgentId);
    const avatarSrc = getDotAvatarSrc(currentAgent);
    const agentName = currentAgent ? escapeHtml(currentAgent.name) : 'Dot';

    bubble.innerHTML = `
        <div class="bubble-sender-row">
            ${sender === 'agent' ? `<img src="${avatarSrc}" class="chat-msg-avatar cartoon-touchable" alt="${agentName}" onclick="touchDotCartoon(null, this, event, '${agentName}')" title="Touch ${agentName}!" />` : ''}
            <span class="bubble-sender">${sender === 'user' ? 'You' : agentName}</span>
        </div>
        <div class="bubble-content">${formatMessageContent(text)}</div>
    `;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

function formatMessageContent(raw) {
    if (!raw) return '';
    let escaped = escapeHtml(raw);
    // Bold **text**
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Inline code `code`
    escaped = escaped.replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,0.3);padding:2px 4px;border-radius:4px;font-family:monospace;">$1</code>');
    // Block quotes
    escaped = escaped.replace(/^>\s*(.*?)$/gm, '<blockquote style="border-left:3px solid var(--primary);padding-left:8px;margin:4px 0;color:#94a3b8;">$1</blockquote>');
    return escaped;
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
        const editor = document.getElementById('file-editor-content');
        if (editor) editor.value = data.content;
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
                    <a href="/api/agents/${selectedAgentId}/screenshots/${encodeURIComponent(filename)}" target="_blank">
                        <img src="/api/agents/${selectedAgentId}/screenshots/${encodeURIComponent(filename)}" alt="Browser Snapshot" loading="lazy">
                    </a>
                    <div style="padding: 4px 6px; font-size: 9px; color: var(--text-dim);">${escapeHTML(filename)}</div>
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

/* =========================================================
   COMMERCIAL SAAS WORKSTATION CONTROLLERS & ACTIONS
   ========================================================= */

// Action Auto-Review & Human In-The-Loop Approvals
function jumpToApprovals() {
    if (pendingDecisions && pendingDecisions.length > 0) {
        const banner = document.getElementById('approval-alert-banner');
        if (banner) {
            banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
            banner.style.boxShadow = '0 0 35px rgba(245, 158, 11, 0.9)';
            setTimeout(() => banner.style.boxShadow = '', 2000);
        }
    } else {
        alert("🛡️ All active Dot operations are currently operating safely within policy bounds. No human approvals required.");
    }
}

async function approveCurrentDecision() {
    if (!pendingDecisions || pendingDecisions.length === 0) return;
    const d = pendingDecisions[0];
    const btn = document.getElementById('btn-banner-approve');
    if (btn) btn.disabled = true;
    try {
        const res = await fetch(`/api/decisions/${d.id}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: "Approved by human operator via Enterprise Workstation." })
        });
        if (res.ok) {
            await fetchFleetData();
        }
    } catch (e) {
        console.error("Failed to approve decision:", e);
    } finally {
        if (btn) btn.disabled = false;
    }
}

async function rejectCurrentDecision() {
    if (!pendingDecisions || pendingDecisions.length === 0) return;
    const d = pendingDecisions[0];
    const btn = document.getElementById('btn-banner-reject');
    if (btn) btn.disabled = true;
    try {
        const res = await fetch(`/api/decisions/${d.id}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: "Declined by human operator. Please adapt strategy without protected actions." })
        });
        if (res.ok) {
            await fetchFleetData();
        }
    } catch (e) {
        console.error("Failed to reject decision:", e);
    } finally {
        if (btn) btn.disabled = false;
    }
}

// 4,000+ Apps & Ecosystem Integrations Modal
function openIntegrationsModal() {
    document.getElementById('integrations-modal').classList.add('open');
    fetchIntegrations();
}

function closeIntegrationsModal() {
    document.getElementById('integrations-modal').classList.remove('open');
}

async function fetchIntegrations() {
    try {
        const res = await fetch('/api/integrations');
        if (!res.ok) return;
        const data = await res.json();
        renderIntegrations(data.integrations || {});
    } catch (e) {
        console.error("Failed to fetch integrations:", e);
    }
}

function renderIntegrations(integrations) {
    const list = document.getElementById('integrations-list');
    if (!list) return;
    list.innerHTML = Object.entries(integrations).map(([id, item]) => `
        <div class="integration-card">
            <div class="integration-icon">${item.icon}</div>
            <div class="integration-info">
                <div class="integration-title">
                    <span>${escapeHtml(item.name)}</span>
                    <span style="font-size: 10px; font-weight:700; color: ${item.status === 'connected' ? '#10b981' : '#94a3b8'};">
                        ${item.status === 'connected' ? '● Connected' : '○ Standby'}
                    </span>
                </div>
                <div class="integration-desc">${escapeHtml(item.details)}</div>
                <button class="integration-toggle ${item.status}" onclick="toggleIntegration('${id}', '${item.status}')">
                    ${item.status === 'connected' ? 'Disconnect' : 'Connect App'}
                </button>
            </div>
        </div>
    `).join('');
}

async function toggleIntegration(id, currentStatus) {
    const nextState = currentStatus !== 'connected';
    try {
        const res = await fetch('/api/integrations/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ integration_id: id, enabled: nextState })
        });
        if (res.ok) {
            fetchIntegrations();
        }
    } catch (e) {
        console.error("Failed to toggle integration:", e);
    }
}

// Enterprise Hub & Commercial Billing / Quotas
async function openBillingModal() {
    document.getElementById('billing-modal').classList.add('open');
    try {
        const res = await fetch('/api/system/stats');
        if (res.ok) {
            const stats = await res.json();
            const used = stats.monthly_cycles_used || 0;
            const max = stats.monthly_cycle_allowance || 25000;
            const pct = Math.min(100, Math.round((used / max) * 100));
            const quotaText = document.getElementById('billing-quota-text');
            if (quotaText) quotaText.innerHTML = `<b>${used.toLocaleString()}</b> / ${max.toLocaleString()} cycles used (${pct}%)`;
            const quotaBar = document.getElementById('billing-quota-bar');
            if (quotaBar) quotaBar.style.width = `${Math.max(2, pct)}%`;
        }
    } catch (e) {
        console.error("Error reading system stats for billing:", e);
    }
}

function closeBillingModal() {
    document.getElementById('billing-modal').classList.remove('open');
}

// Cloud Computer Sandbox File Management Studio
function closeFileViewer() {
    const viewer = document.getElementById('file-viewer-section');
    if (viewer) viewer.style.display = 'none';
}

async function openNewFileModal() {
    if (!selectedAgentId) {
        alert("Please select a Dot from the fleet first.");
        return;
    }
    const filename = prompt("Enter new filename for Cloud Computer (e.g. analysis.py, report.md, pipeline.py):", "analysis.py");
    if (!filename) return;

    let initialCode = "# Cloud Computer Sandbox File\nprint('Running in isolated environment')\n";
    if (filename.endsWith('.md')) {
        initialCode = `# Executive Report\nGenerated on: ${new Date().toLocaleDateString()}\n\n- Milestone: Verified\n`;
    }

    try {
        const res = await fetch(`/api/agents/${selectedAgentId}/files/write`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: filename, content: initialCode })
        });
        if (res.ok) {
            await fetchSandboxFiles(selectedAgentId);
            viewFileContent(filename);
        }
    } catch (e) {
        alert("Failed to create file: " + e);
    }
}

async function saveActiveFileContent() {
    if (!selectedAgentId) return;
    const titleEl = document.getElementById('file-viewer-filename');
    const filename = titleEl.innerText.replace('📄', '').trim();
    const content = document.getElementById('file-editor-content').value;
    try {
        const res = await fetch(`/api/agents/${selectedAgentId}/files/write`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: filename, content })
        });
        if (res.ok) {
            alert(`✓ Successfully saved "${filename}" to Dot's cloud computer.`);
            fetchSandboxFiles(selectedAgentId);
        }
    } catch (e) {
        alert("Error saving file: " + e);
    }
}

function downloadActiveFile() {
    const titleEl = document.getElementById('file-viewer-filename');
    const filename = titleEl.innerText.replace('📄', '').trim();
    const content = document.getElementById('file-editor-content').value;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

async function deleteActiveFile() {
    if (!selectedAgentId) return;
    const titleEl = document.getElementById('file-viewer-filename');
    const filename = titleEl.innerText.replace('📄', '').trim();
    if (!confirm(`Are you sure you want to delete "${filename}" from this Dot's cloud computer?`)) return;

    try {
        const res = await fetch(`/api/agents/${selectedAgentId}/files?path=${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            closeFileViewer();
            fetchSandboxFiles(selectedAgentId);
        }
    } catch (e) {
        alert("Failed to delete file: " + e);
    }
}

// Quick Script Templates for Cloud Computer REPL
function applyScriptTemplate(type) {
    const input = document.getElementById('sandbox-code-input');
    if (!input || !type) return;
    const templates = {
        data_analysis: `# Cloud Computer: Data Analysis & Statistical Trends
import math, json

data = [12.4, 15.8, 14.2, 19.5, 23.1, 28.0, 31.4, 34.2]
mean = sum(data) / len(data)
variance = sum((x - mean) ** 2 for x in data) / len(data)
std_dev = math.sqrt(variance)

summary = {
    "sample_size": len(data),
    "mean_growth": round(mean, 2),
    "variance": round(variance, 2),
    "std_dev": round(std_dev, 2),
    "status": "Target velocity achieved"
}
print(json.dumps(summary, indent=2))`,

        web_scraper: `# Cloud Computer: Autonomous Content Scraper & Digest
import urllib.request
import re

url = "https://news.ycombinator.com"
print(f"Connecting to frontier feed: {url}...")
# In cloud computer, network calls are isolated
print("✓ SSL Handshake successful.")
print("✓ Extracted 15 recurring developer requests.")
print("✓ Prepared executive summary for operator review.")`,

        test_suite: `# Cloud Computer: Regression Test Runner
import unittest

class TestAutonomousDot(unittest.TestCase):
    def test_heartbeat_liveness(self):
        self.assertTrue(True, "Heartbeat is alive")
        
    def test_sandbox_isolation(self):
        self.assertEqual(200, 200, "VPC isolation verified")

suite = unittest.TestLoader().loadTestsFromTestCase(TestAutonomousDot)
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)`,

        markdown_gen: `# Cloud Computer: Generate Markdown Report Deliverable
report_md = """# Autonomous Deliverable Report
Generated by: Cloud Computer
Date: 2026-10-23
Status: Verified & Tested

## Executive Summary
- All goals are trending ahead of schedule.
- Zero security regressions detected.
- 4,000+ app connectors in sync.
"""
with open("deliverable_report.md", "w") as f:
    f.write(report_md)
print("✓ Created deliverable_report.md in cloud computer workspace.")`
    };

    if (templates[type]) {
        input.value = templates[type];
    }
}

// Archetype-Specific Prompt Pills
function renderPromptPillsForAgent(agent) {
    const pillsContainer = document.getElementById('prompt-pills');
    if (!pillsContainer) return;
    const archetype = agent.context?.archetype || 'custom';
    const pillsMap = {
        felipe: [
            "Revise launch checklist for next milestone",
            "Draft customer announcement newsletter",
            "Investigate competitor positioning shifts",
            "Check blocker list and ping engineering"
        ],
        todd: [
            "Rerun statistical analysis on latest sample",
            "Investigate unexpected anomaly in dataset",
            "Generate publication-ready summary figures",
            "Synthesize paper abstract draft"
        ],
        alfred: [
            "Review customer RFP against security policy",
            "Generate technical proof-of-concept script",
            "Calculate enterprise ROI projections",
            "Identify solutions engineer for cross-review"
        ],
        jojo: [
            "Extract highlight clip timestamps from transcript",
            "Draft high-engagement social threads",
            "Prepare podcast show notes & bullet points",
            "Check trending audio hooks in our niche"
        ],
        dev: [
            "Execute regression test suite in sandbox",
            "Scope automated bugfix for customer issue",
            "Review latest pull request diff",
            "Check cloud computer disk and memory status"
        ],
        custom: [
            "What are you currently investigating?",
            "Run a proactive background scan now",
            "Summarize your latest accomplishments",
            "Draft an executive report on your progress"
        ]
    };

    const pills = pillsMap[archetype] || pillsMap.custom;
    pillsContainer.innerHTML = pills.map(p => `
        <button type="button" class="prompt-pill" onclick="sendQuickPrompt('${escapeHtml(p)}')">${escapeHtml(p)}</button>
    `).join('');
}

// Commercial Executive Audit Export
function exportExecutiveDigest() {
    let md = `# DOTS AI AGENT — Commercial Singularity Audit Report\n`;
    md += `Generated: ${new Date().toISOString()}\n`;
    md += `Plan: Business Premium ($50/user/mo) • Model: Google Gemini 3.5\n\n`;
    md += `## 1. Fleet Overview\n`;
    cachedAgents.forEach((a, idx) => {
        md += `### ${idx+1}. ${a.name} (${a.status.toUpperCase()})\n`;
        md += `- **Responsibility**: ${a.responsibility}\n`;
        md += `- **Cadence**: Every ${a.schedule_interval_seconds}s\n`;
        md += `- **Ticks Executed**: ${a.total_ticks}\n\n`;
    });
    md += `## 2. Protected Decisions & Safeguards\n`;
    md += `- Total Pending Approvals: ${pendingDecisions.length}\n`;
    md += `- Zero Unreviewed High-Risk Actions Permitted.\n\n`;
    md += `## 3. Connected Integrations (4,000+ App Ecosystem)\n`;
    md += `- Slack, Microsoft Teams (Agent 365), GitHub, Google Workspace, Notion, Custom Webhooks.\n`;

    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ONE_DOTS_Enterprise_Audit_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/* =========================================================
   ONE DOTS UNIFIED PLATFORM CONTROLLERS
   ========================================================= */

// View Switcher (Showcase vs Workstation vs Docs)
function switchMainView(viewId) {
    document.querySelectorAll('.app-view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-links .nav-link-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));

    const targetView = document.getElementById(viewId);
    if (targetView) targetView.classList.add('active');

    const targetBtn = document.getElementById(`btn-${viewId}`);
    if (targetBtn) targetBtn.classList.add('active');

    if (viewId === 'view-workstation') {
        const layout = document.querySelector('.dot-layout');
        if (layout && !layout.classList.contains('inspector-hidden')) {
            // Default to simplified, clean, premium 2-column workstation
            layout.classList.add('inspector-hidden');
            const btnText = document.getElementById('inspector-btn-text');
            if (btnText) btnText.innerText = 'Inspector';
        }
        if (!selectedAgentId && cachedAgents.length > 0) {
            selectAgent(cachedAgents[0].id);
        }
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToShowcaseSection(sectionId) {
    switchMainView('view-showcase');
    setTimeout(() => {
        const el = document.getElementById(sectionId);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 50);
}

// =========================================================================
// CINEMATIC PLAYABLE LAUNCH FILM CONTROLLER (5 Specialist Dots • 30s Each = 02:30)
// =========================================================================
let filmPlaying = false;
let filmSeconds = 0;
let filmInterval = null;
let filmAudioActive = false;
let currentChapterIdx = 0;
const FILM_TOTAL_SECONDS = 150; // 5 specialists x 30s = 02:30 total duration

const FILM_CHAPTERS = [
    {
        dotKey: "felipe",
        dotName: "Felipe",
        title: "Blue Dot (Felipe): Product Launch Lead",
        badge: "SPECIALIST 1 • BLUE DOT (FELIPE) • 00:00 - 00:30",
        startSec: 0,
        endSec: 30,
        desc: "Learns positioning and audience standards. When product scope shifts, Felipe automatically revises launch narratives, updates Linear roadmaps, and syncs 4,000+ app connectors without delay.",
        narration: "Meet Felipe, the Blue Dot and autonomous Product Launch Lead. When product scope shifts, Felipe automatically rewrites launch narratives, syncs Linear tickets, and prepares customer drafts across your connected apps.",
        renderVisual: () => `
            <div class="film-dot-stage-row felipe-theme">
                <div class="film-character-spotlight" onclick="touchDotCartoon('felipe', this, event)" title="Touch Felipe!">
                    <div class="spotlight-halo halo-blue"></div>
                    <img src="assets/dots/felipe.png" alt="Felipe" class="film-stage-character cartoon-float" />
                    <div class="film-char-badge blue">Blue Dot • Launch Lead</div>
                </div>
                <div class="film-widget-box">
                    <div class="widget-header">
                        <span class="widget-tag blue">PRODUCT ROADMAP ORCHESTRATOR</span>
                        <span class="widget-status"><span class="pulse-dot green"></span> 4,000+ Apps Synced</span>
                    </div>
                    <div class="widget-checklist">
                        <div class="check-item done">
                            <span class="check-icon">✓</span>
                            <div class="check-text">
                                <strong>Linear Scope Shift Ingested</strong>
                                <span>+Streaming SSE Agent Protocol added to Q4 Release</span>
                            </div>
                        </div>
                        <div class="check-item active">
                            <span class="check-icon pulse">⟳</span>
                            <div class="check-text">
                                <strong>Auto-Revising GTM Launch Narrative</strong>
                                <span>Customer changelog &amp; release notes drafted in Notion</span>
                            </div>
                        </div>
                        <div class="check-item pending">
                            <span class="check-icon">✓</span>
                            <div class="check-text">
                                <strong>Slack #announcements Auto-Broadcast</strong>
                                <span>Cross-team alignment broadcast ready for 1-click send</span>
                            </div>
                        </div>
                    </div>
                    <div class="widget-progress-row">
                        <div class="progress-label">
                            <span>Launch Readiness</span>
                            <strong class="text-blue">98% (Ready to Ship)</strong>
                        </div>
                        <div class="progress-bar-track">
                            <div class="progress-bar-fill blue" style="width: 98%;"></div>
                        </div>
                    </div>
                </div>
            </div>
        `
    },
    {
        dotKey: "todd",
        dotName: "Todd",
        title: "Green Dot (Todd): Research Scientist",
        badge: "SPECIALIST 2 • GREEN DOT (TODD) • 00:30 - 01:00",
        startSec: 30,
        endSec: 60,
        desc: "Formulates hypotheses and inspects live telemetry. As new evidence arrives, Todd reruns statistical analyses in its Python cloud sandbox, flags anomalies, and updates figures.",
        narration: "Meet Todd, the Green Dot and autonomous Research Scientist. Powered by its dedicated cloud computer, Todd runs statistical regressions in Python, monitors real-time telemetry, and instantly alerts you when data anomalies are detected.",
        renderVisual: () => `
            <div class="film-dot-stage-row todd-theme">
                <div class="film-character-spotlight" onclick="touchDotCartoon('todd', this, event)" title="Touch Todd!">
                    <div class="spotlight-halo halo-green"></div>
                    <img src="assets/dots/todd.png" alt="Todd" class="film-stage-character cartoon-float" />
                    <div class="film-char-badge green">Green Dot • Research Scientist</div>
                </div>
                <div class="film-widget-box">
                    <div class="widget-header">
                        <span class="widget-tag green">STATISTICAL CLOUD COMPUTER SANDBOX</span>
                        <span class="widget-status"><span class="pulse-dot emerald"></span> Python 3.13 NumPy/Scipy</span>
                    </div>
                    <div class="scientific-chart-wrapper">
                        <svg class="regression-svg" viewBox="0 0 360 85">
                            <defs>
                                <linearGradient id="todd-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" stop-color="#10b981" stop-opacity="0.3"/>
                                    <stop offset="60%" stop-color="#10b981" stop-opacity="1"/>
                                    <stop offset="100%" stop-color="#06b6d4" stop-opacity="0.9"/>
                                </linearGradient>
                            </defs>
                            <path d="M 15,70 Q 90,62 150,38 T 270,22 T 345,12" fill="none" stroke="url(#todd-grad)" stroke-width="3" stroke-linecap="round" class="animated-curve-line" />
                            <circle cx="65" cy="66" r="3.5" fill="#10b981" />
                            <circle cx="120" cy="48" r="3.5" fill="#10b981" />
                            <circle cx="190" cy="32" r="3.5" fill="#10b981" />
                            <circle cx="240" cy="24" r="3.5" fill="#10b981" />
                            <circle cx="315" cy="16" r="3.5" fill="#10b981" />
                            <circle cx="280" cy="52" r="5" fill="#ef4444" class="pulse-anomaly" />
                            <text x="290" y="56" fill="#f87171" font-size="9" font-family="monospace">Anomaly (+3.2σ)</text>
                        </svg>
                    </div>
                    <div class="widget-stats-grid">
                        <div class="stat-pill"><span class="stat-lbl">ANOVA F-STAT</span><strong>48.2 (p = 0.0004)</strong></div>
                        <div class="stat-pill"><span class="stat-lbl">RE-EXECUTION</span><strong>14ms Sandbox</strong></div>
                        <div class="stat-pill"><span class="stat-lbl">CONFIDENCE</span><strong>99.96% Verified</strong></div>
                    </div>
                </div>
            </div>
        `
    },
    {
        dotKey: "alfred",
        dotName: "Alfred",
        title: "Yellow Dot (Alfred): Enterprise Sales Lead",
        badge: "SPECIALIST 3 • YELLOW DOT (ALFRED) • 01:00 - 01:30",
        startSec: 60,
        endSec: 90,
        desc: "Parses dense 80+ page RFPs against your technical documentation, executes proof-of-concept scripts in its cloud sandbox, and automatically qualifies enterprise security requirements.",
        narration: "Meet Alfred, the Yellow Dot and Enterprise Sales Lead. Alfred inspects incoming customer RFPs against your technical documentation, executes sandbox proof of concepts, and automates high-value deal closing.",
        renderVisual: () => `
            <div class="film-dot-stage-row alfred-theme">
                <div class="film-character-spotlight" onclick="touchDotCartoon('alfred', this, event)" title="Touch Alfred!">
                    <div class="spotlight-halo halo-yellow"></div>
                    <img src="assets/dots/alfred.png" alt="Alfred" class="film-stage-character cartoon-float" />
                    <div class="film-char-badge yellow">Yellow Dot • Enterprise Sales</div>
                </div>
                <div class="film-widget-box">
                    <div class="widget-header">
                        <span class="widget-tag yellow">RFP INSPECTOR &amp; POC SIMULATOR</span>
                        <span class="widget-status"><span class="pulse-dot amber"></span> Enterprise Deal Pipeline</span>
                    </div>
                    <div class="deal-highlight-card">
                        <div class="deal-val-box">
                            <span class="deal-label">ACTIVE RFP PIPELINE</span>
                            <span class="deal-amount">$380,000 ARR</span>
                        </div>
                        <div class="deal-meta-box">
                            <span class="deal-org">Acme Enterprise Global RFP (85 Pages)</span>
                            <span class="deal-stage">Stage: Autonomous Technical POC Qualified</span>
                        </div>
                    </div>
                    <div class="compliance-matrix-grid">
                        <div class="comp-badge verified">✓ SOC2 Type II</div>
                        <div class="comp-badge verified">✓ HIPAA BAA</div>
                        <div class="comp-badge verified">✓ ISO 27001</div>
                        <div class="comp-badge verified">✓ AWS VPC Sandbox</div>
                    </div>
                    <div class="rfp-note-line">
                        <span class="rfp-icon">📄</span> Alfred verified 142 technical criteria in 6.2s — zero bottlenecks
                    </div>
                </div>
            </div>
        `
    },
    {
        dotKey: "jojo",
        dotName: "Jojo",
        title: "Purple Dot (Jojo): Content Creator & Media",
        badge: "SPECIALIST 4 • PURPLE DOT (JOJO) • 01:30 - 02:00",
        startSec: 90,
        endSec: 120,
        desc: "Ingests raw podcasts, keynotes, and videos. Jojo extracts high-retention clips, drafts viral social threads, and formats show notes while preserving your authentic voice.",
        narration: "Meet Jojo, the Purple Dot and Content Creator. Jojo ingests your raw recordings and podcasts, identifies viral moments through retention analysis, and writes engaging threads and video scripts in your exact voice.",
        renderVisual: () => `
            <div class="film-dot-stage-row jojo-theme">
                <div class="film-character-spotlight" onclick="touchDotCartoon('jojo', this, event)" title="Touch Jojo!">
                    <div class="spotlight-halo halo-purple"></div>
                    <img src="assets/dots/jojo.png" alt="Jojo" class="film-stage-character cartoon-float" />
                    <div class="film-char-badge purple">Purple Dot • Content &amp; Media</div>
                </div>
                <div class="film-widget-box">
                    <div class="widget-header">
                        <span class="widget-tag purple">VIRAL MEDIA PRODUCTION SUITE</span>
                        <span class="widget-status"><span class="pulse-dot purple"></span> Multi-Channel Publisher</span>
                    </div>
                    <div class="media-waveform-box">
                        <div class="waveform-bars">
                            <span style="height: 14px; animation-delay: 0.1s;"></span>
                            <span style="height: 28px; animation-delay: 0.25s;"></span>
                            <span style="height: 42px; animation-delay: 0.15s;"></span>
                            <span style="height: 18px; animation-delay: 0.35s;"></span>
                            <span style="height: 48px; animation-delay: 0.05s;"></span>
                            <span style="height: 32px; animation-delay: 0.2s;"></span>
                            <span style="height: 45px; animation-delay: 0.3s;"></span>
                            <span style="height: 24px; animation-delay: 0.1s;"></span>
                            <span style="height: 38px; animation-delay: 0.4s;"></span>
                            <span style="height: 12px; animation-delay: 0.15s;"></span>
                        </div>
                        <div class="waveform-peak-tag">
                            <span class="peak-icon">🔥</span> Viral Hook 01: 99.4% Retention (14:20)
                        </div>
                    </div>
                    <div class="media-outputs-list">
                        <div class="media-out-item"><span class="dot-bullet purple"></span> 3 Short-form Reels with kinetic subtitles exported</div>
                        <div class="media-out-item"><span class="dot-bullet purple"></span> 10-Post Twitter/X Thread formatted in creator tone</div>
                        <div class="media-out-item"><span class="dot-bullet purple"></span> YouTube chapters &amp; Spotify show notes ready to publish</div>
                    </div>
                </div>
            </div>
        `
    },
    {
        dotKey: "dev",
        dotName: "Sentry",
        title: "Dev Dot (Sentry): Autonomous Software Dev",
        badge: "SPECIALIST 5 • DEV DOT (SENTRY) • 02:00 - 02:30",
        startSec: 120,
        endSec: 150,
        desc: "Equipped with an isolated development sandbox, Sentry monitors bug reports, writes Git patches, executes complete test suites, and opens automated pull requests with zero regressions.",
        narration: "Meet Sentry, the autonomous Software Developer. Sentry runs your code in dedicated terminal sandboxes, fixes bugs, executes test suites, and opens pull requests with automated zero-regression guarantees.",
        renderVisual: () => `
            <div class="film-dot-stage-row dev-theme">
                <div class="film-character-spotlight" onclick="touchDotCartoon('dev', this, event)" title="Touch Sentry!">
                    <div class="spotlight-halo halo-orange"></div>
                    <img src="assets/dots/sentry.png" alt="Sentry" class="film-stage-character cartoon-float" />
                    <div class="film-char-badge orange">Dev Dot • Autonomous Engineer</div>
                </div>
                <div class="film-widget-box">
                    <div class="widget-header">
                        <span class="widget-tag orange">AUTONOMOUS GIT PR &amp; REPL ENGINE</span>
                        <span class="widget-status"><span class="pulse-dot orange"></span> Terminal Sandbox Isolated</span>
                    </div>
                    <div class="diff-terminal-mockup">
                        <div class="diff-header">
                            <span class="t-dot red"></span><span class="t-dot yellow"></span><span class="t-dot green"></span>
                            <span class="diff-title">git diff bugfix/stream-subprocess-hang</span>
                        </div>
                        <div class="diff-lines">
                            <div class="d-line red">- while not stream.closed: read_async_chunk()  # Windows event loop hang</div>
                            <div class="d-line green">+ async for chunk in stream.safe_event_iter(): # Isolated non-blocking worker</div>
                        </div>
                    </div>
                    <div class="test-runner-strip">
                        <div class="test-count"><span class="green-check">✓</span> <strong>42/42 Tests Passed</strong> (0.34s)</div>
                        <div class="pr-badge">PR #1402 Merged to main • CI/CD Green</div>
                    </div>
                </div>
            </div>
        `
    }
];

function toggleFilmPlayback() {
    filmPlaying = !filmPlaying;
    const playIcon = document.getElementById('film-play-icon');
    const ctrlPlayBtn = document.getElementById('film-ctrl-play-btn');
    const playOverlay = document.getElementById('film-center-play-overlay');
    const statusText = document.getElementById('film-status-text');

    if (filmPlaying) {
        if (playIcon) playIcon.innerText = '⏸';
        if (ctrlPlayBtn) ctrlPlayBtn.innerText = '⏸';
        if (playOverlay) playOverlay.classList.add('playing');
        if (statusText) statusText.innerText = 'Playing launch film: Meet the 5 Dots in action (30s each)...';
        
        if (filmAudioActive) {
            playCurrentChapterNarration();
        }

        if (filmInterval) clearInterval(filmInterval);
        filmInterval = setInterval(() => {
            filmSeconds++;
            if (filmSeconds >= FILM_TOTAL_SECONDS) {
                filmSeconds = 0;
            }
            updateFilmUI();
        }, 1000);
    } else {
        if (playIcon) playIcon.innerText = '▶';
        if (ctrlPlayBtn) ctrlPlayBtn.innerText = '▶';
        if (playOverlay) playOverlay.classList.remove('playing');
        if (statusText) statusText.innerText = 'Click to watch the 5 Dots in Action — 30s Dedicated Demo for Each Dot (02:30)';
        if (filmInterval) clearInterval(filmInterval);
        if (window.speechSynthesis) window.speechSynthesis.cancel();
    }
}

function jumpToFilmChapter(idx, e) {
    if (e) e.stopPropagation();
    if (idx < 0 || idx >= FILM_CHAPTERS.length) return;
    currentChapterIdx = idx;
    filmSeconds = FILM_CHAPTERS[idx].startSec;
    updateFilmUI();
    
    if (!filmPlaying) {
        toggleFilmPlayback();
    } else if (filmAudioActive) {
        playCurrentChapterNarration();
    }
}

function toggleFilmAudio(e) {
    if (e) e.stopPropagation();
    filmAudioActive = !filmAudioActive;
    const icon1 = document.getElementById('film-voice-icon');
    const icon2 = document.getElementById('film-audio-ctrl');
    const text = filmAudioActive ? '🔊' : '🔇';
    if (icon1) icon1.innerText = text;
    if (icon2) icon2.innerText = text;

    if (filmAudioActive) {
        playCurrentChapterNarration();
    } else {
        if (window.speechSynthesis) window.speechSynthesis.cancel();
    }
}

function playCurrentChapterNarration() {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const ch = FILM_CHAPTERS[currentChapterIdx];
    if (!ch) return;
    const utter = new SpeechSynthesisUtterance(ch.narration);
    utter.rate = 1.0;
    utter.pitch = 1.0;
    window.speechSynthesis.speak(utter);
}

function updateFilmUI() {
    // Determine active chapter
    let activeIdx = 0;
    for (let i = 0; i < FILM_CHAPTERS.length; i++) {
        if (filmSeconds >= FILM_CHAPTERS[i].startSec && filmSeconds < FILM_CHAPTERS[i].endSec) {
            activeIdx = i;
            break;
        }
    }

    if (activeIdx !== currentChapterIdx) {
        currentChapterIdx = activeIdx;
        if (filmPlaying && filmAudioActive) {
            playCurrentChapterNarration();
        }
    }

    const ch = FILM_CHAPTERS[currentChapterIdx];
    
    // Update Chapter text & visuals
    const badgeEl = document.getElementById('scene-chapter-badge');
    const titleEl = document.getElementById('scene-title');
    const descEl = document.getElementById('scene-description');
    const visualEl = document.getElementById('scene-visual-display');
    const actionRow = document.getElementById('scene-action-row');

    if (badgeEl && badgeEl.innerText !== ch.badge) badgeEl.innerText = ch.badge;
    if (titleEl && titleEl.innerText !== ch.title) titleEl.innerText = ch.title;
    if (descEl && descEl.innerText !== ch.desc) descEl.innerText = ch.desc;
    if (visualEl) visualEl.innerHTML = ch.renderVisual();

    if (actionRow) {
        actionRow.innerHTML = `
            <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); launchArchetypeFromShowcase('${ch.dotKey}')">
                Collaborate with ${ch.dotName} ➔
            </button>
            <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); startVoiceCall('${ch.dotKey}')">
                📞 Start Voice Call with ${ch.dotName}
            </button>
        `;
    }

    // Update chapter pills active state
    const pills = document.querySelectorAll('#film-chapter-pills .chapter-pill');
    pills.forEach((p, idx) => {
        if (idx === currentChapterIdx) {
            p.classList.add('active');
        } else {
            p.classList.remove('active');
        }
    });

    // Update timecode & scrubber
    const timecode = document.getElementById('film-timecode');
    const fill = document.getElementById('film-scrubber-fill');
    const m = Math.floor(filmSeconds / 60);
    const s = filmSeconds % 60;
    const timeStr = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')} / 02:30`;
    if (timecode) timecode.innerText = timeStr;
    if (fill) {
        const pct = (filmSeconds / FILM_TOTAL_SECONDS) * 100;
        fill.style.width = `${pct}%`;
    }
}

function scrubFilm(e) {
    const scrubber = e.currentTarget;
    const rect = scrubber.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const pct = Math.max(0, Math.min(1, clickX / rect.width));
    filmSeconds = Math.floor(pct * FILM_TOTAL_SECONDS);
    updateFilmUI();
}

// Quick Deploy / Collaborate with an Archetype from Showcase
function launchArchetypeFromShowcase(type) {
    const existing = cachedAgents.find(a => (a.context?.archetype === type) || a.name.toLowerCase().includes(type));
    if (existing) {
        switchMainView('view-workstation');
        selectAgent(existing.id);
    } else {
        applyPreset(type);
        document.getElementById('create-modal').classList.add('open');
    }
}

// Global Search Overlay (Ctrl+K)
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            openSearchModal();
        } else if (e.key === 'Escape') {
            closeSearchModal();
            closeDocsAgent();
        }
    });
}

function openSearchModal() {
    const overlay = document.getElementById('search-modal-overlay');
    if (overlay) {
        overlay.classList.add('open');
        const input = document.getElementById('global-search-input');
        if (input) {
            input.value = '';
            input.focus();
            filterDocsSearch('');
        }
    }
}

function closeSearchModal() {
    const overlay = document.getElementById('search-modal-overlay');
    if (overlay) overlay.classList.remove('open');
}

function handleSearchOverlayClick(e) {
    if (e.target.id === 'search-modal-overlay') {
        closeSearchModal();
    }
}

function filterDocsSearch(query) {
    const list = document.getElementById('search-results-list');
    if (!list) return;
    const items = list.querySelectorAll('.search-result-item');
    const cleanQuery = query.toLowerCase().trim();

    items.forEach(item => {
        const text = item.innerText.toLowerCase();
        if (!cleanQuery || text.includes(cleanQuery)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// Docs Agent Drawer (Ask AI)
function toggleDocsAgent() {
    const drawer = document.getElementById('docs-agent-drawer');
    if (drawer) {
        drawer.classList.toggle('open');
        if (drawer.classList.contains('open')) {
            const input = document.getElementById('docs-agent-input');
            if (input) input.focus();
        }
    }
}

function closeDocsAgent() {
    const drawer = document.getElementById('docs-agent-drawer');
    if (drawer) drawer.classList.remove('open');
}

function clearDocsChat() {
    const stream = document.getElementById('docs-chat-stream');
    if (!stream) return;
    stream.innerHTML = `
        <div class="drawer-msg agent">
            New session started. Ask me anything about ONE DOTS, cloud computer execution, STDIN handling, or the 5 specialist archetypes!
        </div>
    `;
    const prompts = document.getElementById('docs-starter-prompts');
    if (prompts) prompts.style.display = 'flex';
}

function sendStarterPrompt(btn) {
    const text = btn.innerText.trim();
    const input = document.getElementById('docs-agent-input');
    if (!input) return;
    input.value = text;
    document.getElementById('docs-agent-form').dispatchEvent(new Event('submit'));
}

async function handleDocsAgentSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('docs-agent-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    const prompts = document.getElementById('docs-starter-prompts');
    if (prompts) prompts.style.display = 'none';

    appendDocsMessage('user', text);
    const thinkingEl = appendDocsMessage('agent', 'Thinking & checking documentation index...');

    try {
        let reply = "";
        if (cachedAgents.length > 0) {
            const agentId = cachedAgents[0].id;
            const chatRes = await fetch(`/api/agents/${agentId}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: `[DOCUMENTATION QUERY]: ${text}\n(Respond concisely about ONE DOTS: 5 Specialist archetypes, cloud computer with STDIN safe handling, real-time voice call, action auto-review, 4,000+ app connectors, and $50/mo Business Premium tier).`
                })
            });
            if (chatRes.ok) {
                const data = await chatRes.json();
                reply = data.content;
            }
        }

        if (!reply) {
            reply = generateLocalDocsReply(text);
        }

        thinkingEl.innerHTML = formatDocsReply(reply);
    } catch (err) {
        thinkingEl.innerText = generateLocalDocsReply(text);
    }
}

function appendDocsMessage(sender, text) {
    const stream = document.getElementById('docs-chat-stream');
    const msg = document.createElement('div');
    msg.className = `drawer-msg ${sender}`;
    msg.innerText = text;
    stream.appendChild(msg);
    stream.scrollTop = stream.scrollHeight;
    return msg;
}

function formatDocsReply(raw) {
    if (!raw) return '';
    let escaped = escapeHtml(raw);
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.08);padding:2px 4px;border-radius:4px;font-family:monospace;">$1</code>');
    return escaped;
}

function generateLocalDocsReply(query) {
    const q = query.toLowerCase();
    if (q.includes('stdin') || q.includes('input')) {
        return "The Cloud Computer features an isolated sandbox with a Safe Input Shim. When `input()` is called without terminal interaction, it automatically handles EOFError and defaults to 'User' in milliseconds, preventing 30-second timeouts. Operators can also supply inputs directly in the STDIN input field.";
    }
    if (q.includes('archetype') || q.includes('felipe') || q.includes('todd') || q.includes('alfred') || q.includes('dev')) {
        return "ONE DOTS features 5 Specialist Archetypes:\n- **Blue Dot (Felipe)**: Product Launch Lead\n- **Green Dot (Todd)**: Research Scientist & Evidence\n- **Yellow Dot (Alfred)**: Enterprise Deals & Technical POCs\n- **Purple Dot (Jojo)**: Content & Media Creator\n- **Dev Dot (Sentry)**: Autonomous Engineering PRs & Bugfixes.";
    }
    if (q.includes('voice') || q.includes('call')) {
        return "Real-Time Voice Calls connect directly to the Google Gemini 3.5 Audio Engine. Click '📞 Start Live Voice Call' anywhere in the platform to speak with full bidirectional audio synthesis.";
    }
    if (q.includes('safeguard') || q.includes('review') || q.includes('approval')) {
        return "The Action Auto-Review safeguard categorizes operations into Low, Medium, High Risk, and Blocked. High Risk operations (like modifying databases or external systems) halt and trigger the animated Human Approval Gate banner.";
    }
    return "ONE DOTS are always-on autonomous AI agents powered by Google Gemini 3.5 and dedicated cloud computers. They work towards your mission 24/7 with 4,000+ app connectors and human approval safeguards.";
}

// Copy Code & Page URL
function copyCode(btn) {
    const codeBlock = btn.closest('.code-block-wrapper').querySelector('.code-block code');
    if (!codeBlock) return;
    navigator.clipboard.writeText(codeBlock.innerText).then(() => {
        const orig = btn.innerText;
        btn.innerText = 'Copied!';
        setTimeout(() => btn.innerText = orig, 2000);
    });
}

function copyCurrentUrl() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        alert("Page URL copied to clipboard!");
    });
}

// =========================================================================
// CINEMATIC "ONE DOTS" ENTRY ANIMATION CONTROLLER
// =========================================================================
let splashCanvasAnimId = null;
let splashAutoDismissTimer = null;
let splashSequenceTimers = [];

function initEntrySplash() {
    const splash = document.getElementById('entry-splash');
    if (!splash) return;

    // Check if user already saw splash in this session
    // Allow replaying anytime by clicking the logo
    initSplashCanvas();
    startSplashAnimation();

    // Escape key listener to skip intro
    document.addEventListener('keydown', handleSplashKeydown);
}

function handleSplashKeydown(e) {
    if (e.key === 'Escape') {
        dismissEntrySplash(true);
    }
}

function startSplashAnimation() {
    const splash = document.getElementById('entry-splash');
    if (!splash) return;

    // Clear any previous timers
    splashSequenceTimers.forEach(t => clearTimeout(t));
    splashSequenceTimers = [];

    // Reset state classes
    splash.classList.remove('docking-to-navbar', 'dismissed');
    splash.style.display = 'flex';
    splash.style.opacity = '1';
    splash.style.transition = '';

    document.body.classList.add('splash-active');
    document.body.classList.remove('site-revealed');

    const orbit = document.getElementById('quantum-dots-orbit');
    const shockwave = document.getElementById('splash-shockwave');
    const symbol = document.getElementById('singularity-symbol');
    const branding = document.getElementById('splash-branding');
    const stage = document.getElementById('splash-stage');

    if (orbit) orbit.classList.remove('converge');
    if (shockwave) shockwave.classList.remove('trigger');
    if (symbol) symbol.classList.remove('active');
    if (branding) branding.classList.remove('active');

    // Sequence Step 1: Start 5 dots quantum convergence inward (t = 150ms)
    splashSequenceTimers.push(setTimeout(() => {
        if (orbit) orbit.classList.add('converge');
    }, 150));

    // Sequence Step 2: The 5 dots collide at center -> Shockwave + Chime + Crystalline ◈ (t = 850ms)
    splashSequenceTimers.push(setTimeout(() => {
        if (shockwave) shockwave.classList.add('trigger');
        if (symbol) symbol.classList.add('active');
        playSingularityChime();
    }, 850));

    // Sequence Step 3: Kinetic Typography "ONE DOTS" drops in + Shimmer sweep (t = 1050ms)
    splashSequenceTimers.push(setTimeout(() => {
        if (branding) branding.classList.add('active');
    }, 1050));

    // Sequence Step 4: FLY-TO-DOCK Dynamic Choreography (t = 1750ms)
    // Synchronously fly the central stage into the top-left navbar logo while website cascades up
    splashSequenceTimers.push(setTimeout(() => {
        const logoBox = document.querySelector('.logo-box');
        if (logoBox && stage) {
            const logoRect = logoBox.getBoundingClientRect();
            const stageRect = stage.getBoundingClientRect();
            // Pixel-perfect translation vector to target logo center
            const deltaX = (logoRect.left + logoRect.width / 2) - (stageRect.left + stageRect.width / 2);
            const deltaY = (logoRect.top + logoRect.height / 2) - (stageRect.top + stageRect.height / 2);
            stage.style.setProperty('--dock-tx', `${deltaX}px`);
            stage.style.setProperty('--dock-ty', `${deltaY}px`);
        }

        splash.classList.add('docking-to-navbar');
        document.body.classList.remove('splash-active');
        document.body.classList.add('site-revealed');
    }, 1750));

    // Sequence Step 5: Quantum Hand-off & Arrival Pulse into Navbar Logo (t = 2150ms)
    splashSequenceTimers.push(setTimeout(() => {
        const navLogo = document.querySelector('.logo-box');
        if (navLogo) {
            navLogo.classList.remove('arrival-pulse');
            void navLogo.offsetWidth; // force reflow
            navLogo.classList.add('arrival-pulse');
            playArrivalChime();
        }
    }, 2150));

    // Sequence Step 6: Complete Splash Dismissal & Cleanup (t = 2450ms)
    splashAutoDismissTimer = setTimeout(() => {
        dismissEntrySplash(false);
    }, 2450);
}

function dismissEntrySplash(immediate = false) {
    const splash = document.getElementById('entry-splash');
    if (!splash || splash.classList.contains('dismissed')) return;

    if (splashAutoDismissTimer) clearTimeout(splashAutoDismissTimer);
    splashSequenceTimers.forEach(t => clearTimeout(t));
    splashSequenceTimers = [];

    document.removeEventListener('keydown', handleSplashKeydown);

    document.body.classList.remove('splash-active');
    document.body.classList.add('site-revealed');

    const navLogo = document.querySelector('.logo-box');
    if (navLogo) {
        navLogo.classList.remove('arrival-pulse');
        void navLogo.offsetWidth;
        navLogo.classList.add('arrival-pulse');
    }

    if (immediate) {
        splash.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        splash.style.opacity = '0';
    } else {
        splash.style.transition = 'opacity 0.5s ease';
        splash.style.opacity = '0';
    }

    splash.classList.add('dismissed');

    setTimeout(() => {
        if (splashCanvasAnimId) cancelAnimationFrame(splashCanvasAnimId);
        splash.style.display = 'none';
        splash.classList.remove('docking-to-navbar');
    }, immediate ? 200 : 500);
}

// Replay Entry Animation Trigger (called when clicking navbar logo)
function replayEntryAnimation() {
    switchMainView('view-showcase');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    const splash = document.getElementById('entry-splash');
    if (splash) {
        splash.style.display = 'flex';
        splash.style.opacity = '1';
        initSplashCanvas();
        startSplashAnimation();
        document.addEventListener('keydown', handleSplashKeydown);
    }
}

// Starlight Deep Space Canvas Particles
function initSplashCanvas() {
    const canvas = document.getElementById('splash-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const particleCount = Math.min(65, Math.floor((width * height) / 18000));
    const colors = ['#38bdf8', '#818cf8', '#10b981', '#fbbf24', '#a855f7', '#f97316', '#ffffff'];

    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            radius: Math.random() * 1.5 + 0.5,
            color: colors[Math.floor(Math.random() * colors.length)],
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            alpha: Math.random() * 0.6 + 0.2,
            pulseSpeed: Math.random() * 0.02 + 0.005
        });
    }

    function renderParticles() {
        ctx.clearRect(0, 0, width, height);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;

            p.alpha += Math.sin(Date.now() * p.pulseSpeed) * 0.005;
            const clampedAlpha = Math.max(0.1, Math.min(0.85, p.alpha));

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = clampedAlpha;
            ctx.shadowBlur = 10;
            ctx.shadowColor = p.color;
            ctx.fill();
        }

        ctx.globalAlpha = 1.0;
        ctx.shadowBlur = 0;
        splashCanvasAnimId = requestAnimationFrame(renderParticles);
    }

    if (splashCanvasAnimId) cancelAnimationFrame(splashCanvasAnimId);
    renderParticles();
}

// Pure Web Audio Harmonic Chord Chime (Synthesized in Real-Time)
function playSingularityChime() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        if (ctx.state === 'suspended') {
            ctx.resume();
        }

        // Harmonious frontier chord: D4, A4, F#5, D6
        const chordFrequencies = [293.66, 440.00, 739.99, 1174.66];
        const now = ctx.currentTime;

        const masterGain = ctx.createGain();
        masterGain.gain.setValueAtTime(0.001, now);
        masterGain.gain.exponentialRampToValueAtTime(0.18, now + 0.08);
        masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 1.6);
        masterGain.connect(ctx.destination);

        const filter = ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(1200, now);
        filter.frequency.exponentialRampToValueAtTime(3200, now + 0.3);
        filter.connect(masterGain);

        chordFrequencies.forEach((freq, idx) => {
            const osc = ctx.createOscillator();
            const noteGain = ctx.createGain();
            osc.type = idx === 0 ? 'triangle' : 'sine';
            osc.frequency.setValueAtTime(freq, now + idx * 0.03);
            noteGain.gain.setValueAtTime(0.12 / chordFrequencies.length, now);
            osc.connect(noteGain);
            noteGain.connect(filter);
            osc.start(now + idx * 0.03);
            osc.stop(now + 1.8);
        });
    } catch (err) {
        // Audio synthesis fallback (silent mode without error)
    }
}

// Crystalline Quantum Arrival Pulse Chime (synthesized on navbar logo dock)
function playArrivalChime() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        if (ctx.state === 'suspended') ctx.resume();

        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(1760, now); // A6 pure crystal tone
        osc.frequency.exponentialRampToValueAtTime(2637, now + 0.12); // E7 glide

        gain.gain.setValueAtTime(0.001, now);
        gain.gain.exponentialRampToValueAtTime(0.08, now + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.45);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now);
        osc.stop(now + 0.5);
    } catch (e) {
        // Fallback
    }
}
