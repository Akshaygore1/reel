#!/usr/bin/env python3
"""
Streaming Response (SSE / Chunked Transfer) vs Direct Response (Buffered HTTP).
Dual Dispatcher Architecture comparing:
1. STREAMING DISPATCHER (Top): GPU Autoregressive Tokenizer -> SSE Conduit -> Real-Time ChatGPT UI typing.
2. DIRECT DISPATCHER (Bottom): LLM RAM Buffer -> Locked Gate (8s wait) -> BOOM 100% Instant Text Dump.

Narrative:
- Beat 1 (0.0s - 3.0s | Frames 0 - 90): Streaming delivers immediate 38ms TTFB, words stream token-by-token.
- Beat 2 (3.0s - 6.0s | Frames 90 - 180): Direct HTTP locks up in buffer, UI is blank with a 10s wait -> Alert Buzzer.
- Beat 3 (6.0s - 10.0s | Frames 180 - 300): Ting-Tong chime; at 8.0s BOOM gate opens and dumps 100% text all at once!
"""
import os, sys, math
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from blueprint_engine import (
    W, H, FPS, NF, BG, WHITE, MUTED, DIM, TEAL, AMBER, RED, GREEN, BLUE,
    MONO, MONOB, SANS, SANSB, alpha, lerp, draw_header_bar, draw_telemetry_hud, draw_caption_pill, finish
)

CAPTIONS = [
    (0, "Streaming (SSE): flushes words token-by-token in 38ms"),
    (90, "Direct (Buffered): holds full response in RAM — UI is frozen"),
    (180, "BOOM! Direct dumps all text at once at 8.4s (high drop-off)")
]

STREAM_WORDS = [
    "Quantum", "computing", "uses", "qubits", "in",
    "superposition", "to", "solve", "exponential", "problems",
    "millions", "of", "times", "faster", "than", "classical",
    "silicon", "chips."
]

def render(fr):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    t = fr / FPS

    # 1. Header Bar with @buildebugship Branding
    draw_header_bar(
        d, 1.0, handle="@buildebugship",
        comp_left="STREAMING (SSE)", comp_right="DIRECT (BUFFERED)",
        title1="STREAMING", title_vs="vs", title2="DIRECT",
        subhook="why ChatGPT streams token-by-token instead of waiting 10s"
    )

    # 2. Telemetry HUD Cards (Y: 304 - 380)
    if fr < 90:
        draw_telemetry_hud(d, "STREAMING TTFB", "38 ms (INSTANT)", "TRANSFER PROTOCOL", "text/event-stream", 1.0, TEAL, BLUE)
    elif fr < 180:
        flicker = 1.0 if (fr // 4 % 2 == 0) else 0.4
        direct_elapsed = f"{t:.1f}s"
        draw_telemetry_hud(d, "DIRECT LATENCY", f"{direct_elapsed} WAITING...", "USER DROP-OFF", "68% BOUNCE RISK", flicker, RED, RED)
    elif fr < 240:
        draw_telemetry_hud(d, "STREAMING SPEED", "60 TOKENS / SEC", "DIRECT BUFFER", "92% ACCUMULATED", 1.0, GREEN, AMBER)
    else:
        draw_telemetry_hud(d, "STREAMING TTFB", "38 ms (OPTIMAL)", "DIRECT DUMP", "BOOM! 100% AT 8.4s", 1.0, GREEN, TEAL)

    # -------------------------------------------------------------
    # 3. TOP STAGE: STREAMING DISPATCHER (Y: 395 - 655)
    # -------------------------------------------------------------
    top_y0, top_y1 = 395, 655
    streaming_glow = GREEN if fr >= 180 else TEAL
    d.rounded_rectangle([38, top_y0, W - 38, top_y1], radius=10, fill=(11, 15, 23), outline=alpha(streaming_glow, 0.7), width=1)
    
    # Header tag for Streaming Panel
    d.rectangle([38, top_y0, W - 38, top_y0 + 26], fill=(15, 22, 34), outline=alpha(DIM, 0.5), width=1)
    d.ellipse([52, top_y0 + 8, 62, top_y0 + 18], fill=GREEN)
    d.text((70, top_y0 + 13), "1. STREAMING DISPATCHER (SSE / CHUNKED TRANSFER)", font=MONOB(10), fill=WHITE, anchor="lm")
    d.text((W - 52, top_y0 + 13), "TTFB: 38ms", font=MONOB(9), fill=GREEN, anchor="rm")

    # Top Left: LLM / GPU Dispatcher Box
    d_x0, d_y0, d_x1, d_y1 = 52, top_y0 + 36, 172, top_y1 - 12
    d.rounded_rectangle([d_x0, d_y0, d_x1, d_y1], radius=6, fill=(14, 19, 30), outline=alpha(TEAL, 0.8), width=1)
    d.text(((d_x0 + d_x1) / 2, d_y0 + 16), "GPU / LLM", font=MONOB(10), fill=TEAL, anchor="mm")
    d.text(((d_x0 + d_x1) / 2, d_y0 + 30), "DISPATCHER", font=MONO(8), fill=MUTED, anchor="mm")
    
    # Mini attention grid inside GPU
    for r in range(3):
        for c in range(3):
            gc_x = d_x0 + 14 + c * 34
            gc_y = d_y0 + 44 + r * 22
            is_lit = ((int(t * 8) + r + c) % 4 == 0)
            cell_c = GREEN if is_lit else (20, 28, 42)
            d.rounded_rectangle([gc_x, gc_y, gc_x + 26, gc_y + 16], radius=2, fill=cell_c, outline=alpha(TEAL, 0.3), width=1)
            if is_lit:
                d.text((gc_x + 13, gc_y + 8), "Δw", font=MONO(7), fill=(10, 14, 20), anchor="mm")

    d.rectangle([d_x0 + 10, d_y1 - 28, d_x1 - 10, d_y1 - 8], fill=(18, 26, 38), outline=alpha(GREEN, 0.6), width=1)
    d.text(((d_x0 + d_x1) / 2, d_y1 - 18), "FLUSH CHUNK", font=MONOB(8), fill=GREEN, anchor="mm")

    # Top Right: ChatGPT Client UI (Words Stream Live)
    c_x0, c_y0, c_x1, c_y1 = 390, top_y0 + 36, W - 52, top_y1 - 12
    d.rounded_rectangle([c_x0, c_y0, c_x1, c_y1], radius=6, fill=(12, 17, 26), outline=alpha(GREEN, 0.8), width=1)
    
    # ChatGPT client title inside box
    d.rectangle([c_x0, c_y0, c_x1, c_y0 + 22], fill=(16, 23, 36), outline=alpha(DIM, 0.4), width=1)
    d.ellipse([c_x0 + 10, c_y0 + 6, c_x0 + 20, c_y0 + 16], fill=GREEN)
    d.text((c_x0 + 26, c_y0 + 11), "ChatGPT UI (Real-Time)", font=MONOB(9), fill=WHITE, anchor="lm")
    d.text((c_x1 - 10, c_y0 + 11), "LIVE", font=MONOB(8), fill=GREEN, anchor="rm")

    # User Prompt snippet
    d.text((c_x0 + 10, c_y0 + 30), "Prompt: Explain quantum computing...", font=SANS(9), fill=MUTED, anchor="lt")
    d.line([(c_x0 + 10, c_y0 + 44), (c_x1 - 10, c_y0 + 44)], fill=alpha(DIM, 0.4), width=1)

    # Dynamic Typewriter Words for Streaming UI
    # Frame 0 to 300 smoothly reveals words 1 through len(STREAM_WORDS)
    stream_word_count = int((fr / NF) * len(STREAM_WORDS)) + 1
    stream_word_count = min(stream_word_count, len(STREAM_WORDS))
    typed_tokens = STREAM_WORDS[:stream_word_count]

    # Flow words into lines
    lines = []
    curr_line = ""
    for tk in typed_tokens:
        test_line = (curr_line + " " + tk).strip()
        if d.textlength(test_line, font=SANS(10)) > (c_x1 - c_x0 - 24):
            if curr_line: lines.append(curr_line)
            curr_line = tk
        else:
            curr_line = test_line
    if curr_line: lines.append(curr_line)

    for l_idx, line in enumerate(lines[:5]):
        ly = c_y0 + 52 + l_idx * 21
        d.text((c_x0 + 10, ly), line, font=SANS(10), fill=WHITE, anchor="lt")

    # Blinking cursor right after the last word
    if lines:
        last_l = lines[-1]
        last_lw = d.textlength(last_l, font=SANS(10))
        cur_y = c_y0 + 52 + (len(lines) - 1) * 21
        if (fr // 6 % 2 == 0):
            d.rectangle([c_x0 + 12 + last_lw, cur_y + 1, c_x0 + 18 + last_lw, cur_y + 13], fill=GREEN)

    # Top Middle: High-Speed Token Conduit (X: 172 to 390)
    wire_y = (top_y0 + 36 + top_y1 - 12) / 2
    d.line([(172, wire_y - 14), (390, wire_y - 14)], fill=alpha(DIM, 0.6), width=1)
    d.line([(172, wire_y + 14), (390, wire_y + 14)], fill=alpha(DIM, 0.6), width=1)
    d.line([(172, wire_y), (390, wire_y)], fill=alpha(TEAL, 0.3), width=2)

    # Moving token packets in streaming pipe
    num_stream_pkts = 3
    for p in range(num_stream_pkts):
        p_prog = (t * 1.6 + p / num_stream_pkts) % 1.0
        px = 180 + p_prog * (390 - 180 - 64)
        p_token = STREAM_WORDS[(int(t * 3) + p) % len(STREAM_WORDS)]
        d.rounded_rectangle([px, wire_y - 11, px + 60, wire_y + 11], radius=3, fill=(16, 28, 40), outline=GREEN, width=1)
        d.text((px + 30, wire_y), f"\"{p_token[:6]}\"", font=MONOB(8), fill=WHITE, anchor="mm")

    d.text((281, top_y1 - 18), "data: {\"delta\": ...}", font=MONO(8), fill=TEAL, anchor="mm")

    # -------------------------------------------------------------
    # 4. BOTTOM STAGE: DIRECT DISPATCHER (Y: 675 - 935)
    # -------------------------------------------------------------
    bot_y0, bot_y1 = 675, 935
    is_direct_flushed = (fr >= 240) # Flushes at 8.0 seconds (Frame 240)
    direct_outline = GREEN if is_direct_flushed else (RED if fr >= 90 else AMBER)
    
    d.rounded_rectangle([38, bot_y0, W - 38, bot_y1], radius=10, fill=(11, 14, 21), outline=alpha(direct_outline, 0.7), width=1)

    # Header tag for Direct Panel
    d.rectangle([38, bot_y0, W - 38, bot_y0 + 26], fill=(18, 16, 24) if not is_direct_flushed else (15, 24, 28), outline=alpha(DIM, 0.5), width=1)
    d.ellipse([52, bot_y0 + 8, 62, bot_y0 + 18], fill=GREEN if is_direct_flushed else (RED if fr >= 90 else AMBER))
    d.text((70, bot_y0 + 13), "2. DIRECT DISPATCHER (BUFFERED HTTP - 10s WAIT)", font=MONOB(10), fill=WHITE, anchor="lm")
    if not is_direct_flushed:
        d.text((W - 52, bot_y0 + 13), f"BUFFERING: {t:.1f}s", font=MONOB(9), fill=RED if fr >= 90 else AMBER, anchor="rm")
    else:
        d.text((W - 52, bot_y0 + 13), "FLUSHED AT 8.4s!", font=MONOB(9), fill=GREEN, anchor="rm")

    # Bottom Left: LLM Buffering Memory Tank
    b_dx0, b_dy0, b_dx1, b_dy1 = 52, bot_y0 + 36, 172, bot_y1 - 12
    d.rounded_rectangle([b_dx0, b_dy0, b_dx1, b_dy1], radius=6, fill=(15, 18, 27), outline=alpha(AMBER if not is_direct_flushed else GREEN, 0.8), width=1)
    d.text(((b_dx0 + b_dx1) / 2, b_dy0 + 16), "SERVER RAM", font=MONOB(10), fill=WHITE, anchor="mm")
    d.text(((b_dx0 + b_dx1) / 2, b_dy0 + 30), "BUFFER TANK", font=MONO(8), fill=MUTED, anchor="mm")

    # Memory Accumulation Fill Tank (Segmented LED Bars)
    tank_x0, tank_y0, tank_x1, tank_y1 = b_dx0 + 12, b_dy0 + 44, b_dx1 - 12, b_dy1 - 32
    d.rectangle([tank_x0, tank_y0, tank_x1, tank_y1], fill=(8, 10, 15), outline=alpha(DIM, 0.6), width=1)
    
    # Progress of buffer accumulation (0% to 100% up to frame 240)
    buf_pct = min(1.0, fr / 240.0)
    num_bars = 7
    filled_bars = int(buf_pct * num_bars) if not is_direct_flushed else 0
    bar_h = (tank_y1 - tank_y0 - 8) / num_bars

    for b in range(num_bars):
        by0 = tank_y1 - 4 - (b + 1) * bar_h
        by1 = by0 + bar_h - 2
        is_bar_lit = (b < filled_bars)
        b_col = RED if (fr >= 90 and is_bar_lit) else (AMBER if is_bar_lit else (18, 24, 34))
        d.rectangle([tank_x0 + 4, by0, tank_x1 - 4, by1], fill=b_col)

    pct_text = f"{int(buf_pct*100)}%" if not is_direct_flushed else "SENT"
    d.text(((tank_x0 + tank_x1)/2, (tank_y0 + tank_y1)/2), pct_text, font=MONOB(10), fill=WHITE, anchor="mm")

    d.rectangle([b_dx0 + 10, b_dy1 - 28, b_dx1 - 10, b_dy1 - 8], fill=(22, 18, 24) if not is_direct_flushed else (16, 28, 24), outline=alpha(RED if not is_direct_flushed else GREEN, 0.6), width=1)
    d.text(((b_dx0 + b_dx1) / 2, b_dy1 - 18), "HELD IN RAM" if not is_direct_flushed else "FLUSHED!", font=MONOB(8), fill=RED if not is_direct_flushed else GREEN, anchor="mm")

    # Bottom Right: ChatGPT Client UI (Blank/Frozen -> BOOM Text Dump)
    b_cx0, b_cy0, b_cx1, b_cy1 = 390, bot_y0 + 36, W - 52, bot_y1 - 12
    d.rounded_rectangle([b_cx0, b_cy0, b_cx1, b_cy1], radius=6, fill=(12, 16, 24), outline=alpha(GREEN if is_direct_flushed else (RED if fr >= 90 else DIM), 0.8), width=1)

    # Direct client title
    d.rectangle([b_cx0, b_cy0, b_cx1, b_cy0 + 22], fill=(16, 20, 30), outline=alpha(DIM, 0.4), width=1)
    d.ellipse([b_cx0 + 10, b_cy0 + 6, b_cx0 + 20, b_cy0 + 16], fill=GREEN if is_direct_flushed else (RED if fr >= 90 else AMBER))
    d.text((b_cx0 + 26, b_cy0 + 11), "ChatGPT UI (Buffered)", font=MONOB(9), fill=WHITE, anchor="lm")
    d.text((b_cx1 - 10, b_cy0 + 11), "WAITING" if not is_direct_flushed else "100% DONE", font=MONOB(8), fill=RED if not is_direct_flushed else GREEN, anchor="rm")

    # User Prompt snippet
    d.text((b_cx0 + 10, b_cy0 + 30), "Prompt: Explain quantum computing...", font=SANS(9), fill=MUTED, anchor="lt")
    d.line([(b_cx0 + 10, b_cy0 + 44), (b_cx1 - 10, b_cy0 + 44)], fill=alpha(DIM, 0.4), width=1)

    # Direct UI Content:
    if not is_direct_flushed:
        # Client receives NOTHING. Staring at loading spinner and timer!
        sp_cx, sp_cy = (b_cx0 + b_cx1) / 2, b_cy0 + 90
        sp_angle = t * 360 * 2.5
        d.arc([sp_cx - 16, sp_cy - 16, sp_cx + 16, sp_cy + 16], start=sp_angle, end=sp_angle + 250, fill=RED if fr >= 90 else AMBER, width=3)
        d.text((sp_cx, sp_cy + 30), f"Waiting... ({t:.1f}s / 10s)", font=MONOB(9), fill=RED if fr >= 90 else MUTED, anchor="mm")
        d.text((sp_cx, sp_cy + 46), "0 WORDS RECEIVED", font=MONO(8), fill=MUTED, anchor="mm")
    else:
        # BOOM! 100% of text instantly appears all at once!
        # Flash impact effect on frames 240-255
        if fr < 255:
            d.rectangle([b_cx0 + 2, b_cy0 + 2, b_cx1 - 2, b_cy1 - 2], outline=WHITE, width=2)
            d.text(((b_cx0 + b_cx1)/2, b_cy0 + 30), ">>> BOOM! 100% TEXT DUMP <<<", font=MONOB(9), fill=AMBER, anchor="mm")

        # Instant line wrap rendering
        d_lines = []
        d_curr = ""
        for tk in STREAM_WORDS:
            test_line = (d_curr + " " + tk).strip()
            if d.textlength(test_line, font=SANS(10)) > (b_cx1 - b_cx0 - 24):
                if d_curr: d_lines.append(d_curr)
                d_curr = tk
            else:
                d_curr = test_line
        if d_curr: d_lines.append(d_curr)

        for l_idx, line in enumerate(d_lines[:5]):
            ly = b_cy0 + 52 + l_idx * 21
            d.text((b_cx0 + 10, ly), line, font=SANS(10), fill=WHITE, anchor="lt")

    # Bottom Middle: Conduit & Blocking Gate (X: 172 to 390)
    b_wire_y = (bot_y0 + 36 + bot_y1 - 12) / 2
    d.line([(172, b_wire_y - 14), (390, b_wire_y - 14)], fill=alpha(DIM, 0.6), width=1)
    d.line([(172, b_wire_y + 14), (390, b_wire_y + 14)], fill=alpha(DIM, 0.6), width=1)
    
    if not is_direct_flushed:
        # Closed gate in middle blocking all flow
        gate_x = (172 + 390) / 2
        d.rectangle([gate_x - 14, b_wire_y - 24, gate_x + 14, b_wire_y + 24], fill=(26, 18, 22), outline=RED if fr >= 90 else AMBER, width=2)
        d.text((gate_x, b_wire_y - 32), "[GATE LOCKED]", font=MONOB(8), fill=RED if fr >= 90 else AMBER, anchor="mm")
        d.text((gate_x, b_wire_y + 32), "HOLDING IN MEMORY", font=MONO(7), fill=MUTED, anchor="mm")
    else:
        # Gate blown open, massive data explosion block shoots across
        d.line([(172, b_wire_y), (390, b_wire_y)], fill=alpha(GREEN, 0.6), width=3)
        # Giant payload block
        d.rounded_rectangle([220, b_wire_y - 14, 340, b_wire_y + 14], radius=4, fill=(20, 35, 45), outline=GREEN, width=2)
        d.text((280, b_wire_y), "[FULL 10KB DUMP]", font=MONOB(8), fill=WHITE, anchor="mm")

    # -------------------------------------------------------------
    # 5. Lower Caption Progression Pill (Y: 980 - 1030)
    # -------------------------------------------------------------
    draw_caption_pill(d, fr, CAPTIONS, 1.0)

    return finish(img, fr)

def render_and_save_frame(args):
    fr, out_dir = args
    img = render(fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))

if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_streaming_vs_direct"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered Streaming vs Direct frames: {len(frames)}")
