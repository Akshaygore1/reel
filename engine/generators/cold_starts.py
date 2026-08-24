#!/usr/bin/env python3
"""
Serverless Cold Starts — 1,180ms Cold Penalty vs 40ms Warm Invocation.
Visual Apparatus: MicroVM Container Ignition Chamber & Thermal Warming Coils.
Narrative:
- Beat 1 (0-3s): First request arrives, container is dormant / cold.
- Beat 2 (3-6s): Bootstrap freeze: downloading code, starting runtime (1,180ms spike) -> Alert Buzzer.
- Beat 3 (6-10s): Execution environment is warmed -> Subsequent calls execute in 40ms -> Victory Chime.
"""
import os, sys, math
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from blueprint_engine import (
    W, H, FPS, NF, BG, WHITE, MUTED, DIM, TEAL, AMBER, RED, GREEN, BLUE,
    MONO, MONOB, SANS, SANSB, alpha, draw_header_bar, draw_telemetry_hud, draw_caption_pill, finish
)
from apparatus.hydraulic import draw_pipe, draw_fluid_tank, draw_valve

CAPTIONS = [
    (0, "Your function is dormant until called: first request builds the runtime environment"),
    (90, "Cold start pays the 1,180ms setup penalty: code download + microVM initialization"),
    (180, "Once warmed, subsequent requests execute directly in memory at blazing 40ms speed")
]

def render(fr):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    t = fr / FPS

    # 1. Header Bar
    draw_header_bar(d, 1.0, handle="@buildebugship", comp_left="COLD CONTAINER", comp_right="WARM EXECUTION",
                    title1="COLD", title_vs="vs", title2="WARM START", subhook="why serverless functions take 1,180ms then 40ms")

    # 2. Telemetry HUD
    if fr < 90:
        draw_telemetry_hud(d, "CONTAINER STATE", "IDLE (COLD)", "EXECUTION LATENCY", "INITIALIZING...", 1.0, AMBER, MUTED)
    elif fr < 180:
        flicker = 1.0 if (fr // 4 % 2 == 0) else 0.4
        draw_telemetry_hud(d, "COLD START PENALTY", "1,180 ms", "CPU INIT THREAD", "98% BOOTSTRAP", flicker, RED, RED)
    else:
        draw_telemetry_hud(d, "WARM EXECUTION", "40 ms (30x FASTER)", "CONTAINER STATUS", "100% WARM / READY", 1.0, GREEN, GREEN)

    # 3. Visual Stage (MicroVM Execution Chamber & Thermal Coils)
    cx, cy = W / 2, 650

    # Supply pipes at top and bottom
    draw_pipe(d, cx - 180, 420, cx, 480, width=20, fluid_col=AMBER if fr < 180 else GREEN, flow_phase=t * 2.0)
    draw_pipe(d, cx, 800, cx + 180, 860, width=20, fluid_col=GREEN if fr >= 180 else DIM, flow_phase=t * 2.0)

    # Main MicroVM Container Box
    box_w, box_h = 320, 260
    bx0, by0 = cx - box_w / 2, cy - box_h / 2
    bx1, by1 = cx + box_w / 2, cy + box_h / 2

    # Status-dependent container color
    if fr < 90:
        box_col = DIM
        status_text = "CONTAINER: DORMANT (COLD)"
        temp_ratio = 0.1
    elif fr < 180:
        box_col = RED
        status_text = "BOOTING RUNTIME (INIT...)"
        temp_ratio = 0.5 + 0.5 * math.sin(t * 10.0)
    else:
        box_col = GREEN
        status_text = "WARM INSTANCE: ACTIVE (40ms)"
        temp_ratio = 0.95

    # Container Chassis
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=12, fill=(10, 14, 22), outline=alpha(box_col, 0.9), width=2)

    # Header label inside container
    d.rectangle([bx0 + 10, by0 + 10, bx1 - 10, by0 + 42], fill=(14, 20, 30), outline=alpha(box_col, 0.6), width=1)
    d.text((cx, by0 + 26), status_text, font=MONOB(11), fill=WHITE, anchor="mm")

    # Step checklist inside container
    steps = [
        ("1. Fetch Application Code", fr >= 30),
        ("2. Start MicroVM & Runtime", fr >= 100),
        ("3. Execute Global init()", fr >= 140),
        ("4. Handle Request Handler()", fr >= 180)
    ]
    for idx, (label, is_done) in enumerate(steps):
        sy = by0 + 64 + idx * 36
        step_col = GREEN if is_done else (AMBER if (idx == (fr // 45)) else DIM)
        bullet = "✓" if is_done else ("▶" if (idx == (fr // 45)) else "○")
        d.text((bx0 + 24, sy), f"{bullet} {label}", font=MONOB(10), fill=step_col, anchor="lm")
        # Progress bar
        if idx == (fr // 45) and not is_done:
            prog = (fr % 45) / 45.0
            d.line([(bx0 + 24, sy + 14), (bx0 + 24 + prog * 200, sy + 14)], fill=AMBER, width=2)

    # Thermal heat coil glow on sides
    for side_x in [bx0 - 16, bx1 + 16]:
        coil_col = GREEN if fr >= 180 else (RED if fr >= 90 else DIM)
        d.line([(side_x, by0 + 20), (side_x, by1 - 20)], fill=alpha(coil_col, temp_ratio), width=4)

    # 4. Lower Caption Progression
    draw_caption_pill(d, fr, CAPTIONS, 1.0)

    return finish(img, fr)

def render_and_save_frame(args):
    fr, out_dir = args
    img = render(fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))

if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_cold_starts"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered Cold Starts frames: {len(frames)}")
