#!/usr/bin/env python3
"""
Cron Jobs — 24-hour rotating clock dial with 5 sliding gate tracks.
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
    (0,   "a cron expression is 5 mechanical sliding gates."),
    (60,  "minute · hour · day of month · month · day of week."),
    (124, "every 60 seconds, the clock hand advances one notch."),
    (188, "when all 5 gates align, the trapdoor clicks open."),
    (250, "0 0 * * * fires your backup script at midnight sharp."),
]

def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag

    # ---- Header
    d.text((W / 2, 168), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 192), "* * * * * (EVERY MIN)  vs  0 0 * * * (MIDNIGHT)", MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    
    tw1 = d.textlength("CRON ", font=SANSB(42))
    tw2 = d.textlength("JOBS", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 228), "CRON ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 228), "JOBS", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "how the Linux scheduler evaluates 5 time dimensions", font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")

    if diag <= 0.01:
        return base

    # Alignment trigger at frame 180 (Midnight 00:00:00)
    is_aligned = (fr >= 180)

    # ---- Counters Row
    d.line([(64, 340), (220, 340)], fill=alpha(AMBER, a), width=2)
    track(d, (64, 358), "CRON EXPRESSION", MONOB(11), alpha(MUTED, a), sp=2)
    d.text((64, 388), "0 0 * * *", font=MONOB(26), fill=alpha(AMBER, a), anchor="lm")

    d.line([(500, 340), (656, 340)], fill=alpha(GREEN if is_aligned else TEAL, a), width=2)
    track(d, (656, 358), "TRIGGER STATE", MONOB(11), alpha(MUTED, a), sp=2, anchor="rt")
    d.text((656, 388), "FIRED (200)" if is_aligned else "WAITING", font=MONOB(24), fill=alpha(GREEN if is_aligned else TEAL, a), anchor="rm")

    track(d, (W / 2, 350), "DAEMON TICK", MONOB(12), alpha(BLUE, a), sp=3, anchor="mm")
    d.text((W / 2, 370), "23:59:59 -> 00:00:00" if is_aligned else "evaluating every 60s", font=SANS(12), fill=alpha(WHITE if is_aligned else MUTED, a), anchor="mm")

    # ---- 1. 24-Hour Rotating Clockwork Dial (Left Side)
    clock_cx, clock_cy, clock_r = 210, 600, 130
    d.ellipse([clock_cx - clock_r, clock_cy - clock_r, clock_cx + clock_r, clock_cy + clock_r],
              outline=alpha(TEAL, a), width=2)
    d.ellipse([clock_cx - clock_r + 14, clock_cy - clock_r + 14, clock_cx + clock_r - 14, clock_cy + clock_r - 14],
              outline=alpha(DIM, a * 0.5), width=1)

    # Clock Hour Notches & Roman numbers
    for h_tick in range(12):
        rad = math.radians(h_tick * 30 - 90)
        p1x = clock_cx + math.cos(rad) * (clock_r - 12)
        p1y = clock_cy + math.sin(rad) * (clock_r - 12)
        p2x = clock_cx + math.cos(rad) * clock_r
        p2y = clock_cy + math.sin(rad) * clock_r
        d.line([(p1x, p1y), (p2x, p2y)], fill=alpha(WHITE, a), width=2)

    # Rotating Sweeping Clock Hand (Reaches 12 o'clock Midnight at fr 180)
    sweep_deg = (fr * 2.0) % 360 if not is_aligned else 0
    hand_rad = math.radians(sweep_deg - 90)
    hx = clock_cx + math.cos(hand_rad) * (clock_r - 20)
    hy = clock_cy + math.sin(hand_rad) * (clock_r - 20)
    d.line([(clock_cx, clock_cy), (hx, hy)], fill=alpha(AMBER, a), width=3)
    d.ellipse([clock_cx - 6, clock_cy - 6, clock_cx + 6, clock_cy + 6], fill=alpha(WHITE, a))

    track(d, (clock_cx, clock_cy + clock_r + 24), "24-HOUR TICK DIAL", MONOB(10), alpha(MUTED, a), sp=1, anchor="mm")

    # ---- 2. 5 Sliding Mechanical Gate Rails (Right Side)
    gate_labels = [
        ("MIN",  "0",  "0-59"),
        ("HOUR", "0",  "0-23"),
        ("DOM",  "*",  "1-31"),
        ("MON",  "*",  "1-12"),
        ("DOW",  "*",  "0-6")
    ]
    
    start_gx = 420
    start_gy = 480
    gate_w = 230
    gate_h = 36

    for idx, (g_name, g_val, g_range) in enumerate(gate_labels):
        gy = start_gy + idx * 48
        is_gate_open = is_aligned or (idx >= 2 and g_val == "*")
        g_col = GREEN if is_gate_open else (AMBER if is_aligned else DIM)

        # Rail track
        d.rectangle([start_gx, gy, start_gx + gate_w, gy + gate_h],
                    fill=(9, 12, 17), outline=alpha(g_col, a), width=1)
        
        # Sliding Gate Lock
        slider_x = start_gx + (gate_w - 60 if is_gate_open else 20)
        d.rectangle([slider_x, gy + 3, slider_x + 50, gy + gate_h - 3],
                    fill=alpha(g_col, 0.4), outline=alpha(g_col, 0.9), width=1)

        track(d, (start_gx + 12, gy + 18), f"{g_name}: {g_val}", MONOB(11), alpha(WHITE, a), sp=1, anchor="lm")
        d.text((start_gx + gate_w - 10, gy + 18), "MATCH" if is_gate_open else g_range, font=MONO(9), fill=alpha(g_col, a), anchor="rm")

    # ---- Laser Trigger Pulse Downward when Aligned
    if is_aligned:
        d.line([(start_gx + gate_w / 2, start_gy + 5 * 48), (start_gx + gate_w / 2, 790)],
               fill=alpha(GREEN, a), width=3)
        track(d, (start_gx + gate_w / 2, 810), "⚡ TRIGGER: /scripts/backup.sh", MONOB(11), alpha(GREEN, a), sp=1, anchor="mm")

    # ---- Lower Caption Pill & Outro
    draw_caption_pill(d, fr, CAPTIONS, a)

    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "CRONTAB · SYSTEMD TIMERS · KUBERNETES CRONJOB", MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "LINUX  ·  AWS EVENTBRIDGE  ·  CELERY BEAT", MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base

def render_and_save_frame(args):
    fr, out_dir = args
    img = finish(render(fr), fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))

if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_cron_jobs"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered Cron Jobs frames: {len(frames)}")
