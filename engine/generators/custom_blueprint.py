#!/usr/bin/env python3
"""
Dynamic Custom Blueprint Generator — Generates high-fidelity 9:16 system design reels
from any custom topic prompt or AI script with dynamic duration (>10s).
720x1280 @ 30fps.
"""
import os, sys, math
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from blueprint_engine import (
    W, H, FPS, BG, AMBER, AMBER_D, TEAL, TEAL_D, BLUE, BLUE_D,
    WHITE, MUTED, DIM, RED, RED_D, GREEN, GREEN_D,
    MONO, MONOB, SANS, SANSB,
    ease, alpha, lerp, track, panel, screen, belt, machine,
    draw_header_bar, draw_caption_pill, finish
)

DEFAULT_CONFIG = {
    "handle": "@buildebugship",
    "title1": "SYSTEM",
    "title_vs": "vs",
    "title2": "DESIGN",
    "comp_left": "TRADITIONAL",
    "comp_right": "OPTIMIZED",
    "subhook": "how modern distributed architecture scales under heavy load",
    "metric1_label": "LATENCY",
    "metric1_val": "0.4ms",
    "metric2_label": "THROUGHPUT",
    "metric2_val": "100k req/s",
    "node_left_name": "LEGACY ARCHITECTURE",
    "node_right_name": "DISTRIBUTED CLUSTER",
    "captions": [
        (0,   "high traffic hits the service simultaneously."),
        (60,  "traditional synchronous requests bottleneck the database."),
        (124, "decoupling components allows horizontal scaling."),
        (188, "real-time routing delivers instant sub-millisecond responses."),
        (250, "99.99% uptime with zero packet drops under peak load."),
    ]
}

def draw_circuit_node(d, cx, cy, w, h, label, is_active, is_optimized, fr, a):
    """Draws a crisp technical node box with glowing borders and activity pulse"""
    box_col = TEAL if is_optimized else (RED if (is_active and not is_optimized) else AMBER)
    bg_col = (12, 20, 26) if is_optimized else (24, 14, 16) if (is_active and not is_optimized) else (14, 18, 24)
    
    # Outer frame
    d.rectangle([cx - w/2, cy - h/2, cx + w/2, cy + h/2], fill=bg_col, outline=alpha(box_col, a), width=2)
    
    # Corner brackets
    bk = 8
    d.line([(cx - w/2, cy - h/2 + bk), (cx - w/2, cy - h/2), (cx - w/2 + bk, cy - h/2)], fill=WHITE, width=2)
    d.line([(cx + w/2 - bk, cy - h/2), (cx + w/2, cy - h/2), (cx + w/2, cy - h/2 + bk)], fill=WHITE, width=2)
    d.line([(cx - w/2, cy + h/2 - bk), (cx - w/2, cy + h/2), (cx - w/2 + bk, cy + h/2)], fill=WHITE, width=2)
    d.line([(cx + w/2 - bk, cy + h/2), (cx + w/2, cy + h/2), (cx + w/2, cy + h/2 - bk)], fill=WHITE, width=2)
    
    # Label
    d.text((cx, cy - 8), label, font=MONOB(11), fill=alpha(WHITE, a), anchor="mm")
    
    # Status line
    status = "OPTIMIZED ACTIVE" if is_optimized else ("BOTTLENECK DETECTED" if is_active else "NORMAL OPERATION")
    status_col = TEAL if is_optimized else (RED if is_active else MUTED)
    d.text((cx, cy + 12), status, font=MONO(9), fill=alpha(status_col, a * 0.9), anchor="mm")

def render_custom_frame(fr, config=None, total_frames=300):
    if config is None:
        config = DEFAULT_CONFIG
    
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag

    # ---- Header
    draw_header_bar(
        d, intro,
        handle=config.get("handle", "@buildebugship"),
        comp_left=config.get("comp_left", "TRADITIONAL"),
        comp_right=config.get("comp_right", "OPTIMIZED"),
        title1=config.get("title1", "SYSTEM"),
        title_vs=config.get("title_vs", "vs"),
        title2=config.get("title2", "DESIGN"),
        subhook=config.get("subhook", "how distributed systems scale seamlessly")
    )

    if diag <= 0.01:
        return base

    # ---- Telemetry Status Cards
    m1_lab = config.get("metric1_label", "LATENCY")
    m1_val = config.get("metric1_val", "0.4ms")
    m2_lab = config.get("metric2_label", "THROUGHPUT")
    m2_val = config.get("metric2_val", "100k req/s")

    # Left Telemetry
    d.line([(64, 320), (220, 320)], fill=alpha(TEAL, a), width=2)
    track(d, (64, 338), m1_lab, MONOB(11), alpha(MUTED, a), sp=2)
    d.text((64, 368), m1_val, font=MONOB(22), fill=alpha(TEAL, a), anchor="lm")

    # Right Telemetry
    d.line([(500, 320), (656, 320)], fill=alpha(AMBER, a), width=2)
    track(d, (656, 338), m2_lab, MONOB(11), alpha(MUTED, a), sp=2, anchor="rt")
    d.text((656, 368), m2_val, font=MONOB(22), fill=alpha(AMBER, a), anchor="rm")

    # Dynamic 3-Beat Timeline Scaling based on total_frames
    beat1_end = int(total_frames * 0.30)
    beat2_end = int(total_frames * 0.60)
    
    is_bottleneck = (fr >= beat1_end and fr < beat2_end)
    is_optimized = (fr >= beat2_end)

    # Ingest Router Box
    in_y = 420
    d.rectangle([200, in_y, 520, in_y + 50], fill=(14, 18, 26), outline=alpha(BLUE, a), width=2)
    track(d, (360, in_y + 16), "API GATEWAY & LOAD BALANCER", MONOB(11), alpha(BLUE, a), sp=2, anchor="mm")
    d.text((360, in_y + 36), "Ingesting 50,000 req/sec", font=MONO(10), fill=alpha(MUTED, a), anchor="mm")

    # Flow Traces
    pulse1 = (fr * 0.04) % 1.0
    pulse2 = ((fr + 15) * 0.04) % 1.0

    # Left Trace to Node 1
    d.line([(280, in_y + 50), (200, 560)], fill=alpha(RED if is_bottleneck else AMBER, a * 0.4), width=2)
    p1_x, p1_y = lerp(280, 200, pulse1), lerp(in_y + 50, 560, pulse1)
    d.ellipse([p1_x - 4, p1_y - 4, p1_x + 4, p1_y + 4], fill=alpha(RED if is_bottleneck else AMBER, a))

    # Right Trace to Node 2
    d.line([(440, in_y + 50), (520, 560)], fill=alpha(TEAL, a * 0.4), width=2)
    p2_x, p2_y = lerp(440, 520, pulse2), lerp(in_y + 50, 560, pulse2)
    d.ellipse([p2_x - 4, p2_y - 4, p2_x + 4, p2_y + 4], fill=alpha(TEAL, a))

    # Left Stage Node
    draw_circuit_node(
        d, 200, 630, 220, 100,
        config.get("node_left_name", "LEGACY SYSTEM"),
        is_active=is_bottleneck,
        is_optimized=False,
        fr=fr, a=a
    )

    # Right Stage Node
    draw_circuit_node(
        d, 520, 630, 220, 100,
        config.get("node_right_name", "OPTIMIZED CLUSTER"),
        is_active=is_optimized,
        is_optimized=True,
        fr=fr, a=a
    )

    # Downstream Storage / Cache Layer Box
    ds_y = 780
    ds_col = TEAL if is_optimized else (RED if is_bottleneck else AMBER)
    d.rectangle([140, ds_y, 580, ds_y + 110], fill=(10, 14, 20), outline=alpha(ds_col, a), width=2)
    
    track(d, (360, ds_y + 20), "PERSISTENCE & CACHING LAYER", MONOB(11), alpha(BLUE, a), sp=2, anchor="mm")
    
    # Internal Disk / RAM Blocks
    num_blocks = 4
    bw = 90
    bh = 45
    for b in range(num_blocks):
        bx = 175 + b * 105
        by = ds_y + 45
        b_lit = (fr + b * 6) % 24 < 12
        b_col = TEAL if is_optimized else (RED if is_bottleneck else DIM)
        d.rectangle([bx, by, bx + bw, by + bh], fill=(14, 18, 26), outline=alpha(b_col, a * 0.8), width=1)
        d.text((bx + bw/2, by + bh/2), f"PARTITION-{b+1}", font=MONO(9), fill=alpha(WHITE if b_lit else MUTED, a * 0.8), anchor="mm")

    # ---- Dynamic Caption Pill
    captions = config.get("captions", DEFAULT_CONFIG["captions"])
    draw_caption_pill(d, fr, captions, a)

    outro_start = int(total_frames * 0.86)
    if fr > outro_start:
        o = ease((fr - outro_start) / 20)
        track(d, (W / 2, 1090), "HIGH AVAILABILITY · ZERO DOWNTIME · HORIZONTAL SCALE", MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "KAFKA  ·  REDIS  ·  POSTGRES  ·  KUBERNETES", MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base

def _render_custom_worker(args):
    fr, out_dir, config, total_frames = args
    img = finish(render_custom_frame(fr, config, total_frames), fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))

def render_custom_reel(config, out_frames_dir, total_frames=300):
    os.makedirs(out_frames_dir, exist_ok=True)
    tasks = [(fr, out_frames_dir, config, total_frames) for fr in range(total_frames)]
    with ProcessPoolExecutor() as ex:
        list(ex.map(_render_custom_worker, tasks))
