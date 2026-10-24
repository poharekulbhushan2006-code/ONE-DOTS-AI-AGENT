import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2

WIDTH = 1280
HEIGHT = 720
FPS = 30
TOTAL_FRAMES = 480  # 16 seconds at 30 fps

# Palette - Obsidian + Champagne Gold
BG_COLOR = (13, 14, 16)         # #0D0E10
GOLD_COLOR = (214, 183, 121)     # #D6B779
GOLD_HOVER = (229, 201, 141)     # #E5C98D
IVORY_COLOR = (244, 240, 232)    # #F4F0E8
MUTED_GRAY = (163, 164, 170)     # #A3A4AA
DARK_PANEL = (21, 22, 25)        # #151619
BORDER_COLOR = (43, 44, 49)      # #2B2C31
SUCCESS_COLOR = (111, 196, 154)  # #6FC49A
CYAN_COLOR = (56, 189, 248)      # #38BDF8

def get_font(name, size):
    font_path = os.path.join(r"C:\Windows\Fonts", name)
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

FONT_TITLE = get_font("segoeui.ttf", 46)
FONT_SUBTITLE = get_font("segoeui.ttf", 22)
FONT_HEADING = get_font("segoeui.ttf", 28)
FONT_BODY = get_font("segoeui.ttf", 16)
FONT_MONO = get_font("consola.ttf", 14)
FONT_MONO_SM = get_font("consola.ttf", 11)
FONT_BADGE = get_font("segoeui.ttf", 13)

def load_transparent_dot(path):
    if not os.path.exists(path):
        # Fallback colored circle if image missing
        fallback = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        d = ImageDraw.Draw(fallback)
        d.ellipse([20, 20, 280, 280], fill=(56, 189, 248, 255))
        return fallback

    im = Image.open(path).convert("RGB")
    arr = np.array(im, dtype=float)
    # Distance from white
    diff = np.sqrt(np.sum((255 - arr) ** 2, axis=2))
    alpha = np.clip((diff - 18) / 40.0, 0, 1) * 255
    rgba = np.dstack((arr, alpha)).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")

def main():
    print("Loading Dot avatar assets...")
    dots_raw = {
        "nova": load_transparent_dot("web/assets/dots/nova.png"),
        "sage": load_transparent_dot("web/assets/dots/sage.png"),
        "axis": load_transparent_dot("web/assets/dots/axis.png"),
        "muse": load_transparent_dot("web/assets/dots/muse.png"),
        "hex": load_transparent_dot("web/assets/dots/hex.png"),
    }

    # Setup particles
    np.random.seed(42)
    num_particles = 70
    particles = []
    for _ in range(num_particles):
        particles.append({
            "x": np.random.uniform(0, WIDTH),
            "y": np.random.uniform(0, HEIGHT),
            "vx": np.random.uniform(-0.3, 0.3),
            "vy": np.random.uniform(-0.5, -0.1),
            "size": np.random.uniform(1.5, 3.5),
            "alpha": np.random.uniform(30, 140),
        })

    output_path = "web/assets/introducing_dots.mp4"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, FPS, (WIDTH, HEIGHT))

    if not out.isOpened():
        print("Failed to open VideoWriter with mp4v!")
        return

    print(f"Rendering {TOTAL_FRAMES} frames into {output_path}...")

    # Act 1: 0 - 120 (0.0s - 4.0s) - Introduction & Awakening
    # Act 2: 121 - 240 (4.0s - 8.0s) - Autonomous Deep Work (NOVA focus)
    # Act 3: 241 - 360 (8.0s - 12.0s) - Multi-Agent Synergy & Data Flow
    # Act 4: 361 - 480 (12.0s - 16.0s) - Resolution & ONE DOTS Branding

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / float(FPS)
        base = Image.new("RGBA", (WIDTH, HEIGHT), BG_COLOR + (255,))
        draw = ImageDraw.Draw(base)

        # 1. Subtle Dark Ambient Grid
        grid_alpha = 18
        for gx in range(0, WIDTH, 48):
            draw.line([(gx, 0), (gx, HEIGHT)], fill=(255, 255, 255, grid_alpha), width=1)
        for gy in range(0, HEIGHT, 48):
            draw.line([(0, gy), (WIDTH, gy)], fill=(255, 255, 255, grid_alpha), width=1)

        # 2. Golden Ambient Glow in the Center
        glow_radius = 280 + math.sin(t * 1.5) * 30
        glow_img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_img)
        glow_alpha = int(22 + 8 * math.sin(t * 2))
        glow_draw.ellipse(
            [WIDTH // 2 - glow_radius, HEIGHT // 2 - glow_radius + 40,
             WIDTH // 2 + glow_radius, HEIGHT // 2 + glow_radius + 40],
            fill=(214, 183, 121, glow_alpha)
        )
        glow_img = glow_img.filter(ImageFilter.GaussianBlur(60))
        base = Image.alpha_composite(base, glow_img)
        draw = ImageDraw.Draw(base)

        # 3. Drifting Particles
        for p in particles:
            p["x"] = (p["x"] + p["vx"]) % WIDTH
            p["y"] = (p["y"] + p["vy"]) % HEIGHT
            px, py = int(p["x"]), int(p["y"])
            pa = int(p["alpha"] * (0.6 + 0.4 * math.sin(t * 3 + p["x"])))
            draw.ellipse([px, py, px + p["size"], py + p["size"]], fill=GOLD_COLOR + (pa,))

        # 4. Scenes Rendering
        if frame_idx < 120:
            # =========================================================================
            # ACT 1: MEET THE DOTS — ALWAYS-ON AUTONOMOUS WORKFORCE
            # =========================================================================
            p_enter = min(1.0, frame_idx / 40.0)
            fade = min(1.0, frame_idx / 25.0)

            # Top Badge
            badge_text = "ONE DOTS · INTRODUCING DOTS"
            draw.rounded_rectangle([WIDTH // 2 - 160, 48, WIDTH // 2 + 160, 80], radius=16, fill=DARK_PANEL + (int(220 * fade),), outline=BORDER_COLOR + (int(255 * fade),))
            draw.ellipse([WIDTH // 2 - 142, 60, WIDTH // 2 - 132, 70], fill=GOLD_COLOR + (int(255 * fade),))
            draw.text((WIDTH // 2 - 122, 54), badge_text, fill=MUTED_GRAY + (int(255 * fade),), font=FONT_BADGE)

            # Main Headline
            head_text = "Intelligent agents. Always on."
            draw.text((WIDTH // 2 - 270, 96), head_text, fill=IVORY_COLOR + (int(255 * fade),), font=FONT_TITLE)

            sub_text = "They run continuously on dedicated cloud sandboxes, executing goals while you sleep."
            draw.text((WIDTH // 2 - 360, 156), sub_text, fill=MUTED_GRAY + (int(255 * fade),), font=FONT_SUBTITLE)

            # 5 Dots Lineup
            lineup = [
                ("muse", -380, 0.4),
                ("sage", -190, 0.2),
                ("nova", 0, 0.0),
                ("axis", 190, 0.2),
                ("hex", 380, 0.4),
            ]

            for key, x_off, delay in lineup:
                item_progress = min(1.0, max(0.0, (frame_idx - delay * 30) / 40.0))
                # Smooth ease-out
                ease = 1.0 - math.pow(1.0 - item_progress, 3)
                curr_y = int(450 - ease * 70 + math.sin(t * 2.5 + x_off) * 12)
                curr_x = int(WIDTH // 2 + x_off * ease)

                size = 180 if key == "nova" else 145
                alpha_val = int(255 * ease)

                avatar = dots_raw[key].resize((size, size), Image.Resampling.LANCZOS)
                # Shadow beneath
                shadow_w = int(size * 0.75)
                draw.ellipse(
                    [curr_x - shadow_w // 2, curr_y + size // 2 - 10,
                     curr_x + shadow_w // 2, curr_y + size // 2 + 12],
                    fill=(0, 0, 0, int(90 * ease))
                )
                base.paste(avatar, (curr_x - size // 2, curr_y - size // 2), avatar)

                # Name Tag
                name_y = curr_y + size // 2 + 18
                name_str = key.upper()
                name_color = GOLD_COLOR if key == "nova" else IVORY_COLOR
                draw.text((curr_x - 22, name_y), name_str, fill=name_color + (alpha_val,), font=FONT_BODY)

        elif frame_idx < 240:
            # =========================================================================
            # ACT 2: AUTONOMOUS EXECUTION & DEDICATED CLOUD SANDBOX (NOVA DEEP DIVE)
            # =========================================================================
            f_act2 = frame_idx - 120
            p_act2 = min(1.0, f_act2 / 30.0)

            # Left side: NOVA hero + orbital rings
            center_x = 380
            center_y = int(370 + math.sin(t * 3) * 10)
            nova_size = 230
            nova_avatar = dots_raw["nova"].resize((nova_size, nova_size), Image.Resampling.LANCZOS)

            # Orbital Ring (Rotates in 3D)
            orbit_angle = t * 1.8
            rx = 190
            ry = 65
            for deg in range(0, 360, 4):
                rad = math.radians(deg + orbit_angle * 50)
                ox = center_x + int(rx * math.cos(rad))
                oy = center_y + int(ry * math.sin(rad))
                opa = int(70 + 60 * math.sin(rad))
                draw.ellipse([ox - 1, oy - 1, ox + 1, oy + 1], fill=GOLD_COLOR + (opa,))

            # Shadow
            draw.ellipse([center_x - 90, center_y + 110, center_x + 90, center_y + 135], fill=(0, 0, 0, 120))
            base.paste(nova_avatar, (center_x - nova_size // 2, center_y - nova_size // 2), nova_avatar)

            # Orbiting Tool Satellites
            tools = [
                ("Linear API", 0),
                ("GitHub Connect", 120),
                ("Slack Dispatcher", 240),
            ]
            for tool_name, angle_deg in tools:
                rad = math.radians(angle_deg + orbit_angle * 50)
                tx = center_x + int(rx * math.cos(rad))
                ty = center_y + int(ry * math.sin(rad))
                # Only draw satellite
                draw.rounded_rectangle([tx - 44, ty - 14, tx + 44, ty + 14], radius=6, fill=DARK_PANEL + (220,), outline=BORDER_COLOR + (255,))
                draw.text((tx - 38, ty - 7), tool_name, fill=IVORY_COLOR, font=FONT_MONO_SM)

            # Right side: Simulated High-Tech Cloud REPL Window
            repl_x = 640
            repl_y = 130
            repl_w = 560
            repl_h = 470

            # Window Frame
            draw.rounded_rectangle([repl_x, repl_y, repl_x + repl_w, repl_y + repl_h], radius=12, fill=DARK_PANEL + (245,), outline=BORDER_COLOR + (255,))
            # Titlebar
            draw.rounded_rectangle([repl_x, repl_y, repl_x + repl_w, repl_y + 44], radius=12, fill=(17, 18, 21, 255))
            draw.rectangle([repl_x, repl_y + 36, repl_x + repl_w, repl_y + 44], fill=(17, 18, 21, 255))
            draw.line([(repl_x, repl_y + 44), (repl_x + repl_w, repl_y + 44)], fill=BORDER_COLOR + (255,), width=1)

            # Traffic Lights
            draw.ellipse([repl_x + 16, repl_y + 17, repl_x + 26, repl_y + 27], fill=(229, 139, 136, 255))
            draw.ellipse([repl_x + 34, repl_y + 17, repl_x + 44, repl_y + 27], fill=(230, 189, 117, 255))
            draw.ellipse([repl_x + 52, repl_y + 17, repl_x + 62, repl_y + 27], fill=(111, 196, 154, 255))

            draw.text((repl_x + 76, repl_y + 14), "nova@isolated-sandbox-wal: ~/gtm-orchestration", fill=MUTED_GRAY, font=FONT_MONO)
            draw.text((repl_x + repl_w - 110, repl_y + 14), "● REPL LIVE", fill=SUCCESS_COLOR, font=FONT_MONO_SM)

            # Terminal Code Stream (Progressive typing)
            logs = [
                ("$ python3 -m dots.orchestrator --agent NOVA", CYAN_COLOR),
                ("[NOVA] Authenticated with Linear API (OAuth2 scoped)", MUTED_GRAY),
                ("[NOVA] Scope delta detected in issue ENG-4129: SOC2 RLS Required", GOLD_COLOR),
                ("[NOVA] Executing 19-layer security hardening test harness...", MUTED_GRAY),
                (">>> pytest tests/test_security_suite.py", IVORY_COLOR),
                ("[PASS] Row Level Security (RLS) Active & Verified", SUCCESS_COLOR),
                ("[PASS] Parameterized Queries & Input Sanitization: 100%", SUCCESS_COLOR),
                ("[PASS] Isolated Container WAL Sandbox: Stable", SUCCESS_COLOR),
                ("[NOVA] Linear status updated to 'In Review' • PR #4129 Created", CYAN_COLOR),
                ("[NOVA] Slack executive briefing dispatched to #product-leadership", GOLD_COLOR),
                ("STATUS: 0 human interventions needed. Next task in 180s.", SUCCESS_COLOR),
            ]

            # Show lines based on time
            lines_visible = int((f_act2 / 120.0) * len(logs)) + 2
            curr_log_y = repl_y + 60
            for i, (line_text, line_col) in enumerate(logs[:lines_visible]):
                draw.text((repl_x + 20, curr_log_y), line_text, fill=line_col, font=FONT_MONO)
                curr_log_y += 32

            # Top Badge
            draw.text((repl_x, 80), "AUTONOMOUS TASK ORCHESTRATION", fill=GOLD_COLOR, font=FONT_HEADING)

        elif frame_idx < 360:
            # =========================================================================
            # ACT 3: MULTI-AGENT SYNERGY & CONNECTED INTELLIGENCE
            # =========================================================================
            f_act3 = frame_idx - 240
            p_act3 = min(1.0, f_act3 / 30.0)

            draw.text((WIDTH // 2 - 240, 56), "Connected Workforce Synergy", fill=IVORY_COLOR, font=FONT_TITLE)
            draw.text((WIDTH // 2 - 280, 114), "Specialist Dots coordinate in real time across your entire stack.", fill=MUTED_GRAY, font=FONT_BODY)

            # 5 Nodes in a Harmonious Constellation
            node_coords = [
                ("nova", 640, 360, 150, "NOVA · Lead Orchestrator", GOLD_COLOR),
                ("sage", 320, 260, 120, "SAGE · Research & Stats", SUCCESS_COLOR),
                ("axis", 960, 260, 120, "AXIS · Enterprise Sales", (245, 158, 11)),
                ("muse", 340, 510, 120, "MUSE · Content Studio", (192, 132, 252)),
                ("hex", 940, 510, 120, "HEX · Cloud Compiler", CYAN_COLOR),
            ]

            # Draw Energy Flows between NOVA (center) and other 4 Dots
            center_node = node_coords[0]
            for other in node_coords[1:]:
                # Animated energy pulse along line
                x1, y1 = center_node[1], center_node[2]
                x2, y2 = other[1], other[2]

                # Base connection line
                draw.line([(x1, y1), (x2, y2)], fill=BORDER_COLOR + (180,), width=2)

                # Flowing energy pulse
                pulse_phase = (t * 2.5 + other[2] * 0.01) % 1.0
                px = int(x1 + (x2 - x1) * pulse_phase)
                py = int(y1 + (y2 - y1) * pulse_phase)
                draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=GOLD_COLOR + (255,))
                draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=GOLD_COLOR + (70,))

            # Render Characters & Badges
            for key, cx, cy, sz, role_label, accent in node_coords:
                bob = int(math.sin(t * 3.0 + cx) * 8)
                avatar = dots_raw[key].resize((sz, sz), Image.Resampling.LANCZOS)
                # Aura
                draw.ellipse([cx - sz // 2 - 6, cy + bob - sz // 2 - 6, cx + sz // 2 + 6, cy + bob + sz // 2 + 6], outline=accent + (100,), width=2)
                # Shadow
                draw.ellipse([cx - sz // 3, cy + bob + sz // 2 - 6, cx + sz // 3, cy + bob + sz // 2 + 10], fill=(0, 0, 0, 100))
                base.paste(avatar, (cx - sz // 2, cy + bob - sz // 2), avatar)

                # Pill Label below
                lbl_y = cy + bob + sz // 2 + 12
                draw.rounded_rectangle([cx - 86, lbl_y, cx + 86, lbl_y + 24], radius=6, fill=DARK_PANEL + (230,), outline=BORDER_COLOR + (255,))
                draw.text((cx - 80, lbl_y + 5), role_label, fill=IVORY_COLOR, font=FONT_MONO_SM)

            # Bottom Status Strip
            draw.rounded_rectangle([WIDTH // 2 - 280, 640, WIDTH // 2 + 280, 680], radius=8, fill=DARK_PANEL + (240,), outline=BORDER_COLOR + (255,))
            draw.ellipse([WIDTH // 2 - 262, 656, WIDTH // 2 - 254, 664], fill=SUCCESS_COLOR)
            status_summary = "5 SPECIALISTS ACTIVE • CLOUD REPL ISOLATED • 4,000+ CONNECTORS"
            draw.text((WIDTH // 2 - 240, 652), status_summary, fill=MUTED_GRAY, font=FONT_MONO_SM)

        else:
            # =========================================================================
            # ACT 4: RESOLUTION — ONE DOTS (WORK SMARTER. COORDINATE INTELLIGENCE.)
            # =========================================================================
            f_act4 = frame_idx - 360
            fade_in = min(1.0, f_act4 / 30.0)

            # Central Hero Emblem and Characters
            nova_size = 200
            nova_avatar = dots_raw["nova"].resize((nova_size, nova_size), Image.Resampling.LANCZOS)
            ny = int(240 + math.sin(t * 2) * 8)
            base.paste(nova_avatar, (WIDTH // 2 - nova_size // 2, ny - nova_size // 2), nova_avatar)

            # Flanking teammates
            sage_avatar = dots_raw["sage"].resize((130, 130), Image.Resampling.LANCZOS)
            axis_avatar = dots_raw["axis"].resize((130, 130), Image.Resampling.LANCZOS)
            muse_avatar = dots_raw["muse"].resize((110, 110), Image.Resampling.LANCZOS)
            hex_avatar = dots_raw["hex"].resize((110, 110), Image.Resampling.LANCZOS)

            base.paste(sage_avatar, (WIDTH // 2 - 260, ny - 20), sage_avatar)
            base.paste(axis_avatar, (WIDTH // 2 + 130, ny - 20), axis_avatar)
            base.paste(muse_avatar, (WIDTH // 2 - 380, ny + 10), muse_avatar)
            base.paste(hex_avatar, (WIDTH // 2 + 270, ny + 10), hex_avatar)

            # Elegant Typography
            # Eyebrow
            draw.text((WIDTH // 2 - 130, 380), "ONE UNIFIED WORKSPACE", fill=GOLD_COLOR, font=FONT_BADGE)

            # Large Logo
            brand_title = "ONE DOTS"
            draw.text((WIDTH // 2 - 140, 410), brand_title, fill=IVORY_COLOR, font=FONT_TITLE)

            # Five Colored Pips under title
            pips = [
                (CYAN_COLOR, -24),
                (SUCCESS_COLOR, -12),
                (GOLD_COLOR, 0),
                ((192, 132, 252), 12),
                ((245, 158, 11), 24),
            ]
            for col, x_diff in pips:
                draw.ellipse([WIDTH // 2 + x_diff - 4, 480, WIDTH // 2 + x_diff + 4, 488], fill=col)

            # Sub-headline
            draw.text((WIDTH // 2 - 210, 505), "Work smarter. Coordinate intelligence.", fill=GOLD_COLOR, font=FONT_HEADING)
            draw.text((WIDTH // 2 - 275, 555), "A unified workspace for AI agents, task execution, and intelligent automation.", fill=MUTED_GRAY, font=FONT_BODY)

            # CTA Pill simulation
            draw.rounded_rectangle([WIDTH // 2 - 110, 600, WIDTH // 2 + 110, 644], radius=8, fill=GOLD_COLOR, outline=GOLD_HOVER)
            draw.text((WIDTH // 2 - 68, 612), "Explore agents ↗", fill=(23, 21, 18), font=FONT_HEADING)

        # Convert PIL RGBA to OpenCV BGR
        frame_rgb = base.convert("RGB")
        frame_bgr = cv2.cvtColor(np.array(frame_rgb), cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

        if frame_idx % 60 == 0:
            print(f"Rendered {frame_idx}/{TOTAL_FRAMES} frames ({int(frame_idx/TOTAL_FRAMES*100)}%)...")

    out.release()
    print("Video generation complete: web/assets/introducing_dots.mp4 successfully created!")

if __name__ == "__main__":
    main()
