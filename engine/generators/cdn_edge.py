#!/usr/bin/env python3
"""
Flagship System Design Reel: CDN Edge (Central Origin 320ms vs Global Edge PoPs 8ms)
Visual Apparatus: Global client nodes (Tokyo, London, Sydney) routing heavy static media.
Beat 1: Trans-oceanic undersea cables suffer 320ms round-trip latency to a single US-East Origin.
Beat 2: Global traffic spike causes 98% CPU redline, packet loss, and 350ms severe lag.
Beat 3: Edge PoPs deploy worldwide with Anycast routing; 98.4% cache hit delivers 8ms local responses.
720x1280 @ 30fps, 10s (300 frames).
"""
import os, sys, math
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from blueprint_engine import (
    W, H, FPS, DUR, NF, BG, AMBER, AMBER_D, TEAL, TEAL_D, BLUE, BLUE_D,
    WHITE, MUTED, DIM, RED, RED_D, GREEN, GREEN_D,
    MONO, MONOB, SANS, SANSB,
    ease, alpha, lerp, track, finish, draw_caption_pill, draw_telemetry_hud,
)

CAPTIONS = [
    (0,   "players worldwide fetch heavy 4K textures & video assets."),
    (60,  "without a CDN, every packet travels 12,000km to one US-East origin."),
    (124, "320ms trans-oceanic latency. Origin CPU redlines at 98%."),
    (188, "CDN deploys global Edge PoPs with Anycast geo-routing."),
    (250, "98.4% cache hit ratio. 8ms local responses right at the edge."),
]

# Client nodes configuration (Tokyo, London, Sydney)
CLIENTS = [
    {"name": "TOKYO", "code": "TYO", "y": 530, "region": "APAC"},
    {"name": "LONDON", "code": "LHR", "y": 665, "region": "EMEA"},
    {"name": "SYDNEY", "code": "SYD", "y": 800, "region": "OCEA"},
]

CLIENT_X0, CLIENT_X1 = 52, 168
EDGE_X0, EDGE_X1 = 236, 368
ORIGIN_X0, ORIGIN_X1 = 492, 668
ORIGIN_Y0, ORIGIN_Y1 = 492, 838


def draw_query_pill(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    col = GREEN if beat3 else (RED if beat2 else BLUE)
    ca = a * (pulse if beat2 else 1.0)
    
    d.rounded_rectangle([52, 415, 668, 465], radius=10, fill=(12, 16, 24),
                        outline=alpha(col, ca * 0.9), width=2)
    d.ellipse([68, 433, 82, 447], fill=alpha(col, ca))
    
    if beat3:
        track(d, (96, 429), 'GET https://cdn.game.io/assets/hero.mp4',
              MONOB(12), alpha(WHITE, a), sp=0, anchor="lm")
        d.text((96, 450), "Anycast DNS -> Nearest Edge PoP Cache · 8ms TTFB",
               font=SANS(10), fill=alpha(GREEN, a), anchor="lm")
    else:
        track(d, (96, 429), 'GET https://origin.us-east.io/hero.mp4',
              MONOB(12), alpha(WHITE, a), sp=0, anchor="lm")
        sub = "180k req/s bottleneck · single origin server" if beat2 else "12,000km undersea cable · 320ms round-trip latency"
        d.text((96, 450), sub, font=SANS(10), fill=alpha(RED if beat2 else MUTED, a), anchor="lm")


def draw_clients(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    
    for c in CLIENTS:
        cy = c["y"]
        x0, x1 = CLIENT_X0, CLIENT_X1
        y0, y1 = cy - 44, cy + 44
        
        # Client card box
        box_col = GREEN if beat3 else (RED if beat2 else BLUE)
        d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=(11, 14, 20),
                            outline=alpha(box_col, a * (pulse if beat2 else 0.8)), width=2)
        
        # Device header bar
        d.rectangle([x0 + 4, y0 + 4, x1 - 4, y0 + 20], fill=(16, 20, 30))
        d.text((x0 + 8, y0 + 12), c["code"], font=MONOB(9), fill=alpha(WHITE, a), anchor="lm")
        d.text((x1 - 8, y0 + 12), c["region"], font=MONO(8), fill=alpha(MUTED, a), anchor="rm")
        
        # Client City Name
        d.text(((x0 + x1)/2, y0 + 38), c["name"], font=SANSB(12), fill=alpha(WHITE, a), anchor="mm")
        
        # Ping latency pill
        ping_val = "8ms" if beat3 else ("350ms" if beat2 else "320ms")
        ping_col = GREEN if beat3 else (RED if beat2 else AMBER)
        d.rounded_rectangle([x0 + 8, y0 + 56, x1 - 8, y0 + 76], radius=4, fill=(8, 10, 16),
                            outline=alpha(ping_col, a * 0.7), width=1)
        d.text(((x0 + x1)/2, y0 + 66), f"RTT {ping_val}", font=MONOB(9),
               fill=alpha(ping_col, a * (pulse if beat2 else 1.0)), anchor="mm")


def draw_origin_server(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    
    x0, y0, x1, y1 = ORIGIN_X0, ORIGIN_Y0, ORIGIN_X1, ORIGIN_Y1
    
    rack_col = GREEN if beat3 else (RED if beat2 else WHITE)
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=(11, 14, 20),
                        outline=alpha(rack_col, a * (pulse if beat2 else 0.9)), width=2)
    
    # Header tag
    d.rounded_rectangle([x0 + 6, y0 + 6, x1 - 6, y0 + 32], radius=6, fill=(16, 22, 34))
    d.text(((x0 + x1)/2, y0 + 19), "ORIGIN SERVER", font=MONOB(11), fill=alpha(WHITE, a), anchor="mm")
    
    # Sub-badge (US-EAST 1 / VIRGINIA)
    d.text(((x0 + x1)/2, y0 + 44), "AWS us-east-1 · Virginia", font=MONO(9), fill=alpha(MUTED, a), anchor="mm")
    
    # CPU Load Meter Bar
    cpu_pct = 2 if beat3 else (int(lerp(35, 98, ease((fr - 90)/60))) if beat2 else 35)
    meter_col = GREEN if beat3 else (RED if beat2 else BLUE)
    
    my0 = y0 + 58
    d.rectangle([x0 + 12, my0, x1 - 12, my0 + 20], fill=(8, 10, 14), outline=alpha(DIM, a * 0.8), width=1)
    bar_w = int((x1 - x0 - 28) * (cpu_pct / 100.0))
    if bar_w > 0:
        d.rectangle([x0 + 14, my0 + 2, x0 + 14 + bar_w, my0 + 18], fill=alpha(meter_col, a * (pulse if beat2 else 0.85)))
    d.text(((x0 + x1)/2, my0 + 10), f"CPU LOAD {cpu_pct}%", font=MONOB(9), fill=alpha(WHITE, a), anchor="mm")
    
    # 4 Server Blades / Rack units
    blade_y0 = y0 + 88
    for b in range(4):
        by = blade_y0 + b * 42
        d.rounded_rectangle([x0 + 10, by, x1 - 10, by + 34], radius=4, fill=(14, 18, 26),
                            outline=alpha(DIM, a * 0.7), width=1)
        
        # Blade LED status
        led_col = GREEN if beat3 else (RED if beat2 else TEAL)
        blink = 0.4 + 0.6 * math.sin(fr * (0.8 if beat2 else 0.25) + b * 1.7)
        d.ellipse([x0 + 18, by + 12, x0 + 28, by + 22], fill=alpha(led_col, a * blink))
        
        # Disk text
        d.text((x0 + 36, by + 17), f"BLADE-0{b+1} · ORIGIN DISK", font=MONO(8), fill=alpha(MUTED, a), anchor="lm")
        
        # Status tick on right
        st_col = GREEN if beat3 else (RED if beat2 else TEAL)
        d.rectangle([x1 - 22, by + 11, x1 - 16, by + 23], fill=alpha(st_col, a * 0.7))
    
    # Bottom Status summary
    bot_y = y1 - 24
    if beat3:
        d.text(((x0 + x1)/2, bot_y), "✓ OFFLOADED (98% SAVINGS)", font=MONOB(9), fill=alpha(GREEN, a), anchor="mm")
    elif beat2:
        d.text(((x0 + x1)/2, bot_y), "⚠ 98% SATURATION OVERLOAD", font=MONOB(9), fill=alpha(RED, a * pulse), anchor="mm")
    else:
        d.text(((x0 + x1)/2, bot_y), "SERVING ALL GLOBAL TRAFFIC", font=MONO(9), fill=alpha(AMBER, a), anchor="mm")


def draw_edge_pops(d, fr, a):
    beat3 = fr >= 180
    edge_alpha = ease((fr - 180) / 20) if beat3 else 0.0
    
    if edge_alpha <= 0.01:
        return

    ea = a * edge_alpha
    for c in CLIENTS:
        cy = c["y"]
        x0, x1 = EDGE_X0, EDGE_X1
        y0, y1 = cy - 44, cy + 44
        
        # Edge PoP active container
        d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=(12, 22, 26),
                            outline=alpha(TEAL, ea), width=2)
        
        # Header bar
        d.rectangle([x0 + 4, y0 + 4, x1 - 4, y0 + 20], fill=(16, 32, 38))
        d.text((x0 + 8, y0 + 12), f"EDGE POP", font=MONOB(9), fill=alpha(WHITE, ea), anchor="lm")
        d.text((x1 - 8, y0 + 12), c["code"], font=MONOB(9), fill=alpha(TEAL, ea), anchor="rm")
        
        # SSD Fast Cache Label
        d.text(((x0 + x1)/2, y0 + 38), "NVMe SSD CACHE", font=MONOB(10), fill=alpha(WHITE, ea), anchor="mm")
        
        # Cache Hit Status Pill
        d.rounded_rectangle([x0 + 8, y0 + 56, x1 - 8, y0 + 76], radius=4, fill=(10, 26, 22),
                            outline=alpha(GREEN, ea * 0.9), width=1)
        d.text(((x0 + x1)/2, y0 + 66), "✓ 98.4% CACHE HIT", font=MONOB(9), fill=alpha(GREEN, ea), anchor="mm")


def draw_network_cables_and_packets(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    
    # 1. Draw Undersea Cables to Origin
    cable_col = RED if beat2 else (DIM if beat3 else AMBER)
    cable_a = a * (0.22 if beat3 else (1.0 if beat2 else 0.7))
    
    for c in CLIENTS:
        cy = c["y"]
        # Cable from Client to Origin
        d.line([(CLIENT_X1, cy), (ORIGIN_X0, cy)], fill=alpha(cable_col, cable_a), width=2)
        
        # Tick markers along undersea cable
        for mx in range(CLIENT_X1 + 25, ORIGIN_X0 - 15, 30):
            d.line([(mx, cy - 3), (mx, cy + 3)], fill=alpha(cable_col, cable_a * 0.5), width=1)

    # 2. Draw Packet Flow
    if beat3:
        # BEAT 3: Local Edge Traffic (Ultra fast loop 8ms between Client and Edge PoP)
        for i, c in enumerate(CLIENTS):
            cy = c["y"]
            # Short local link
            d.line([(CLIENT_X1, cy), (EDGE_X0, cy)], fill=alpha(GREEN, a * 0.9), width=3)
            
            # Fast green packets (Client <-> Edge)
            num_local_pkts = 3
            for p in range(num_local_pkts):
                prog = ((fr * 0.12) + p / num_local_pkts + i * 0.33) % 1.0
                px = lerp(CLIENT_X1, EDGE_X0, prog)
                # glowing green orb
                d.ellipse([px - 4, cy - 4, px + 4, cy + 4], fill=alpha(GREEN, a))
                d.ellipse([px - 7, cy - 7, px + 7, cy + 7], outline=alpha(GREEN, a * 0.4), width=1)
            
            # Single slow sync line from Edge to Origin (Cache refresh heartbeat)
            sync_prog = ((fr * 0.02) + i * 0.33) % 1.0
            sx = lerp(EDGE_X1, ORIGIN_X0, sync_prog)
            d.ellipse([sx - 3, cy - 3, sx + 3, cy + 3], fill=alpha(BLUE, a * 0.6))
            
    elif beat2:
        # BEAT 2: Heavy storm of red packets jamming the single origin
        for i, c in enumerate(CLIENTS):
            cy = c["y"]
            num_storm_pkts = 5
            for p in range(num_storm_pkts):
                prog = ((fr * 0.04) + p / num_storm_pkts + i * 0.25) % 1.0
                px = lerp(CLIENT_X1, ORIGIN_X0, prog)
                d.ellipse([px - 5, cy - 5, px + 5, cy + 5], fill=alpha(RED, a * pulse))
                d.ellipse([px - 8, cy - 8, px + 8, cy + 8], outline=alpha(RED, a * 0.5), width=1)
                
            # Dropped packet X mark near origin
            if (fr + i * 15) % 30 < 15:
                dx = ORIGIN_X0 - 32
                d.text((dx, cy - 14), "✗ DROP", font=MONOB(8), fill=alpha(RED, a * pulse), anchor="mm")
                
    else:
        # BEAT 1: Normal steady traffic packets traveling long distance
        for i, c in enumerate(CLIENTS):
            cy = c["y"]
            num_pkts = 3
            for p in range(num_pkts):
                prog = ((fr * 0.025) + p / num_pkts + i * 0.33) % 1.0
                px = lerp(CLIENT_X1, ORIGIN_X0, prog)
                d.ellipse([px - 4, cy - 4, px + 4, cy + 4], fill=alpha(AMBER, a))
                d.ellipse([px - 7, cy - 7, px + 7, cy + 7], outline=alpha(AMBER, a * 0.35), width=1)


def draw_takeaway_bar(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    
    y = 920
    d.line([(52, y - 24), (668, y - 24)], fill=alpha(DIM, a * 0.5), width=1)
    
    if beat3:
        track(d, (W/2, y), "✓ ANYCAST GEO-ROUTING  ·  NVMe EDGE CACHING  ·  98% OFFLOAD",
              MONOB(10), alpha(GREEN, a), sp=1, anchor="mm")
    elif beat2:
        track(d, (W/2, y), "⚠ SINGLE ORIGIN BOTTLENECK  ·  CROSS-OCEAN PACKET LOSS",
              MONOB(10), alpha(RED, a * pulse), sp=1, anchor="mm")
    else:
        track(d, (W/2, y), "CENTRALIZED ORIGIN ARCHITECTURE  ·  12,000km PHYSICAL DISTANCE",
              MONOB(10), alpha(MUTED, a), sp=1, anchor="mm")


def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag

    # ---- 1. Header (Y: 148 – 290)
    # Red Handle Pill with live pulsing LED
    pill_w = d.textlength("@buildebugship", font=MONOB(12)) + 36
    px0, py0 = W / 2 - pill_w / 2, 148
    px1, py1 = W / 2 + pill_w / 2, 172
    d.rounded_rectangle([px0, py0, px1, py1], radius=12, fill=(18, 14, 20), outline=alpha(RED, 0.8 * intro), width=1)
    d.ellipse([px0 + 10, py0 + 8, px0 + 16, py0 + 14], fill=RED)
    d.text((px0 + 24, py0 + 11), "@buildebugship", font=MONOB(12), fill=alpha(WHITE, intro), anchor="lm")

    # Comparison Tag Pill
    track(d, (W / 2, 192), "CENTRAL ORIGIN (320ms)   vs   GLOBAL EDGE CDN (8ms)",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")

    # Large Bold Headline
    tw1 = d.textlength("CDN ", font=SANSB(42))
    tw2 = d.textlength("EDGE", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 228), "CDN ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 228), "EDGE", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")

    # Subhook Context
    d.text((W / 2, 268), "how Content Delivery Networks eliminate global network lag",
           font=SANS(13), fill=alpha(BLUE, intro * 0.95), anchor="mm")

    # Lower Divider Ruler
    d.line([(48, 290), (W - 48, 290)], fill=alpha(DIM, 0.6), width=1)

    if diag <= 0.01:
        return base

    # ---- 2. Telemetry HUD (Y: 304 – 376)
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    
    if beat3:
        lat_val = "8.0 ms"
        lat_col = GREEN
        load_val = "3.2k req/s"
        load_col = GREEN
    elif beat2:
        lat_ms = int(lerp(320, 350, ease((fr - 90)/60)))
        lat_val = f"{lat_ms} ms"
        lat_col = RED
        load_val = "180k req/s"
        load_col = RED
    else:
        lat_val = "320 ms"
        lat_col = AMBER
        load_val = "15k req/s"
        load_col = BLUE

    draw_telemetry_hud(d, "ROUND TRIP PING", lat_val, "ORIGIN LOAD", load_val, a,
                       m1_col=lat_col, m2_col=load_col)

    # ---- 3. Stage Apparatus (Y: 415 – 945)
    draw_query_pill(d, fr, a)
    draw_network_cables_and_packets(d, fr, a)
    draw_clients(d, fr, a)
    draw_edge_pops(d, fr, a)
    draw_origin_server(d, fr, a)
    draw_takeaway_bar(d, fr, a)

    # ---- 4. Caption Pill (Y: 980 – 1028)
    draw_caption_pill(d, fr, CAPTIONS, a)

    # ---- 5. Outro Footer (frames 258+)
    if fr >= 258:
        out_a = ease((fr - 258) / 18)
        track(d, (W / 2, 1090), "EDGE POP CACHE · ANYCAST DNS · STATIC ASSET OFFLOAD",
              MONOB(11), alpha(TEAL, out_a), sp=2, anchor="mm")
        track(d, (W / 2, 1112), "CLOUDFLARE · CLOUDFRONT · FASTLY · AKAMAI · NGINX",
              MONO(10), alpha(MUTED, out_a * 0.85), sp=2, anchor="mm")

    return base


def render_and_save_frame(args):
    fr, out_dir = args
    finish(render(fr), fr).save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_cdn_edge"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, [(fr, out_dir) for fr in frames]))
