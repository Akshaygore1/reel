#!/usr/bin/env python3
"""
Flagship System Design Reel: Kafka Partitions & Consumer Groups
Visual Apparatus: Multi-Lane Commit Log Conveyor Belts (P-0, P-1, P-2) with Laser Consumer Worker Fleet.
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
    ease, alpha, lerp, track, finish, draw_caption_pill
)

CAPTIONS = [
    (0,   "a single consumer queue processes events strictly one at a time."),
    (60,  "traffic spikes create massive consumer lag and head-of-line blocking."),
    (124, "52,400 unread messages pile up behind the single worker bottleneck."),
    (188, "Kafka partitions the commit log across parallel consumer group workers."),
    (250, "zero lag. 1.2 million events processed in parallel with strict order."),
]

def draw_partition_track(d, cx, cy, w, h, p_idx, fr, is_spike, is_scaled, a):
    """Draws a single horizontal Kafka Partition append-only commit log track"""
    half_w = w / 2
    half_h = h / 2
    x0, y0, x1, y1 = cx - half_w, cy - half_h, cx + half_w, cy + half_h
    
    # Track Background & Outer Frame
    track_col = RED if (is_spike and not is_scaled) else (TEAL if is_scaled else BLUE)
    d.rectangle([x0, y0, x1, y1], fill=(10, 14, 20), outline=alpha(track_col, a * 0.7), width=2)
    
    # Moving Log Segment Blocks (Offsets)
    block_w = 70
    num_blocks = 6
    speed = 4.2 if (is_scaled or is_spike) else 1.8
    scroll = (fr * speed + p_idx * 25) % (block_w + 8)
    base_offset = 1000 * (p_idx + 1) + int((fr * speed) / 20)
    
    log_area_x0 = x0 + 82
    log_area_x1 = x1 - 8
    
    # Draw blocks
    for i in range(-1, num_blocks + 2):
        bx0 = log_area_x0 + i * (block_w + 8) - scroll
        bx1 = bx0 + block_w
        if bx1 <= log_area_x0 or bx0 >= log_area_x1:
            continue
        
        draw_bx0 = max(log_area_x0, bx0)
        draw_bx1 = min(log_area_x1, bx1)
        
        block_off = base_offset + i
        is_active = (i == 2)
        b_col = track_col if not (is_spike and not is_scaled) else RED
        
        # Sub-rectangle for each message payload
        d.rectangle([draw_bx0, y0 + 6, draw_bx1, y1 - 6], 
                    fill=(16, 22, 32) if not is_active else (24, 34, 50),
                    outline=alpha(b_col, a * (0.9 if is_active else 0.4)), width=1)
        
        mid_x = (bx0 + bx1) / 2
        if mid_x - 24 > log_area_x0 and mid_x + 24 < log_area_x1:
            d.text((mid_x, cy - 6), f"off:{block_off}", font=MONO(9), fill=alpha(WHITE if is_active else MUTED, a * 0.9), anchor="mm")
            d.text((mid_x, cy + 9), f"k:u_{p_idx*3+i%3}", font=MONO(8), fill=alpha(TEAL_D if is_scaled else DIM, a * 0.8), anchor="mm")

    # High Watermark line (HWM)
    hwm_x = x0 + 82 + 2 * (block_w + 8) + 10
    d.line([(hwm_x, y0 + 2), (hwm_x, y1 - 2)], fill=alpha(AMBER if not is_scaled else GREEN, a), width=2)
    d.text((hwm_x + 4, y0 + 8), "HWM", font=MONO(7), fill=alpha(AMBER if not is_scaled else GREEN, a * 0.8), anchor="lm")

    # Partition Header Tag (Left - Drawn on top with solid backing to prevent bleed)
    d.rectangle([x0, y0, x0 + 78, y1], fill=(14, 18, 26), outline=alpha(track_col, a), width=1)
    d.text((x0 + 39, cy - 8), f"PART-{p_idx}", font=MONOB(11), fill=alpha(WHITE, a), anchor="mm")
    d.text((x0 + 39, cy + 10), "LEADER", font=MONO(8), fill=alpha(MUTED, a * 0.8), anchor="mm")

def draw_consumer_node(d, cx, cy, w, h, c_idx, assigned_p, is_active, is_lagging, fr, a):
    """Draws a dedicated consumer worker container box with scanning laser head"""
    half_w = w / 2
    half_h = h / 2
    x0, y0, x1, y1 = cx - half_w, cy - half_h, cx + half_w, cy + half_h
    
    col = RED if is_lagging else (GREEN if is_active else DIM)
    
    # Outer consumer card
    d.rectangle([x0, y0, x1, y1], fill=(12, 16, 24), outline=alpha(col, a), width=2)
    
    # Top Status Bar
    status_text = "LAG OVERLOAD" if is_lagging else ("STREAMING" if is_active else "IDLE / STANDBY")
    d.rectangle([x0, y0, x1, y0 + 20], fill=(18, 24, 36), outline=alpha(col, a * 0.5), width=1)
    d.text((cx, y0 + 10), f"CONSUMER {c_idx+1}", font=MONOB(10), fill=alpha(WHITE, a), anchor="mm")
    
    # Content Labels
    d.text((cx, cy + 5), f"Assigned: P-{assigned_p}" if assigned_p is not None else "Unassigned", 
           font=MONO(9), fill=alpha(TEAL if is_active else MUTED, a), anchor="mm")
    d.text((cx, cy + 20), status_text, font=MONOB(9), fill=alpha(col, a), anchor="mm")
    
    # Activity Blip / Pulse LED
    led_col = RED if is_lagging else (GREEN if is_active else DIM)
    led_pulse = (math.sin(fr * 0.4 + c_idx) * 0.5 + 0.5) if is_active else 0.2
    d.ellipse([x0 + 8, y0 + 6, x0 + 16, y0 + 14], fill=alpha(led_col, a * led_pulse))

def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag

    # ---- Header Bar
    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 184), "SINGLE CONSUMER (LAG 52k)  vs  3x PARTITIONS (LAG 0)", MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    
    tw1 = d.textlength("KAFKA ", font=SANSB(42))
    tw2 = d.textlength("PARTITIONS", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 220), "KAFKA ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 220), "PARTITIONS", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 256), "why partitioned consumer groups process 1.2M events/sec", font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")

    if diag <= 0.01:
        return base

    # Timeline beats:
    # Beat 1 (0s - 3s / 0 - 90): Normal 1-partition flow, 1 consumer
    # Beat 2 (3s - 6s / 90 - 180): Traffic surges 10x! 1 consumer stalls, 52,400 lag, red alarm
    # Beat 3 (6s - 10s / 180 - 300): Kafka consumer group spins up C-2, C-3, lag drops to 0!
    is_spike = (fr >= 90)
    is_scaled = (fr >= 180)
    rebalance_prog = ease((fr - 165) / 30) if fr >= 165 else 0.0

    # ---- Telemetry HUD Cards
    # Left: Consumer Lag
    if not is_spike:
        lag_val = "42 msgs"
        lag_col = TEAL
    elif not is_scaled:
        lag_count = int(lerp(42, 52400, ease((fr - 90) / 45)))
        lag_val = f"{lag_count:,} msgs"
        lag_col = RED
    else:
        lag_count = int(lerp(52400, 0, ease((fr - 180) / 35)))
        lag_val = f"{lag_count:,} msgs"
        lag_col = GREEN if lag_count == 0 else AMBER

    d.line([(64, 316), (230, 316)], fill=alpha(lag_col, a), width=2)
    track(d, (64, 334), "CONSUMER GROUP LAG", MONOB(11), alpha(MUTED, a), sp=2)
    d.text((64, 364), lag_val, font=MONOB(24), fill=alpha(lag_col, a), anchor="lm")

    # Right: Throughput
    if not is_spike:
        tp_val = "15k msg/s"
        tp_col = BLUE
    elif not is_scaled:
        tp_val = "18k msg/s (STALL)"
        tp_col = RED
    else:
        tp_val = "1.2M msg/s"
        tp_col = GREEN

    d.line([(490, 316), (656, 316)], fill=alpha(tp_col, a), width=2)
    track(d, (656, 334), "TOTAL THROUGHPUT", MONOB(11), alpha(MUTED, a), sp=2, anchor="rt")
    d.text((656, 364), tp_val, font=MONOB(22), fill=alpha(tp_col, a), anchor="rm")

    # Center Tag
    track(d, (W / 2, 326), "TOPIC ARCHITECTURE", MONOB(11), alpha(BLUE, a), sp=2, anchor="mm")
    d.text((W / 2, 348), "3 Partitions · Strict Key Ordering", font=MONOB(13), fill=alpha(GREEN if is_scaled else WHITE, a), anchor="mm")

    # ---- Top Producer Router Box (Y = 405)
    prod_y = 405
    d.rectangle([140, prod_y, 580, prod_y + 44], fill=(14, 20, 28), outline=alpha(BLUE, a), width=2)
    track(d, (W / 2, prod_y + 14), "PRODUCER: orders.checkout", MONOB(11), alpha(WHITE, a), sp=2, anchor="mm")
    d.text((W / 2, prod_y + 30), "murmur2(key) % 3 -> [P-0, P-1, P-2]", font=MONO(9), fill=alpha(MUTED, a), anchor="mm")

    # 3 Route Guide Lines from Producer to the 3 Partitions
    p_ys = [500, 580, 660]
    p_cols = [TEAL, BLUE, AMBER]
    for idx, py in enumerate(p_ys):
        # Feeder curve line
        d.line([(220 + idx * 140, prod_y + 44), (220 + idx * 140, py - 30)], fill=alpha(DIM, a * 0.6), width=1)
        d.line([(220 + idx * 140, py - 30), (100, py - 30)], fill=alpha(DIM, a * 0.6), width=1)
        d.line([(100, py - 30), (100, py - 20)], fill=alpha(DIM, a * 0.6), width=1)
        
        # Animated ingress packet
        pkt_t = ((fr * 0.08 + idx * 0.33) % 1.0)
        pkt_y = prod_y + 44 + pkt_t * (py - prod_y - 44)
        d.ellipse([220 + idx * 140 - 3, pkt_y - 3, 220 + idx * 140 + 3, pkt_y + 3], fill=alpha(p_cols[idx], a * 0.9))

    # ---- Middle Stage: 3 Kafka Partition Tracks
    track_w = 600
    track_h = 58
    for idx, py in enumerate(p_ys):
        draw_partition_track(d, W / 2, py, track_w, track_h, idx, fr, is_spike, is_scaled, a)

    # ---- Bottom Stage: Consumer Group Fleet (Y = 760 to 920)
    cg_box_y = 760
    d.rectangle([40, cg_box_y, 680, 920], fill=(8, 12, 18), outline=alpha(GREEN if is_scaled else (RED if is_spike else BLUE), a * 0.6), width=1)
    
    # Header tag for consumer group box
    d.rectangle([180, cg_box_y, 540, cg_box_y + 22], fill=(16, 22, 32), outline=alpha(GREEN if is_scaled else (RED if is_spike else BLUE), a * 0.8), width=1)
    track(d, (W / 2, cg_box_y + 11), "CONSUMER GROUP: 'order-processors'", MONOB(10), alpha(GREEN if is_scaled else WHITE, a), sp=2, anchor="mm")

    # Consumers Layout
    c_w = 190
    c_h = 86
    c_xs = [150, 360, 570]
    c_y = 852

    if not is_scaled:
        # Single Consumer (C-1) centered
        draw_consumer_node(d, 360, c_y, 280, c_h, 0, 0 if not is_spike else "ALL (OVERLOAD)", 
                           is_active=True, is_lagging=is_spike, fr=fr, a=a)
        
        # Read laser beam from Partition 0 (or all) to Consumer 1
        laser_col = RED if is_spike else TEAL
        target_py = p_ys[0] if not is_spike else p_ys[1]
        d.line([(360, target_py + 29), (360, c_y - c_h/2)], fill=alpha(laser_col, a * (0.8 + 0.2 * math.sin(fr * 0.5))), width=2)
        
        if is_spike:
            # Overload alarm box over consumer
            d.rectangle([210, cg_box_y + 26, 510, cg_box_y + 48], fill=(36, 12, 18), outline=alpha(RED, a), width=1)
            d.text((360, cg_box_y + 37), "SINGLE WORKER BOTTLENECK", font=MONOB(10), fill=alpha(RED, a), anchor="mm")
    else:
        # 3 Consumers in Parallel!
        for c_idx in range(3):
            cx = c_xs[c_idx]
            draw_consumer_node(d, cx, c_y, c_w, c_h, c_idx, c_idx, is_active=True, is_lagging=False, fr=fr, a=a)
            
            # Laser beams directly connecting each partition to its dedicated consumer
            p_center_x = 420 + (c_idx - 1) * 60
            d.line([(p_center_x, p_ys[c_idx] + 29), (cx, c_y - c_h/2)], fill=alpha(GREEN, a * (0.7 + 0.3 * math.sin(fr * 0.4 + c_idx))), width=2)

    # ---- Bottom Caption Pill HUD
    draw_caption_pill(d, fr, CAPTIONS, a)

    # ---- Outro Footer
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "HORIZONTAL SCALABILITY · ZERO CONSUMER LOCKING", MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "KAFKA  ·  REDIS STREAMS  ·  AWS KINESIS  ·  RABBITMQ STREAMS", MONO(9), alpha(DIM, o), sp=1, anchor="mm")

    return base

def render_and_save_frame(args):
    fr, out_dir = args
    img = finish(render(fr), fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))

if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_kafka_partitions"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered Kafka Partitions frames: {len(frames)}")
