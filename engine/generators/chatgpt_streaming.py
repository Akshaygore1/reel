#!/usr/bin/env python3
"""
How ChatGPT Streams Responses — Server-Sent Events (SSE) & Token Generation.
Visual Apparatus: GPU Transformer Attention Engine -> Chunked SSE Data Wire -> ChatGPT Chat Bubble UI with Typing Cursor.
Narrative:
- Beat 1 (0-3s): User sends prompt; Transformer GPU calculates next-token probabilities autoregressively.
- Beat 2 (3-6s): Why buffering fails: Waiting for 500 tokens causes a 14.8s frozen screen -> Alert Buzzer.
- Beat 3 (6-10s): SSE text/event-stream flushes each token delta immediately: 38ms TTFB, 45 tok/s -> Victory Chime.
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

CAPTIONS = [
    (0, "ChatGPT generates answers autoregressively: one token at a time"),
    (90, "Without streaming, waiting for 500 tokens freezes the UI for 14.8s"),
    (180, "SSE flushes each token delta over HTTP chunked transfer in 38ms")
]

STREAM_TOKENS = ["Quantum", "computers", "use", "qubits", "to", "process", "states", "in", "parallel."]

def render(fr):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    t = fr / FPS

    # 1. Header Bar
    draw_header_bar(d, 1.0, handle="@buildebugship", comp_left="GPU TRANSFORMER", comp_right="SERVER-SENT EVENTS",
                    title1="HOW CHATGPT", title_vs="STREAMS", title2="RESPONSES", subhook="how text/event-stream delivers tokens in real time")

    # 2. Telemetry HUD
    if fr < 90:
        draw_telemetry_hud(d, "TOKEN GENERATION", "AUTOREGRESSIVE", "PROTOCOL", "text/event-stream", 1.0, TEAL, BLUE)
    elif fr < 180:
        flicker = 1.0 if (fr // 4 % 2 == 0) else 0.4
        draw_telemetry_hud(d, "BUFFERED DELAY", "14.8s FREEZE", "CLIENT PERCEPTION", "FROZEN SPINNER", flicker, RED, RED)
    else:
        draw_telemetry_hud(d, "TIME TO FIRST BYTE", "38 ms (INSTANT)", "STREAM RATE", "45 TOKENS / SEC", 1.0, GREEN, TEAL)

    # 3. Visual Stage (GPU Transformer -> SSE Wire -> ChatGPT UI)
    
    # ---- Left Stage: GPU Transformer Core (Y: 400 - 640)
    gpu_x0, gpu_y0, gpu_x1, gpu_y1 = 48, 400, 310, 650
    d.rounded_rectangle([gpu_x0, gpu_y0, gpu_x1, gpu_y1], radius=10, fill=(10, 14, 22), outline=alpha(TEAL, 0.8), width=1)
    
    # GPU Header Badge
    d.rectangle([gpu_x0 + 8, gpu_y0 + 8, gpu_x1 - 8, gpu_y0 + 34], fill=(14, 20, 32), outline=alpha(DIM, 0.5), width=1)
    d.text(((gpu_x0 + gpu_x1) / 2, gpu_y0 + 21), "NVIDIA H100 · KV CACHE", font=MONOB(10), fill=TEAL, anchor="mm")

    # Transformer Attention Matrix Grid
    rows, cols = 4, 5
    cell_w, cell_h = 42, 28
    grid_sx, grid_sy = gpu_x0 + 22, gpu_y0 + 48
    active_cell = (int(t * 8) % rows, int(t * 12) % cols)

    for r in range(rows):
        for c in range(cols):
            cx0 = grid_sx + c * (cell_w + 6)
            cy0 = grid_sy + r * (cell_h + 6)
            is_active = (r == active_cell[0] and c == active_cell[1])
            cell_col = GREEN if (fr >= 180 and is_active) else (AMBER if is_active else (16, 22, 34))
            d.rounded_rectangle([cx0, cy0, cx0 + cell_w, cy0 + cell_h], radius=3, fill=cell_col, outline=alpha(TEAL, 0.4), width=1)
            if is_active:
                d.text((cx0 + cell_w/2, cy0 + cell_h/2), "P(w)", font=MONO(9), fill=(10, 14, 22) if fr >= 180 else WHITE, anchor="mm")

    # Next Token Prediction Bar
    d.rectangle([gpu_x0 + 16, gpu_y1 - 42, gpu_x1 - 16, gpu_y1 - 14], fill=(14, 20, 30), outline=alpha(GREEN if fr >= 180 else AMBER, 0.7), width=1)
    tok_idx = int(t * 3) % len(STREAM_TOKENS)
    curr_tok = STREAM_TOKENS[tok_idx]
    d.text(((gpu_x0 + gpu_x1) / 2, gpu_y1 - 28), f"NEXT TOKEN: \"{curr_tok}\"", font=MONOB(10), fill=GREEN if fr >= 180 else AMBER, anchor="mm")

    # ---- Right Stage: ChatGPT Interface Bubble (Y: 400 - 650)
    chat_x0, chat_y0, chat_x1, chat_y1 = 350, 400, W - 48, 650
    d.rounded_rectangle([chat_x0, chat_y0, chat_x1, chat_y1], radius=10, fill=(12, 16, 24), outline=alpha(GREEN if fr >= 180 else (RED if fr >= 90 else DIM), 0.8), width=1)
    
    # ChatGPT UI Header
    d.rectangle([chat_x0 + 8, chat_y0 + 8, chat_x1 - 8, chat_y0 + 34], fill=(16, 22, 32), outline=alpha(DIM, 0.5), width=1)
    # ChatGPT logo green dot
    d.ellipse([chat_x0 + 18, chat_y0 + 16, chat_x0 + 26, chat_y0 + 24], fill=GREEN)
    d.text((chat_x0 + 36, chat_y0 + 21), "CHATGPT CLIENT (UI)", font=MONOB(10), fill=WHITE, anchor="lm")

    # Chat Response Content Box
    if fr < 90:
        # Prompt sent, waiting for first token
        d.text((chat_x0 + 18, chat_y0 + 55), "Prompt: Explain Quantum...", font=SANS(11), fill=MUTED, anchor="lt")
        d.text((chat_x0 + 18, chat_y0 + 95), "Connecting SSE stream...", font=MONO(10), fill=TEAL, anchor="lt")
    elif fr < 180:
        # Freeze / No streaming
        d.text((chat_x0 + 18, chat_y0 + 55), "Prompt: Explain Quantum...", font=SANS(11), fill=MUTED, anchor="lt")
        # Loading spinner
        sp_angle = t * 360 * 3
        scx, scy = (chat_x0 + chat_x1) / 2, chat_y0 + 120
        d.arc([scx - 18, scy - 18, scx + 18, scy + 18], start=sp_angle, end=sp_angle + 240, fill=RED, width=3)
        d.text((scx, scy + 36), "14.8s BUFFERING WAIT", font=MONOB(10), fill=RED, anchor="mm")
    else:
        # Active Streaming with Typewriter Effect
        d.text((chat_x0 + 18, chat_y0 + 50), "ChatGPT:", font=MONOB(11), fill=GREEN, anchor="lt")
        words_shown = int((fr - 180) / 12) + 1
        words_shown = min(words_shown, len(STREAM_TOKENS))
        typed_str = " ".join(STREAM_TOKENS[:words_shown])
        
        # Word wrap rendering
        lines = []
        words = typed_str.split(" ")
        cur_line = ""
        for w in words:
            if len(cur_line + " " + w) > 18:
                lines.append(cur_line)
                cur_line = w
            else:
                cur_line = (cur_line + " " + w).strip()
        if cur_line: lines.append(cur_line)
        
        for l_idx, line in enumerate(lines[:4]):
            d.text((chat_x0 + 18, chat_y0 + 78 + l_idx * 24), line, font=SANSB(12), fill=WHITE, anchor="lt")
        
        # Blinking Cursor
        cursor_visible = (fr // 8 % 2 == 0)
        if cursor_visible and lines:
            last_line = lines[-1]
            last_w = d.textlength(last_line, font=SANSB(12))
            cur_y = chat_y0 + 78 + (len(lines) - 1) * 24
            d.rectangle([chat_x0 + 20 + last_w, cur_y + 2, chat_x0 + 28 + last_w, cur_y + 18], fill=GREEN)

    # ---- Bottom Stage: HTTP SSE Chunked Wire Protocol (Y: 690 - 930)
    wire_y0, wire_y1 = 690, 930
    d.rounded_rectangle([48, wire_y0, W - 48, wire_y1], radius=10, fill=(11, 15, 22), outline=alpha(GREEN if fr >= 180 else DIM, 0.8), width=1)
    
    # Wire Header
    d.text((68, wire_y0 + 20), "HTTP/2 PROTOCOL · Transfer-Encoding: chunked", font=MONOB(10), fill=BLUE if fr < 180 else GREEN, anchor="lm")
    d.line([(48, wire_y0 + 36), (W - 48, wire_y0 + 36)], fill=alpha(DIM, 0.5), width=1)

    # Laser Pipe Transmission Channel
    pipe_y = wire_y0 + 110
    d.line([(80, pipe_y), (W - 80, pipe_y)], fill=alpha(GREEN if fr >= 180 else DIM, 0.8), width=4)
    d.line([(80, pipe_y - 18), (W - 80, pipe_y - 18)], fill=alpha(DIM, 0.4), width=1)
    d.line([(80, pipe_y + 18), (W - 80, pipe_y + 18)], fill=alpha(DIM, 0.4), width=1)

    # Flying SSE Event Packets
    if fr >= 180 or fr < 90:
        num_packets = 4
        for p in range(num_packets):
            prog = (t * 1.5 + p / num_packets) % 1.0
            px = 120 + prog * (W - 240)
            p_tok = STREAM_TOKENS[(tok_idx + p) % len(STREAM_TOKENS)]
            # Packet box
            d.rounded_rectangle([px - 45, pipe_y - 14, px + 45, pipe_y + 14], radius=4, fill=(16, 26, 36), outline=GREEN if fr >= 180 else TEAL, width=1)
            d.text((px, pipe_y), f"data: \"{p_tok}\"", font=MONO(9), fill=WHITE, anchor="mm")

    # Bottom Protocol Specs
    d.text((68, wire_y1 - 24), "1. POST /v1/chat/completions (stream=true)", font=MONO(9), fill=MUTED, anchor="lm")
    d.text((W / 2 + 30, wire_y1 - 24), "2. data: {\"delta\": ...} -> data: [DONE]", font=MONOB(9), fill=GREEN if fr >= 180 else MUTED, anchor="lm")

    # 4. Lower Caption Progression
    draw_caption_pill(d, fr, CAPTIONS, 1.0)

    return finish(img, fr)

def render_and_save_frame(args):
    fr, out_dir = args
    img = render(fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))

if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_chatgpt_streaming"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered ChatGPT Streaming frames: {len(frames)}")
