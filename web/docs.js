/**
 * DOTS Learn Documentation Hub — Interactive Scripting
 * Exactly modeled on learn.chatgpt.com/docs
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initScrollSpy();
    initKeyboardShortcuts();
});

// Theme Management (Dark / Light)
function initTheme() {
    const savedTheme = localStorage.getItem('dots-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('dots-theme', next);
    updateThemeIcon(next);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.innerText = theme === 'dark' ? '☀️' : '🌙';
    }
}

// Copy Code Snippet
function copyCode(btn) {
    const codeBlock = btn.closest('.code-block-wrapper').querySelector('.code-block code');
    if (!codeBlock) return;
    const text = codeBlock.innerText;

    navigator.clipboard.writeText(text).then(() => {
        const originalText = btn.innerText;
        btn.innerText = 'Copied!';
        btn.style.color = '#10b981';
        setTimeout(() => {
            btn.innerText = originalText;
            btn.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy code:', err);
    });
}

// Copy Page URL
function copyCurrentUrl() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        const textEl = document.getElementById('copy-btn-text');
        const iconEl = document.getElementById('copy-btn-icon');
        if (textEl) textEl.innerText = 'Copied!';
        if (iconEl) iconEl.innerText = '✓';
        setTimeout(() => {
            if (textEl) textEl.innerText = 'Copy link';
            if (iconEl) iconEl.innerText = '📋';
        }, 2000);
    });
}

// Table of Contents Scroll-Spy
function initScrollSpy() {
    const sections = document.querySelectorAll('.doc-section, .doc-title, .docs-hero-card');
    const navLinks = document.querySelectorAll('.docs-toc-rail .toc-link');

    window.addEventListener('scroll', () => {
        let currentId = '';
        const scrollPosition = window.scrollY + 140;

        sections.forEach(section => {
            const top = section.offsetTop;
            const height = section.offsetHeight;
            if (scrollPosition >= top && scrollPosition < top + height) {
                currentId = section.getAttribute('id');
            }
        });

        if (currentId) {
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${currentId}`) {
                    link.classList.add('active');
                }
            });
        }
    });
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
let docsAgentThread = [];

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
    stream.innerHTML = `
        <div class="drawer-msg agent">
            New session started. Ask me anything about Dots, Cloud Computer execution, STDIN handling, or the 5 specialist archetypes!
        </div>
    `;
    const prompts = document.getElementById('docs-starter-prompts');
    if (prompts) prompts.style.display = 'flex';
}

function sendStarterPrompt(btn) {
    const text = btn.innerText.trim();
    const input = document.getElementById('docs-agent-input');
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
        // Query active agent or intelligent docs synthesis
        const agentsRes = await fetch('/api/agents');
        let reply = "";

        if (agentsRes.ok) {
            const agents = await agentsRes.json();
            if (agents.length > 0) {
                const agentId = agents[0].id;
                const chatRes = await fetch(`/api/agents/${agentId}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: `[DOCUMENTATION QUERY FROM USER]: ${text}\n(Please answer with direct knowledge of our DOTS platform: 5 Specialist archetypes, dedicated cloud computer with STDIN safe handling, real-time voice call, action auto-review, 4,000+ app connectors, and $50/mo Business Premium tier).`
                    })
                });
                if (chatRes.ok) {
                    const data = await chatRes.json();
                    reply = data.content;
                }
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
    let escaped = raw
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.08);padding:2px 4px;border-radius:4px;font-family:monospace;">$1</code>');
    return escaped;
}

function generateLocalDocsReply(query) {
    const q = query.toLowerCase();
    if (q.includes('stdin') || q.includes('input')) {
        return "The Cloud Computer features an isolated execution sandbox equipped with a Safe Input Shim. When `input()` is called without terminal interaction, it automatically handles EOFError and defaults to 'User' in milliseconds, preventing the 30-second timeout. Operators can also supply inputs directly in the STDIN input field.";
    }
    if (q.includes('archetype') || q.includes('felipe') || q.includes('todd') || q.includes('alfred') || q.includes('dev')) {
        return "DOTS features 5 Specialist Archetypes:\n- **Blue Dot (Felipe)**: Product Launch Lead\n- **Green Dot (Todd)**: Research Scientist & Evidence\n- **Yellow Dot (Alfred)**: Enterprise Deals & Technical POCs\n- **Purple Dot (Jojo)**: Content & Media Creator\n- **Dev Dot (Sentry)**: Autonomous Engineering PRs & Bugfixes.";
    }
    if (q.includes('voice') || q.includes('call')) {
        return "Real-Time Voice Calls connect directly to the Google Gemini 3.5 Audio Engine. Click '📞 Voice Call' in any Dot profile to begin speaking with full bidirectional audio synthesis.";
    }
    if (q.includes('safeguard') || q.includes('review') || q.includes('approval')) {
        return "The Action Auto-Review safeguard categorizes operations into Low, Medium, High Risk, and Blocked. High Risk operations (like modifying databases or external systems) halt and trigger the animated Human Approval Gate banner.";
    }
    return "DOTS are always-on autonomous AI agents powered by Google Gemini 3.5 and dedicated cloud computers. They work towards your mission 24/7 with 4,000+ app connectors and human approval safeguards.";
}
