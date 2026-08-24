#!/usr/bin/env python3
"""
Autoscaling — Pachinko request drops into server tubes with crane autoscaler.
720x1280 @ 30fps, 10s (300 frames).
"""
import os, sys, math, random
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from blueprint_engine import (
    W, H, FPS, DUR, NF, BG, AMBER, AMBER_D, TEAL, TEAL_D, BLUE, BLUE_D,
    WHITE, MUTED, DIM, RED, RED_D, GREEN, GREEN_D,
    MONO, MONOB, SANS, SANSB,
    ease, alpha, lerp, track, panel, screen, machine, finish, draw_caption_pill
)

CAPTIONS = [
    (0,   "traffic surges 10x during a flash sale."),
    (60,  "2 server instances hit 98% CPU and start dropping packets."),
    (124, "the autoscaler detects the load spike in real time."),
    (188, "an overhead crane rolls in 2 new server tubes automatically."),
    (250, "load redistributes instantly across 4 instances. 0% downtime."),
]

def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag

    # ---- Header
    d.text((W / 2, 168), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 192), "2 INSTANCES (98% CPU)  vs  4 AUTOSCALED (34% CPU)", MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    
    tw1 = d.textlength("AUTO ", font=SANSB(42))
    tw2 = d.textlength("SCALING", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 228), "AUTO ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 228), "SCALING", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "how cloud infra spins up instances before servers melt", font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")

    if diag <= 0.01:
        return base

    # Autoscaling States:
    # 0s - 3s: 2 servers normal load (40% CPU)
    # 3s - 5.5s: Traffic spike! 2 servers in RED (98% CPU)
    # 5.5s - 7.5s: Crane trolley rolls in 2 new server tubes!
    # 7.5s - 10s: 4 servers in parallel, load drops to 32% CPU (GREEN)!

    is_spike = (fr >= 90)
    crane_progress = ease((fr - 165) / 45) if fr >= 165 else 0.0
    is_scaled = (fr >= 210)

    # ---- Counters Row
    num_instances = 2 + (2 if crane_progress >= 0.9 else (1 if crane_progress >= 0.4 else 0))
    cpu_load = 42 if fr < 90 else (98 if fr < 180 else int(lerp(98, 34, ease((fr - 180) / 45))))
    cpu_col = GREEN if cpu_load < 60 else (AMBER if cpu_load < 85 else RED)

    d.line([(64, 340), (196, 340)], fill=alpha(cpu_col, a), width=2)
    track(d, (64, 358), "CLUSTER LOAD", MONOB(11), alpha(MUTED, a), sp=2)
    d.text((64, 388), f"{cpu_load}%", font=MONOB(28), fill=alpha(cpu_col, a), anchor="lm")
    d.text((64 + d.textlength(f"{cpu_load}%", font=MONOB(28)) + 9, 396),
           "CPU", font=MONO(11), fill=alpha(cpu_col, a * 0.7), anchor="lm")

    d.line([(524, 340), (656, 340)], fill=alpha(TEAL, a), width=2)
    track(d, (656, 358), "ACTIVE PODS", MONOB(11), alpha(MUTED, a), sp=2, anchor="rt")
    d.text((656, 388), f"{num_instances} NODES", font=MONOB(26), fill=alpha(TEAL, a), anchor="rm")

    track(d, (W / 2, 350), "TRAFFIC INGEST", MONOB(12), alpha(BLUE, a), sp=3, anchor="mm")
    d.text((W / 2, 370), "12,000 req/s (peak)" if is_spike else "1,200 req/s (normal)", font=SANS(12), fill=alpha(AMBER if is_spike else MUTED, a), anchor="mm")

    # ---- Overhead Ingest Funnel (Top)
    funnel_y = 420
    d.line([(260, funnel_y), (460, funnel_y)], fill=alpha(BLUE, a), width=2)
    d.line([(260, funnel_y), (310, funnel_y + 40)], fill=alpha(BLUE, a), width=2)
    d.line([(460, funnel_y), (410, funnel_y + 40)], fill=alpha(BLUE, a), width=2)
    d.line([(310, funnel_y + 40), (410, funnel_y + 40)], fill=alpha(BLUE, a), width=2)

    track(d, (W / 2, funnel_y + 22), "REQUEST STREAM", MONOB(10), alpha(WHITE, a), sp=1, anchor="mm")

    # ---- Pachinko Deflector Pins Matrix
    pin_start_y = 480
    pin_rows = 4
    for r in range(pin_rows):
        py = pin_start_y + r * 28
        count = 7 if r % 2 == 0 else 6
        start_px = 360 - (count - 1) * 22
        for c in range(count):
            px = start_px + c * 44
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=alpha(DIM, a))

    # ---- Falling Pachinko Request Orbs
    num_orbs = 24 if is_spike else 8
    rng = np.random.default_rng(42)
    for i in range(num_orbs):
        orb_speed = 7.0 if is_spike else 4.0
        orb_prog = ((fr * orb_speed + i * 28) % 180) / 180.0
        oy = funnel_y + 40 + orb_prog * 160
        ox = 360 + math.sin(orb_prog * math.pi * 3 + i) * (35 + orb_prog * 120)
        d.ellipse([ox - 4, oy - 4, ox + 4, oy + 4], fill=alpha(TEAL if not is_spike or is_scaled else RED, a * 0.9))

    # ---- Overhead Crane Trolley Track (Moving in 2 new server pods)
    crane_y = 660
    d.line([(40, crane_y), (680, crane_y)], fill=alpha(DIM, a), width=2)
    # Crane trolley wheels
    crane_x = lerp(640, 470, crane_progress)
    d.rectangle([crane_x - 40, crane_y - 8, crane_x + 40, crane_y + 8], fill=(20, 24, 33), outline=alpha(AMBER, a), width=1)
    track(d, (crane_x, crane_y - 14), "AUTOSCALER CRANE", MONO(9), alpha(AMBER, a), sp=1, anchor="mm")

    # Crane cable lowering pods
    if crane_progress > 0.05 and not is_scaled:
        d.line([(crane_x - 22, crane_y + 8), (crane_x - 22, crane_y + 36)], fill=alpha(AMBER, a), width=1)
        d.line([(crane_x + 22, crane_y + 8), (crane_x + 22, crane_y + 36)], fill=alpha(AMBER, a), width=1)

    # ---- 4 Vertical Glass Server Cylinder Tubes
    tube_w = 95
    tube_h = 240
    tube_y = 700
    tubes_x = [120, 240, 360, 480]

    # Active tube count
    for idx, tx in enumerate(tubes_x):
        is_active = (idx < 2) or (idx == 2 and crane_progress > 0.5) or (idx == 3 and crane_progress > 0.85)

        tube_alpha = a if is_active else a * 0.18
        border_col = cpu_col if is_active else DIM

        # Draw glass cylinder
        d.rectangle([tx - tube_w/2, tube_y, tx + tube_w/2, tube_y + tube_h],
                    fill=(9, 12, 17) if is_active else (6, 8, 11),
                    outline=alpha(border_col, tube_alpha), width=2)
        
        # Specular reflection highlight on glass
        d.line([(tx - tube_w/2 + 6, tube_y + 8), (tx - tube_w/2 + 6, tube_y + tube_h - 8)],
               fill=alpha(WHITE, tube_alpha * 0.25), width=1)

        # Cylinder Header
        track(d, (tx, tube_y + 16), f"POD-{idx+1}", MONOB(11), alpha(WHITE if is_active else MUTED, tube_alpha), sp=1, anchor="mm")

        # Liquid load level inside cylinder
        if is_active:
            fill_pct = (cpu_load / 100.0) + math.sin(fr * 0.15 + idx) * 0.03
            liquid_h = int(tube_h * fill_pct * 0.75)
            liquid_y = tube_y + tube_h - liquid_h

            d.rectangle([tx - tube_w/2 + 4, liquid_y, tx + tube_w/2 - 4, tube_y + tube_h - 4],
                        fill=alpha(border_col, 0.35))
            d.line([(tx - tube_w/2 + 4, liquid_y), (tx + tube_w/2 - 4, liquid_y)],
                   fill=alpha(border_col, 0.9), width=2)
            
            # CPU label inside cylinder
            d.text((tx, tube_y + tube_h - 18), f"{int(cpu_load)}%", font=MONOB(13), fill=alpha(WHITE, tube_alpha), anchor="mm")
        else:
            d.text((tx, tube_y + tube_h / 2), "STANDBY", font=MONO(10), fill=alpha(DIM, tube_alpha), anchor="mm")

    # ---- Outro & Caption Pill
    draw_caption_pill(d, fr, CAPTIONS, a)

    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "HPA · CPU THRESHOLD > 80% · REPLICA SET", MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "KUBERNETES  ·  AWS ECS  ·  GCP CLOUD RUN", MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base

def render_and_save_frame(args):
    fr, out_dir = args
    img = finish(render(fr), fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))

if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_autoscaling"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered Autoscaling frames: {len(frames)}")
