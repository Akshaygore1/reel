#!/usr/bin/env python3
"""
Flagship System Design Reel: Redis In-Memory vs PostgreSQL Disk Storage
Visual Apparatus: Glowing RAM Silicon Memory Banks (0.1ms) vs Rotating Magnetic Platter Disk (45ms).
720x1280 @ 30fps, 10s (300 frames).
"""
import os, sys, math
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from blueprint_engine import (
    W, H, FPS, DUR, NF, BG, AMBER, AMBER_D, TEAL, TEAL_D, BLUE, BLUE_D,
    WHITE, MUTED, DIM, RED, RED_D, GREEN, GREEN_D,
    MONO, MONOB, SANS, SANSB,
    ease, alpha, lerp, track, finish, draw_caption_pill
)

CAPTIONS = [
    (0,   "your API needs to fetch a user profile on every single request."),
    (60,  "reading from magnetic disk requires mechanical head seeking."),
    (124, "45 milliseconds of I/O latency creates an API bottleneck."),
    (188, "Redis stores key-values directly in electrical DRAM transistors."),
    (250, "0.12 milliseconds. 375x faster responses directly from RAM."),
]

def draw_silicon_ram_module(d, cx, cy, w, h, fr, a):
    """Draws an ultra-clean green silicon PCB RAM stick with surface mount DRAM chips"""
    # Green PCB Board
    d.rectangle([cx - w/2, cy - h/2, cx + w/2, cy + h/2], fill=(12, 28, 20), outline=alpha(TEAL, a), width=2)
    
    # Gold Contact Pins at bottom
    pin_w = 4
    for px in range(int(cx - w/2 + 8), int(cx + w/2 - 8), 7):
        d.rectangle([px, cy + h/2 - 8, px + pin_w, cy + h/2], fill=alpha(AMBER, a * 0.8))
        
    # 4 Black DRAM Silicon Chips on the stick
    chip_w = (w - 36) / 4
    chip_h = h - 28
    for i in range(4):
        chx = cx - w/2 + 10 + i * (chip_w + 5)
        chy = cy - h/2 + 10
        d.rectangle([chx, chy, chx + chip_w, chy + chip_h], fill=(8, 12, 16), outline=alpha(TEAL, a * 0.6), width=1)
        
        # DRAM Text on Chip
        d.text((chx + chip_w/2, chy + chip_h/2), f"DRAM-{i+1}", font=MONO(8), fill=alpha(WHITE, a * 0.7), anchor="mm")
        
        # Glowing electrical activity pulse
        if (fr + i * 4) % 12 < 4:
            d.rectangle([chx + 2, chy + 2, chx + chip_w - 2, chy + chip_h - 2], outline=alpha(TEAL, a * 0.9), width=1)

def draw_magnetic_disk_drive(d, cx, cy, radius, fr, a):
    """Draws a mechanical hard disk with rotating circular platter and actuator arm"""
    # Drive Enclosure Box
    box_w = radius * 2 + 28
    d.rectangle([cx - box_w/2, cy - box_w/2, cx + box_w/2, cy + box_w/2], fill=(16, 20, 28), outline=alpha(AMBER, a), width=2)
    
    # Circular Platter
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(9, 12, 17), outline=alpha(AMBER_D, a), width=2)
    d.ellipse([cx - radius + 12, cy - radius + 12, cx + radius - 12, cy + radius - 12], outline=alpha(DIM, a * 0.4), width=1)
    
    # Spindle Hub (Center)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(24, 30, 42), outline=alpha(WHITE, a * 0.6), width=1)
    
    # Mechanical Actuator Seek Arm swinging back and forth
    arm_angle = math.sin(fr * 0.2) * 22 - 35
    arm_rad = math.radians(arm_angle)
    pivot_x, pivot_y = cx - radius + 10, cy - radius + 10
    head_x = pivot_x + math.cos(arm_rad) * (radius * 1.3)
    head_y = pivot_y + math.sin(arm_rad) * (radius * 1.3)
    
    # Arm Pivot Base
    d.ellipse([pivot_x - 8, pivot_y - 8, pivot_x + 8, pivot_y + 8], fill=(36, 42, 54), outline=alpha(AMBER, a), width=1)
    # Arm Body
    d.line([(pivot_x, pivot_y), (head_x, head_y)], fill=alpha(WHITE, a), width=3)
    # Read/Write Head Tip
    d.ellipse([head_x - 4, head_y - 4, head_x + 4, head_y + 4], fill=alpha(AMBER, a))

def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag

    # ---- Header
    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 184), "IN-MEMORY RAM (0.1ms)  vs  DISK I/O (45ms)", MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    
    tw1 = d.textlength("REDIS ", font=SANSB(42))
    tw2 = d.textlength("CACHE", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 220), "REDIS ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 220), "CACHE", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 256), "why in-memory lookups are 375x faster than disk storage", font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")

    if diag <= 0.01:
        return base

    # ---- Telemetry Speed Meters
    d.line([(64, 320), (220, 320)], fill=alpha(TEAL, a), width=2)
    track(d, (64, 338), "RAM LATENCY (REDIS)", MONOB(11), alpha(MUTED, a), sp=2)
    d.text((64, 368), "0.12 ms", font=MONOB(26), fill=alpha(TEAL, a), anchor="lm")

    d.line([(500, 320), (656, 320)], fill=alpha(AMBER, a), width=2)
    track(d, (656, 338), "DISK LATENCY (DB)", MONOB(11), alpha(MUTED, a), sp=2, anchor="rt")
    d.text((656, 368), "45.0 ms", font=MONOB(26), fill=alpha(AMBER, a), anchor="rm")

    track(d, (W / 2, 330), "PERFORMANCE MULTIPLIER", MONOB(11), alpha(BLUE, a), sp=2, anchor="mm")
    d.text((W / 2, 350), "375x Faster Data Throughput", font=MONOB(14), fill=alpha(GREEN, a), anchor="mm")

    # ---- Center Request Dispatcher Box
    req_y = 410
    d.rectangle([220, req_y, 500, req_y + 50], fill=(12, 16, 24), outline=alpha(BLUE, a), width=2)
    track(d, (360, req_y + 16), "GET /api/users/profile", MONOB(11), alpha(WHITE, a), sp=1, anchor="mm")
    d.text((360, req_y + 34), "Simultaneous Read Query", font=SANS(10), fill=alpha(MUTED, a), anchor="mm")

    # ---- Left Apparatus: Redis Silicon RAM (cx = 200)
    ram_cx, ram_cy = 200, 580
    draw_silicon_ram_module(d, ram_cx, ram_cy, 240, 70, fr, a)
    draw_silicon_ram_module(d, ram_cx, ram_cy + 85, 240, 70, fr + 6, a)
    track(d, (ram_cx, ram_cy + 150), "DRAM MEMORY BUS", MONOB(12), alpha(TEAL, a), sp=2, anchor="mm")
    d.text((ram_cx, ram_cy + 172), "electrical transistor states", font=SANS(11), fill=alpha(MUTED, a), anchor="mm")
    d.text((ram_cx, ram_cy + 190), "O(1) Hash Map Lookup", font=MONO(10), fill=alpha(TEAL_D, a), anchor="mm")

    # ---- Right Apparatus: PostgreSQL Mechanical Disk Drive (cx = 520)
    disk_cx, disk_cy = 520, 615
    draw_magnetic_disk_drive(d, disk_cx, disk_cy, 68, fr, a)
    track(d, (disk_cx, disk_cy + 115), "ROTATING MAGNETIC DISK", MONOB(12), alpha(AMBER, a), sp=2, anchor="mm")
    d.text((disk_cx, disk_cy + 137), "physical head seeks sectors", font=SANS(11), fill=alpha(MUTED, a), anchor="mm")
    d.text((disk_cx, disk_cy + 155), "Mechanical Latency Penalty", font=MONO(10), fill=alpha(AMBER_D, a), anchor="mm")

    # ---- Bottom Speed Comparative Bar
    bar_y = 860
    d.line([(80, bar_y), (640, bar_y)], fill=alpha(DIM, a), width=1)
    track(d, (360, bar_y + 16), "EXECUTION TIME PER 10,000 REQUESTS", MONOB(11), alpha(MUTED, a), sp=1, anchor="mm")
    
    # Progress bars
    d.rectangle([100, bar_y + 36, 100 + 40, bar_y + 54], fill=alpha(TEAL, a))
    d.text((150, bar_y + 45), "Redis: 1.2s", font=MONOB(11), fill=alpha(TEAL, a), anchor="lm")
    
    d.rectangle([100, bar_y + 64, 100 + 450, bar_y + 82], fill=alpha(AMBER, a))
    d.text((560, bar_y + 73), "Disk: 450s", font=MONOB(11), fill=alpha(AMBER, a), anchor="lm")

    # ---- Caption Pill HUD
    draw_caption_pill(d, fr, CAPTIONS, a)

    # ---- Outro Footer
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "CACHE-ASIDE PATTERN · SUB-MILLISECOND LATENCY", MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "REDIS  ·  MEMCACHED  ·  DRAGONFLY  ·  VALKEY", MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base

def render_and_save_frame(args):
    fr, out_dir = args
    img = finish(render(fr), fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))

if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_redis_vs_db"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered Redis vs DB frames: {len(frames)}")
