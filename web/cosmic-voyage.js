/**
 * COSMIC VOYAGE: Luminous Orange-and-Blue Particle Swarm Engine
 * Inspired by GetLayers AI "New Era" Template
 *
 * "A luminous swarm of orange-and-blue particles drifts through deep space,
 *  endlessly reshaping itself as you scroll — a cinematic voyage from a single
 *  point of light to a vast spiral galaxy."
 *
 * Formations:
 *  0. The Primordial Singularity (0.00 - 0.15): Single radiant point of light, pulsating corona
 *  1. Cosmic Torus & Vortex (0.20 - 0.45): Dual interlocked rings of orange & blue plasma
 *  2. Galactic Filament Web (0.50 - 0.70): Weaving celestial ribbons & neural bridges
 *  3. Vast Spiral Galaxy (0.75 - 1.00): 4-arm logarithmic spiral with Keplerian differential rotation
 */

(function () {
    'use strict';

    // Configuration
    const TOTAL_PARTICLES = 2400;
    const CAMERA_FOV = 650;
    const GALAXY_RADIUS = 520;
    const LERP_FACTOR = 0.065;

    // Canvas & Context
    let canvas, ctx;
    let width = 0, height = 0, dpr = 1;
    let animFrameId = null;

    // State Variables
    let scrollProgress = 0;
    let targetScrollProgress = 0;
    let autoCruiseActive = false;
    let autoCruiseTime = 0;
    let mouseX = 0, mouseY = 0;
    let targetMouseX = 0, targetMouseY = 0;
    let globalAngle = 0;

    // Palette: Luminous Celestial Oranges & Electric Space Blues
    const PALETTE = {
        orange: [
            { r: 255, g: 90, b: 0 },    // Incandescent blaze orange
            { r: 255, g: 140, b: 20 },  // Solar amber
            { r: 255, g: 175, b: 45 },  // Golden corona
            { r: 255, g: 60, b: 0 },    // Deep volcanic orange
            { r: 255, g: 210, b: 80 }   // Hot stellar gold
        ],
        blue: [
            { r: 0, g: 245, b: 255 },   // Neon cyan
            { r: 56, g: 189, b: 248 },  // Electric sky blue
            { r: 14, g: 165, b: 233 },  // Deep celestial azure
            { r: 99, g: 102, b: 241 },  // Cosmic indigo
            { r: 37, g: 99, b: 235 }    // Royal space blue
        ],
        stellar: [
            { r: 255, g: 255, b: 255 }, // Pure white supergiant
            { r: 254, g: 240, b: 138 }  // Warm stellar core
        ]
    };

    // Particles Data Array
    let particles = [];

    // Formation Generator Functions
    function initParticles() {
        particles = [];

        for (let i = 0; i < TOTAL_PARTICLES; i++) {
            // Determine Color Scheme: ~48% Orange, ~47% Blue, ~5% Core White
            let colorType, rgb;
            const randType = Math.random();
            if (randType < 0.48) {
                colorType = 'orange';
                rgb = PALETTE.orange[Math.floor(Math.random() * PALETTE.orange.length)];
            } else if (randType < 0.95) {
                colorType = 'blue';
                rgb = PALETTE.blue[Math.floor(Math.random() * PALETTE.blue.length)];
            } else {
                colorType = 'stellar';
                rgb = PALETTE.stellar[Math.floor(Math.random() * PALETTE.stellar.length)];
            }

            // -------------------------------------------------------------
            // Formation 0: The Primordial Singularity (Single Point of Light)
            // Dense hyper-concentrated micro-sphere with intense core
            // -------------------------------------------------------------
            const u0 = Math.random();
            const r0 = 8 + Math.pow(u0, 3.2) * 52; // Tightly packed in core radius 8-60px
            const theta0 = Math.random() * Math.PI * 2;
            const phi0 = Math.acos(2 * Math.random() - 1);
            const f0 = {
                x: r0 * Math.sin(phi0) * Math.cos(theta0),
                y: r0 * Math.sin(phi0) * Math.sin(theta0),
                z: r0 * Math.cos(phi0),
                spinSpeed: (Math.random() - 0.5) * 0.08
            };

            // -------------------------------------------------------------
            // Formation 1: Cosmic Torus / Dual Orbital Vortex
            // Intertwined toroidal rings of orbiting orange and blue streams
            // -------------------------------------------------------------
            const majorR1 = 260 + (Math.random() - 0.5) * 50;
            const minorR1 = 45 + Math.random() * 35;
            const ringAngle1 = (i / TOTAL_PARTICLES) * Math.PI * 2;
            const tubeAngle1 = ringAngle1 * 6 + (colorType === 'orange' ? 0 : Math.PI);
            const f1 = {
                x: (majorR1 + minorR1 * Math.cos(tubeAngle1)) * Math.cos(ringAngle1),
                y: (majorR1 + minorR1 * Math.cos(tubeAngle1)) * Math.sin(ringAngle1) * 0.42 + minorR1 * Math.sin(tubeAngle1) * 0.88,
                z: -(majorR1 + minorR1 * Math.cos(tubeAngle1)) * Math.sin(ringAngle1) * 0.88 + minorR1 * Math.sin(tubeAngle1) * 0.42,
                spinSpeed: 0.015
            };

            // -------------------------------------------------------------
            // Formation 2: Celestial Filament Web / Neural Constellation
            // Flowing ribbons and galactic bridges stretching across deep space
            // -------------------------------------------------------------
            const strandIdx = i % 4; // 4 major cosmic filaments
            const t2 = (i / TOTAL_PARTICLES) * Math.PI * 4 - Math.PI * 2;
            const radius2 = 180 + Math.sin(t2 * 3) * 80 + Math.random() * 60;
            const strandOffset = (strandIdx * Math.PI) / 2;
            const f2 = {
                x: radius2 * Math.cos(t2 + strandOffset),
                y: t2 * 90 + Math.sin(t2 * 2 + strandOffset) * 60,
                z: radius2 * Math.sin(t2 + strandOffset),
                spinSpeed: 0.008
            };

            // -------------------------------------------------------------
            // Formation 3: Vast Spiral Galaxy (Milky Way / Andromeda Architecture)
            // 4 logarithmic spiral arms, central bulge, differential rotation
            // -------------------------------------------------------------
            const numArms = 4;
            const arm = i % numArms;
            // Radius from center: concentrated near galactic bulge, fading out into spiral arms
            const distFrac = Math.pow(Math.random(), 0.62);
            const r3 = 25 + distFrac * GALAXY_RADIUS;
            // Logarithmic spiral: theta = armAngle + b * ln(r) + random spread
            const armAngle = (arm * (Math.PI * 2)) / numArms;
            const spiralWinding = 3.6;
            const theta3 = armAngle + spiralWinding * Math.log(r3 / 20) + (Math.random() - 0.5) * (0.35 + (r3 / GALAXY_RADIUS) * 0.5);
            // Disk thickness tapers toward the edge
            const diskThickness = (1 - (r3 / GALAXY_RADIUS) * 0.7) * 45;
            const z3Raw = (Math.random() - 0.5) * diskThickness;

            // Inclination: Tilt the galaxy in 3D space (~55 deg pitch, ~20 deg roll)
            const pitch = 0.95; // ~54.4 degrees tilt
            const yaw = 0.35;
            const cosP = Math.cos(pitch), sinP = Math.sin(pitch);
            const cosY = Math.cos(yaw), sinY = Math.sin(yaw);

            const xGal = r3 * Math.cos(theta3);
            const yGal = r3 * Math.sin(theta3);
            const zGal = z3Raw;

            // Rotate into 3D view
            const xRot = xGal * cosY - zGal * sinY;
            const zRot = xGal * sinY + zGal * cosY;
            const yFinal = yGal * cosP - zRot * sinP;
            const zFinal = yGal * sinP + zRot * cosP;

            const f3 = {
                x: xRot,
                y: yFinal,
                z: zFinal,
                r: r3,
                theta: theta3,
                // Differential Keplerian rotation: inner stars orbit faster than outer stars
                spinSpeed: 0.035 / Math.sqrt(1 + (r3 / 80))
            };

            particles.push({
                rgb: rgb,
                colorType: colorType,
                baseRadius: Math.random() < 0.08 ? (Math.random() * 2.2 + 2.2) : (Math.random() * 1.4 + 0.8),
                alpha: Math.random() * 0.5 + 0.45,
                twinkleSpeed: Math.random() * 0.03 + 0.008,
                phase: Math.random() * Math.PI * 2,
                f0: f0,
                f1: f1,
                f2: f2,
                f3: f3,
                currX: f0.x,
                currY: f0.y,
                currZ: f0.z
            });
        }
    }

    // Smoothstep easing helper
    function smoothstep(min, max, value) {
        const x = Math.max(0, Math.min(1, (value - min) / (max - min)));
        return x * x * (3 - 2 * x);
    }

    // Resize Handler
    function handleResize() {
        if (!canvas) return;
        width = window.innerWidth;
        height = window.innerHeight;
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        canvas.style.width = width + 'px';
        canvas.style.height = height + 'px';
        if (ctx) {
            ctx.scale(dpr, dpr);
        }
    }

    // Scroll & Mouse Listeners
    function handleScroll() {
        if (autoCruiseActive) return;
        const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
        const raw = window.scrollY / maxScroll;
        targetScrollProgress = Math.max(0, Math.min(1, raw));
        updateHudText();
    }

    function handleMouseMove(e) {
        targetMouseX = ((e.clientX / width) - 0.5) * 80;
        targetMouseY = ((e.clientY / height) - 0.5) * 80;
    }

    // Main 3D Particle Render Loop
    function render(timestamp) {
        animFrameId = requestAnimationFrame(render);
        if (!ctx) return;

        // Auto-Cruise Mode Animation
        if (autoCruiseActive) {
            autoCruiseTime += 0.003;
            // Smoothly traverse from 0 to 1 and back in an endless sinusoidal loop
            targetScrollProgress = 0.5 + 0.5 * Math.sin(autoCruiseTime);
            updateHudText();
        }

        // Interpolate scroll progress & mouse coordinates with smooth inertia
        scrollProgress += (targetScrollProgress - scrollProgress) * LERP_FACTOR;
        mouseX += (targetMouseX - mouseX) * 0.05;
        mouseY += (targetMouseY - mouseY) * 0.05;

        // Global slow cosmic rotation
        globalAngle += 0.0025;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        const centerX = width / 2;
        const centerY = height / 2;

        // Piecewise Interpolation Weights across the 4 Epochs
        // Epoch 0: Singularity (p in 0.00 - 0.28)
        // Epoch 1: Cosmic Torus (p in 0.28 - 0.58)
        // Epoch 2: Filament Web (p in 0.58 - 0.82)
        // Epoch 3: Spiral Galaxy (p in 0.82 - 1.00)
        let w0 = 0, w1 = 0, w2 = 0, w3 = 0;

        if (scrollProgress < 0.33) {
            const t = smoothstep(0.0, 0.33, scrollProgress);
            w0 = 1 - t;
            w1 = t;
            w2 = 0;
            w3 = 0;
        } else if (scrollProgress < 0.66) {
            const t = smoothstep(0.33, 0.66, scrollProgress);
            w0 = 0;
            w1 = 1 - t;
            w2 = t;
            w3 = 0;
        } else {
            const t = smoothstep(0.66, 1.0, scrollProgress);
            w0 = 0;
            w1 = 0;
            w2 = 1 - t;
            w3 = t;
        }

        // Render Singularity Central Hyper-Glow when near Epoch 0
        if (w0 > 0.05) {
            renderSingularityOpticalCore(centerX, centerY, w0, timestamp);
        }

        // Enable additive optical blending for brilliant incandescent cosmic bloom
        ctx.globalCompositeOperation = 'lighter';

        // Update and project each particle
        for (let i = 0; i < TOTAL_PARTICLES; i++) {
            const p = particles[i];

            // 1. Compute dynamic positions in each formation
            // Form 0: Singularity pulsing & rapid spin
            const singPulse = 1 + 0.18 * Math.sin(timestamp * 0.005 + p.phase);
            const sCos = Math.cos(globalAngle * 4 + p.f0.spinSpeed);
            const sSin = Math.sin(globalAngle * 4 + p.f0.spinSpeed);
            const x0 = (p.f0.x * sCos - p.f0.z * sSin) * singPulse;
            const y0 = p.f0.y * singPulse;
            const z0 = (p.f0.x * sSin + p.f0.z * sCos) * singPulse;

            // Form 1: Torus rotation
            const tCos = Math.cos(globalAngle * 1.5);
            const tSin = Math.sin(globalAngle * 1.5);
            const x1 = p.f1.x * tCos - p.f1.z * tSin;
            const y1 = p.f1.y;
            const z1 = p.f1.x * tSin + p.f1.z * tCos;

            // Form 2: Filament wave
            const fCos = Math.cos(globalAngle * 0.8);
            const fSin = Math.sin(globalAngle * 0.8);
            const x2 = p.f2.x * fCos - p.f2.z * fSin;
            const y2 = p.f2.y + Math.sin(timestamp * 0.002 + p.phase) * 15;
            const z2 = p.f2.x * fSin + p.f2.z * fCos;

            // Form 3: Spiral Galaxy differential rotation
            const gAngle = globalAngle * 1.2 + p.f3.spinSpeed * (timestamp * 0.05);
            const gCos = Math.cos(gAngle);
            const gSin = Math.sin(gAngle);
            const x3 = p.f3.x * gCos - p.f3.z * gSin;
            const y3 = p.f3.y;
            const z3 = p.f3.x * gSin + p.f3.z * gCos;

            // 2. Smoothly Morph between Formations
            const targetX = x0 * w0 + x1 * w1 + x2 * w2 + x3 * w3;
            const targetY = y0 * w0 + y1 * w1 + y2 * w2 + y3 * w3;
            const targetZ = z0 * w0 + z1 * w1 + z2 * w2 + z3 * w3;

            // Smooth inertia interpolation for current position
            p.currX += (targetX - p.currX) * 0.12;
            p.currY += (targetY - p.currY) * 0.12;
            p.currZ += (targetZ - p.currZ) * 0.12;

            // 3. 3D Perspective Projection with Mouse Parallax
            const finalZ = p.currZ + 250;
            const depthFactor = CAMERA_FOV / (CAMERA_FOV + finalZ);
            if (depthFactor <= 0) continue;

            const screenX = centerX + (p.currX + mouseX) * depthFactor;
            const screenY = centerY + (p.currY + mouseY) * depthFactor;

            // Skip offscreen particles
            if (screenX < -50 || screenX > width + 50 || screenY < -50 || screenY > height + 50) continue;

            // Twinkle & depth-based alpha
            const twinkle = 0.8 + 0.2 * Math.sin(timestamp * p.twinkleSpeed + p.phase);
            const apparentRadius = Math.max(0.6, p.baseRadius * depthFactor);
            const finalAlpha = Math.min(1, Math.max(0.12, p.alpha * depthFactor * twinkle));

            // 4. Luminous Multi-Pass Particle Rendering
            const r = p.rgb.r, g = p.rgb.g, b = p.rgb.b;

            // Outer luminous ambient aura
            ctx.beginPath();
            ctx.arc(screenX, screenY, apparentRadius * 3.2, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${finalAlpha * 0.22})`;
            ctx.fill();

            // Vibrant dense core
            ctx.beginPath();
            ctx.arc(screenX, screenY, apparentRadius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${finalAlpha * 0.95})`;
            ctx.fill();

            // Hot stellar focal point for larger particles
            if (p.baseRadius > 1.8) {
                ctx.beginPath();
                ctx.arc(screenX, screenY, apparentRadius * 0.45, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 255, ${finalAlpha * 0.9})`;
                ctx.fill();
            }
        }

        // Reset composite operation
        ctx.globalCompositeOperation = 'source-over';
    }

    // Render Singularity Optical Diffraction Flare (The Single Point of Light)
    function renderSingularityOpticalCore(cx, cy, intensity, time) {
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';

        const pulse = 1 + 0.15 * Math.sin(time * 0.008);
        const coreRadius = (35 + 25 * pulse) * intensity;

        // Central blinding white-orange-blue core glow
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreRadius * 2.8);
        grad.addColorStop(0, `rgba(255, 255, 255, ${0.9 * intensity})`);
        grad.addColorStop(0.2, `rgba(255, 140, 0, ${0.75 * intensity})`);
        grad.addColorStop(0.5, `rgba(0, 245, 255, ${0.45 * intensity})`);
        grad.addColorStop(0.85, `rgba(37, 99, 235, ${0.15 * intensity})`);
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(cx, cy, coreRadius * 2.8, 0, Math.PI * 2);
        ctx.fill();

        // Cross diffraction light rays (Cosmic Lens Flare)
        ctx.strokeStyle = `rgba(255, 255, 255, ${0.45 * intensity})`;
        ctx.lineWidth = 1.8;

        const rayLen = 140 * intensity * pulse;
        // Horizontal ray
        ctx.beginPath();
        ctx.moveTo(cx - rayLen, cy);
        ctx.lineTo(cx + rayLen, cy);
        ctx.stroke();

        // Vertical ray
        ctx.beginPath();
        ctx.moveTo(cx, cy - rayLen);
        ctx.lineTo(cx, cy + rayLen);
        ctx.stroke();

        ctx.restore();
    }

    // Interactive Floating HUD Controller Pill
    function initCosmicVoyageHUD() {
        const hud = document.createElement('div');
        hud.id = 'cosmic-voyage-hud';
        hud.className = 'cosmic-voyage-hud';
        hud.innerHTML = `
            <div class="hud-pill-inner">
                <div class="hud-indicator-dot"></div>
                <div class="hud-label-group">
                    <span class="hud-eyebrow">COSMIC VOYAGE • GETLAYERS NEW ERA</span>
                    <strong class="hud-epoch-title" id="hud-epoch-title">Point of Light (Singularity)</strong>
                </div>
                <div class="hud-stages-bar">
                    <button type="button" class="hud-stage-btn active" data-progress="0.00" title="Epoch 0: Primordial Singularity (Point of Light)">◉ Singularity</button>
                    <button type="button" class="hud-stage-btn" data-progress="0.35" title="Epoch 1: Cosmic Torus & Vortex">◯ Torus</button>
                    <button type="button" class="hud-stage-btn" data-progress="0.65" title="Epoch 2: Celestial Filament Web">☊ Filaments</button>
                    <button type="button" class="hud-stage-btn" data-progress="1.00" title="Epoch 3: Vast Spiral Galaxy">🌀 Galaxy</button>
                </div>
                <div class="hud-actions-group">
                    <button type="button" class="hud-cruise-btn" id="hud-cruise-toggle" title="Toggle Hands-Free Cinematic Auto-Voyage">
                        <span id="hud-cruise-icon">▶</span> Cruise
                    </button>
                    <button type="button" class="hud-minimize-btn" id="hud-minimize-toggle" title="Minimize / Expand HUD Pill">
                        —
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(hud);

        // Bind Stage buttons
        hud.querySelectorAll('.hud-stage-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                autoCruiseActive = false;
                const prog = parseFloat(btn.dataset.progress);
                targetScrollProgress = prog;

                // Sync window scroll
                const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
                window.scrollTo({
                    top: prog * maxScroll,
                    behavior: 'smooth'
                });
                updateHudText();
            });
        });

        // Bind Auto-Cruise toggle
        const cruiseBtn = document.getElementById('hud-cruise-toggle');
        if (cruiseBtn) {
            cruiseBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                autoCruiseActive = !autoCruiseActive;
                cruiseBtn.classList.toggle('active', autoCruiseActive);
                const icon = document.getElementById('hud-cruise-icon');
                if (icon) icon.innerText = autoCruiseActive ? '⏸' : '▶';
                updateHudText();
            });
        }

        // Bind Minimize toggle
        const minBtn = document.getElementById('hud-minimize-toggle');
        if (minBtn) {
            minBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                hud.classList.toggle('minimized');
                minBtn.innerText = hud.classList.contains('minimized') ? '✦' : '—';
            });
        }
    }

    // Update HUD Text & Active Stage State
    function updateHudText() {
        const titleEl = document.getElementById('hud-epoch-title');
        const p = scrollProgress;
        let epochName = 'Point of Light (Singularity)';
        let activeIdx = 0;

        if (p < 0.22) {
            epochName = '1. Primordial Singularity (Point of Light)';
            activeIdx = 0;
        } else if (p < 0.52) {
            epochName = '2. Cosmic Torus & Vortex (Expansion)';
            activeIdx = 1;
        } else if (p < 0.78) {
            epochName = '3. Celestial Filament Web (Deep Space)';
            activeIdx = 2;
        } else {
            epochName = '4. Vast Spiral Galaxy (Milky Way / Andromeda)';
            activeIdx = 3;
        }

        if (titleEl) {
            const pct = Math.round(p * 100);
            titleEl.innerText = `${epochName} • ${pct}%`;
        }

        const btns = document.querySelectorAll('.hud-stage-btn');
        btns.forEach((btn, idx) => {
            btn.classList.toggle('active', idx === activeIdx);
        });
    }

    // Initialization
    function init() {
        canvas = document.getElementById('cosmic-voyage-canvas');
        if (!canvas) {
            // If canvas not yet in DOM, create and prepend to app-background or body
            const bg = document.querySelector('.app-background') || document.body;
            canvas = document.createElement('canvas');
            canvas.id = 'cosmic-voyage-canvas';
            canvas.className = 'cosmic-voyage-canvas';
            bg.insertBefore(canvas, bg.firstChild);
        }

        ctx = canvas.getContext('2d');
        if (!ctx) return;

        handleResize();
        initParticles();
        initCosmicVoyageHUD();

        window.addEventListener('resize', handleResize, { passive: true });
        window.addEventListener('scroll', handleScroll, { passive: true });
        window.addEventListener('mousemove', handleMouseMove, { passive: true });

        // Touch support
        window.addEventListener('touchmove', (e) => {
            if (e.touches && e.touches.length > 0) {
                targetMouseX = ((e.touches[0].clientX / width) - 0.5) * 80;
                targetMouseY = ((e.touches[0].clientY / height) - 0.5) * 80;
            }
        }, { passive: true });

        // Kick off render loop
        if (animFrameId) cancelAnimationFrame(animFrameId);
        animFrameId = requestAnimationFrame(render);

        // Initial scroll sync
        handleScroll();
    }

    // Auto-init on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export Global API for developer inspection & interactive controls
    window.CosmicVoyage = {
        setEpoch: (epoch) => {
            const targets = [0.0, 0.35, 0.65, 1.0];
            const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
            const val = targets[epoch] || 0.0;
            targetScrollProgress = val;
            window.scrollTo({ top: val * maxScroll, behavior: 'smooth' });
        },
        toggleCruise: () => {
            const btn = document.getElementById('hud-cruise-toggle');
            if (btn) btn.click();
        },
        getScrollProgress: () => scrollProgress
    };

})();
