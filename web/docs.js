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
                        message: `[DOCUMENTATION QUERY]: ${text}\n(Provide an accurate, detailed technical explanation answering this exact inquiry directly with deep knowledge of ONE DOTS systems, empirical algorithms, or software engineering).`
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

    if (q.includes('discovery') || q.includes('ineffable') || q.includes('silver') || q.includes('funsearch') || q.includes('bin packing') || q.includes('heuristic') || q.includes('rl')) {
        return "The **Ineffable Empirical Discovery Engine** implements David Silver's pure RL paradigm. It discovers novel algorithmic heuristics and mathematical invariants via autonomous trial-and-error without human demonstration data. Features include: 3 island mutation pools (Prompt Mutation, AST Crossover, Heuristic Synthesis), deterministic Python sandbox verifiers (1D Bin Packing, Range Query RMQ, and Prime Polynomial Invariants), and zero hallucinations guaranteed by objective reward thresholds (>0.9000).";
    }

    if (q.includes('tender') || q.includes('rfp') || q.includes('nit') || q.includes('bid') || q.includes('pwd') || q.includes('cpwd') || q.includes('nhai') || q.includes('dossier')) {
        return "The **AXIS Tender Intelligence & Bid Readiness Subsystem** automates public sector procurement auditing across Indian government bodies (Maha PWD, CPWD, NHAI). It ingests 100+ page NITs in seconds, calculates statutory Indian Bid Capacity using `(A * N * 2) - B`, audits financial turnover and banker solvency, cross-checks 15 authentic benchmarks, and exports executive Microsoft Word (.docx) Bid Readiness Dossiers.";
    }

    if (q.includes('dbms') || q.includes('database') || q.includes('sql') || q.includes('rdbms') || q.includes('nosql') || q.includes('acid')) {
        return "A **Database Management System (DBMS)** is specialized software that enables users and applications to create, protect, read, update, and manage structured collections of data.\n\n" +
               "### 🏛️ Core Concepts & Architecture\n" +
               "1. **Primary Functions**:\n" +
               "   - **Data Definition (DDL)**: Formulate schemas, tables, relationships, constraints, and indexes.\n" +
               "   - **Data Manipulation (DML)**: Insert, query, update, and filter records efficiently using SQL or query APIs.\n" +
               "   - **Concurrency Control & Locking**: Ensure multiple concurrent transactions read and write without data corruption.\n\n" +
               "2. **Major Categories of DBMS**:\n" +
               "   - **Relational (RDBMS)**: Structured tabular data with foreign keys and strict schema adherence (*PostgreSQL, MySQL, SQLite, Oracle*).\n" +
               "   - **NoSQL / Document Stores**: Schema-flexible JSON documents optimized for horizontal scaling (*MongoDB, CouchDB, DynamoDB*).\n" +
               "   - **In-Memory & Caching**: Ultra-low-latency key-value stores (*Redis, Memcached*).\n" +
               "   - **Vector Databases**: High-dimensional vector indexers for AI episodic memory & semantic search (*sqlite-vec, ChromaDB, Pinecone*).\n\n" +
               "3. **The ACID Guarantee**:\n" +
               "   - **Atomicity**: An operation succeeds completely or rolls back with zero partial changes.\n" +
               "   - **Consistency**: Transactions always transition the database from one valid state to another.\n" +
               "   - **Isolation**: Concurrent transactions execute safely without dirty reads or race conditions.\n" +
               "   - **Durability**: Committed data is permanently written to non-volatile disk via Write-Ahead Logging (WAL).\n\n" +
               "*Inside ONE DOTS, our autonomous agents utilize SQLite WAL for tamper-evident state storage and sqlite-vec for episodic memory recall.*";
    }

    if (q.includes('api') || q.includes('rest api') || q.includes('endpoint') || q.includes('webhook')) {
        return "An **Application Programming Interface (API)** is a formal protocol that allows distinct software applications to communicate and exchange data securely:\n\n" +
               "- **REST APIs**: Stateless, resource-oriented HTTP endpoints utilizing standard verbs (`GET`, `POST`, `PUT`, `DELETE`) with standardized HTTP status codes.\n" +
               "- **Webhooks**: Event-driven push notifications triggered immediately when external events occur (e.g. GitHub commits, Stripe payments).\n" +
               "- **FastAPI Framework**: Modern, high-performance Python web framework featuring async event loops, Pydantic type validation, and automatic OpenAPI documentation.\n\n" +
               "*ONE DOTS exposes secure REST endpoints with Row-Level Security (RLS) and HMAC SHA-256 webhook signatures.*";
    }

    if (q.includes('python') || q.includes('asyncio') || q.includes('fastapi')) {
        return "**Python** is a versatile high-level programming language renowned for its expressive syntax, rich ecosystem, and dominance in AI and backend engineering:\n\n" +
               "- **AsyncIO**: Concurrent asynchronous execution with event loops, `async`/`await` coroutines, and non-blocking I/O.\n" +
               "- **Type Hinting & Pydantic**: Robust runtime data validation and schema enforcement.\n" +
               "- **Scientific Computing**: Libraries like NumPy, SciPy, and Pandas power empirical research (utilized by our **SAGE** specialist).\n\n" +
               "*ONE DOTS executes sandboxed Python code in isolated cloud runtimes with interactive STDIN safety.*";
    }

    if (q.includes('stdin') || q.includes('input')) {
        return "The Cloud Computer features an isolated execution sandbox equipped with a Safe Input Shim. When `input()` is called without terminal interaction, it automatically handles EOFError and defaults to 'User' in milliseconds, preventing the 30-second timeout. Operators can also supply inputs directly in the STDIN input field.";
    }

    if (q.includes('archetype') || q.includes('nova') || q.includes('sage') || q.includes('axis') || q.includes('muse') || q.includes('hex') || q.includes('silver')) {
        return "ONE DOTS features 6 Specialist Archetypes:\n- **Blue Dot (NOVA)**: Product Launch Lead — Linear & GitHub roadmaps\n- **Lime-Green Dot (SAGE)**: Research Scientist — Statistical analysis, Welch's t-test, ANOVA & charts\n- **Golden-Yellow Dot (AXIS)**: Tender & Enterprise Lead — Government tender NIT ingestion & compliance matrices\n- **Purple Dot (MUSE)**: Content Studio Lead — Real .pptx presentations, .docx reports & study guides\n- **Dark Navy Dot (HEX)**: Autonomous Software Dev — Bug reproduction, sandbox pytests & atomic patches\n- **Red Dot (SILVER)**: Ineffable Discovery Scientist — Pure RL heuristics & verified mathematical invariants.";
    }

    if (q.includes('voice') || q.includes('call')) {
        return "Real-Time Voice Calls connect directly to the Google Gemini Audio Engine. Click 'Live Voice Call' in any Dot profile to speak with full bidirectional audio synthesis.";
    }

    if (q.includes('safeguard') || q.includes('review') || q.includes('approval') || q.includes('security')) {
        return "The 19-Layer Hardened Security Matrix includes: Row-Level Security (RLS) tenant isolation, tamper-evident SQLite WAL audit logging, zero-trust cloud computers, Action Auto-Review risk scoring, and mandatory Human-in-the-Loop approval gates.";
    }

    if (q.includes('pricing') || q.includes('tier') || q.includes('plan') || q.includes('cost') || q.includes('quota')) {
        return "ONE DOTS offers two commercial tiers:\n- **Starter ($0/mo)**: Community access, 50 autonomous cycles/mo, shared sandboxes.\n- **Business Premium ($50/user/mo)**: 500 deep work cycles/mo, dedicated cloud computers, priority voice synthesis, and unlimited 4,000+ app connectors.";
    }

    return "ONE DOTS is an always-on autonomous AI platform powered by Google Gemini and dedicated cloud computers. It features 6 specialist Dots, the Ineffable Empirical Discovery Engine, AXIS Tender Intelligence, and 19 enterprise security layers. Ask me anything about our architecture, specialists, discovery experiments, or engineering questions!";
}
