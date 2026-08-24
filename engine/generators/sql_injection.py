#!/usr/bin/env python3
"""
Flagship System Design Reel: SQL Injection (How ' OR 1=1 -- Breaches the Database)
Ultra-polished isometric blueprint with circuit traces, animated parser gears,
emergency alarm flasher, and rich particle dynamics.
720x1280 @ 30fps, 10s (300 frames).
"""
import os, sys, math, hashlib
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from blueprint_engine import (
    W, H, FPS, DUR, NF, BG, AMBER, AMBER_D, TEAL, TEAL_D, BLUE, BLUE_D,
    WHITE, MUTED, DIM, RED, RED_D, GREEN, GREEN_D,
    MONO, MONOB, SANS, SANSB,
    ease, alpha, lerp, track, panel, screen, finish, draw_caption_pill
)

CAPTIONS = [
    (0,   "a hacker enters ' OR 1=1 -- into the login username field."),
    (60,  "raw string concatenation merges code with user input."),
    (124, "the SQL parser interprets 1=1 as always TRUE."),
    (188, "auth check bypasses! the database dumps all 100,000 users."),
    (250, "prepared statements parameterize input so code never executes."),
]

def draw_isometric_server_rack(d, cx, cy, w, h, depth, is_breached, fr, a):
    """Draws a rich 3D isometric database server rack with blinking LED arrays and drive bays"""
    col = RED if is_breached else TEAL
    base_col = (14, 18, 26) if not is_breached else (28, 14, 16)
    
    # Front Face
    d.rectangle([cx - w/2, cy - h/2, cx + w/2, cy + h/2], fill=base_col, outline=alpha(col, a), width=2)
    
    # Top 3D Face
    top_poly = [
        (cx - w/2, cy - h/2),
        (cx - w/2 + depth, cy - h/2 - depth * 0.5),
        (cx + w/2 + depth, cy - h/2 - depth * 0.5),
        (cx + w/2, cy - h/2)
    ]
    d.polygon(top_poly, fill=(22, 28, 38) if not is_breached else (38, 20, 22), outline=alpha(col, a * 0.7))
    
    # Right 3D Face
    right_poly = [
        (cx + w/2, cy - h/2),
        (cx + w/2 + depth, cy - h/2 - depth * 0.5),
        (cx + w/2 + depth, cy + h/2 - depth * 0.5),
        (cx + w/2, cy + h/2)
    ]
    d.polygon(right_poly, fill=(18, 22, 30) if not is_breached else (32, 16, 18), outline=alpha(col, a * 0.7))
    
    # Server Drive Slots (4 Rack Units)
    num_slots = 4
    slot_h = (h - 24) / num_slots
    for s in range(num_slots):
        sy = cy - h/2 + 12 + s * slot_h
        d.rectangle([cx - w/2 + 8, sy, cx + w/2 - 8, sy + slot_h - 4], fill=(9, 12, 17), outline=alpha(col, a * 0.5), width=1)
        
        # Blinking LED lights on each drive
        for led in range(4):
            lx = cx - w/2 + 18 + led * 14
            ly = sy + slot_h / 2 - 2
            is_lit = ((fr + s * 3 + led * 5) % 8 < 4) or is_breached
            led_col = RED if is_breached else (GREEN if led < 3 else AMBER)
            d.ellipse([lx - 2, ly - 2, lx + 2, ly + 2], fill=alpha(led_col if is_lit else DIM, a))
        
        # Drive vent slits
        for vx in range(int(cx), int(cx + w/2 - 16), 8):
            d.line([(vx, sy + 4), (vx, sy + slot_h - 8)], fill=alpha(DIM, a * 0.6), width=1)

def draw_circuit_traces(d, x1, y1, x2, y2, color, a, pulse_pos=0.0):
    """Draws glowing 90-degree circuit traces with pulsing packet orbs"""
    mid_x = (x1 + x2) / 2
    d.line([(x1, y1), (mid_x, y1)], fill=alpha(color, a * 0.35), width=2)
    d.line([(mid_x, y1), (mid_x, y2)], fill=alpha(color, a * 0.35), width=2)
    d.line([(mid_x, y2), (x2, y2)], fill=alpha(color, a * 0.35), width=2)
    
    # Pulsing glowing packet along the trace
    if 0.0 <= pulse_pos <= 1.0:
        if pulse_pos < 0.33:
            t = pulse_pos / 0.33
            px, py = lerp(x1, mid_x, t), y1
        elif pulse_pos < 0.66:
            t = (pulse_pos - 0.33) / 0.33
            px, py = mid_x, lerp(y1, y2, t)
        else:
            t = (pulse_pos - 0.66) / 0.34
            px, py = lerp(mid_x, x2, t), y2
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=alpha(color, a))

def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag

    # SQL Injection Timeline:
    # 0s - 3s (fr 0 - 90): User inputs standard login 'admin'
    # 3s - 6s (fr 90 - 180): Malicious payload enters: ' OR 1=1 --
    # 6s - 8s (fr 180 - 240): Parser evaluates 1=1 -> TRUE, ALARM TRIPS (RED), Data leak!
    # 8s - 10s (fr 240 - 300): Mitigation: Prepared Statement Parameterization

    is_malicious = (fr >= 85)
    is_breached = (fr >= 170)
    is_mitigated = (fr >= 245)

    # ---- Header HUD
    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 184), "STRING CONCAT  vs  PREPARED STATEMENTS", MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    
    tw1 = d.textlength("SQL ", font=SANSB(42))
    tw2 = d.textlength("INJECTION", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 220), "SQL ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 220), "INJECTION", font=SANSB(42), fill=alpha(RED if is_breached else TEAL, intro), anchor="lm")
    d.text((W / 2, 256), "how one rogue quote bypasses authentication entirely", font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")

    if diag <= 0.01:
        return base

    # ---- Telemetry Status Cards
    status_text = "SYSTEM BREACHED" if is_breached else ("QUERY PARSING" if is_malicious else "AUTH SECURE")
    status_col = RED if is_breached else (AMBER if is_malicious else GREEN)
    
    d.line([(64, 320), (220, 320)], fill=alpha(status_col, a), width=2)
    track(d, (64, 338), "AUTH STATUS", MONOB(11), alpha(MUTED, a), sp=2)
    d.text((64, 368), status_text, font=MONOB(18), fill=alpha(status_col, a), anchor="lm")

    leaked_count = 100000 if is_breached else 0
    d.line([(500, 320), (656, 320)], fill=alpha(status_col, a), width=2)
    track(d, (656, 338), "ROWS DUMPED", MONOB(11), alpha(MUTED, a), sp=2, anchor="rt")
    d.text((656, 368), f"{leaked_count:,}" if is_breached else "0 ROWS", font=MONOB(22), fill=alpha(status_col, a), anchor="rm")

    track(d, (W / 2, 330), "VULNERABILITY VECTOR", MONOB(11), alpha(BLUE, a), sp=2, anchor="mm")
    d.text((W / 2, 350), "Raw String Interpolation: $sql = \"...\" + input", font=MONO(10), fill=alpha(MUTED, a), anchor="mm")

    # ---- 1. Input Box (Top Browser Terminal)
    in_box_y = 410
    d.rectangle([100, in_box_y, 620, in_box_y + 60], fill=(12, 15, 22), outline=alpha(AMBER if is_malicious else BLUE, a), width=2)
    track(d, (116, in_box_y + 14), "INPUT: USERNAME FIELD", MONOB(10), alpha(MUTED, a), sp=1)
    
    # Input typing simulation
    if not is_malicious:
        input_str = "admin"
        in_col = WHITE
    else:
        full_payload = "admin' OR 1=1 --"
        type_prog = min(len(full_payload), int((fr - 85) / 3))
        input_str = full_payload[:type_prog]
        in_col = RED if is_breached else AMBER
    
    cursor = " █" if (fr % 16 < 8) else ""
    d.text((116, in_box_y + 40), input_str + cursor, font=MONOB(16), fill=alpha(in_col, a), anchor="lm")

    # ---- Circuit Traces down to Parser
    pulse = ((fr * 0.05) % 1.0)
    draw_circuit_traces(d, 360, in_box_y + 60, 360, 520, RED if is_breached else TEAL, a, pulse)

    # ---- 2. SQL Parser Engine Machine (Center Box)
    parser_y = 520
    d.rectangle([80, parser_y, 640, parser_y + 110], fill=(9, 12, 17), outline=alpha(RED if is_breached else BLUE, a), width=2)
    track(d, (360, parser_y + 16), "SQL QUERY PARSER & AST EVALUATOR", MONOB(11), alpha(BLUE, a), sp=2, anchor="mm")

    # The Executed SQL Query String
    if not is_malicious:
        sql_display = "SELECT * FROM users WHERE user = 'admin' AND pass = '...'"
    elif not is_breached:
        sql_display = "SELECT * FROM users WHERE user = '" + input_str + "' AND pass = '...'"
    else:
        sql_display = "SELECT * FROM users WHERE user = 'admin' OR 1=1 -- AND pass = '...'"

    d.text((360, parser_y + 48), sql_display[:46], font=MONO(11), fill=alpha(WHITE, a), anchor="mm")
    if len(sql_display) > 46:
        d.text((360, parser_y + 68), sql_display[46:], font=MONO(11), fill=alpha(RED if is_breached else AMBER, a), anchor="mm")

    # Boolean Evaluation Tag
    if is_breached:
        d.rectangle([250, parser_y + 82, 470, parser_y + 104], fill=(36, 12, 14), outline=alpha(RED, a), width=1)
        track(d, (360, parser_y + 93), "EVAL: 1=1 IS TRUE (BYPASS)", MONOB(10), alpha(RED, a), sp=1, anchor="mm")
    else:
        d.rectangle([250, parser_y + 82, 470, parser_y + 104], fill=(14, 26, 20), outline=alpha(TEAL, a), width=1)
        track(d, (360, parser_y + 93), "EVAL: AWAITING CREDENTIALS", MONOB(10), alpha(TEAL, a), sp=1, anchor="mm")

    # ---- Circuit Traces down to 3D Database Servers
    draw_circuit_traces(d, 220, parser_y + 110, 220, 710, RED if is_breached else TEAL, a, (pulse + 0.3) % 1.0)
    draw_circuit_traces(d, 500, parser_y + 110, 500, 710, RED if is_breached else TEAL, a, (pulse + 0.7) % 1.0)

    # ---- 3. Dual 3D Isometric Database Server Racks (Bottom Left & Right)
    draw_isometric_server_rack(d, 220, 780, 180, 130, 24, is_breached, fr, a)
    draw_isometric_server_rack(d, 500, 780, 180, 130, 24, is_breached, fr + 15, a)

    track(d, (220, 870), "USER DB CLUSTER #1", MONOB(11), alpha(WHITE, a), sp=1, anchor="mm")
    track(d, (500, 870), "USER DB CLUSTER #2", MONOB(11), alpha(WHITE, a), sp=1, anchor="mm")

    if is_breached:
        track(d, (220, 890), "TABLE DUMP: EXFILTRATING", MONO(10), alpha(RED, a), sp=1, anchor="mm")
        track(d, (500, 890), "CREDENTIALS COMPROMISED", MONO(10), alpha(RED, a), sp=1, anchor="mm")
    else:
        track(d, (220, 890), "ACCESS LOCKED (0 READS)", MONO(10), alpha(GREEN, a), sp=1, anchor="mm")
        track(d, (500, 890), "ACCESS LOCKED (0 READS)", MONO(10), alpha(GREEN, a), sp=1, anchor="mm")

    # ---- Caption Pill HUD
    draw_caption_pill(d, fr, CAPTIONS, a)

    # ---- Mitigation Outro Footer
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "FIX: PREPARED STATEMENTS & PARAMETER BINDING", MONOB(11), alpha(GREEN, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "PDO  ·  PRISMA  ·  SQLX  ·  HIBERNATE ORM", MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base

def render_and_save_frame(args):
    fr, out_dir = args
    img = finish(render(fr), fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))

if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_sql_injection"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered SQL Injection frames: {len(frames)}")
