#!/usr/bin/env python3
"""
VPN Explained — Clear-Text Routing vs Encrypted Transit Tunnel.
Visual Apparatus: Airport Runway & Armored VPN Transit Tube.
Narrative:
- Beat 1 (0-3s): Direct HTTPS request reveals destination IP to local Wi-Fi & ISP.
- Beat 2 (3-6s): ISP/Router surveillance logs destinations (github.com, paypal.com) -> Alert Buzzer.
- Beat 3 (6-10s): VPN encapsulates packet in outer tunnel envelope -> Wi-Fi sees only VPN Server IP -> Victory Chime.
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
from apparatus.airport import draw_runway, draw_airplane, draw_radar_scope
from apparatus.network import draw_vpn_tunnel

CAPTIONS = [
    (0, "HTTPS encrypts content, but your WiFi still sees destination IPs"),
    (90, "WiFi router & ISP log every domain you visit in plain clear-text"),
    (180, "VPN wraps entire request in outer tunnel envelope: WiFi sees only VPN IP")
]

def render(fr):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    t = fr / FPS

    # 1. Header Bar
    draw_header_bar(d, 1.0, handle="@buildebugship", comp_left="CLEAR-TEXT WIFI", comp_right="VPN ENCAPSULATION",
                    title1="VPN", title_vs="vs", title2="ISP SNOOP", subhook="what your wifi can actually see vs hide")

    # 2. Telemetry HUD
    if fr < 90:
        draw_telemetry_hud(d, "DESTINATION IP", "EXPOSED (CLEAR)", "ISP VISIBILITY", "100% LOGGED", 1.0, AMBER, AMBER)
    elif fr < 180:
        # Alert Phase
        flicker = 1.0 if (fr // 4 % 2 == 0) else 0.4
        draw_telemetry_hud(d, "PACKET SNOOP", "PAYPAL.COM", "SURVEILLANCE", "CRISIS DETECTED", flicker, RED, RED)
    else:
        # Secure Phase
        draw_telemetry_hud(d, "DESTINATION IP", "MASKED (VPN)", "ENCRYPTION", "AES-256-GCM", 1.0, GREEN, TEAL)

    # 3. Visual Stage (Airport Runway / Laser Transit Tunnel)
    runway_cx = W / 2
    draw_runway(d, runway_cx, 400, 920, width=140, lights_phase=t * 1.5)

    # Radar Scope in upper corner
    draw_radar_scope(d, 140, 480, radius=55, sweep_deg=(t * 180) % 360, col=RED if (90 <= fr < 180) else TEAL)

    # Middle Tunnel / Inspection Gate
    is_vpn_active = (fr >= 180)
    draw_vpn_tunnel(d, runway_cx - 160, 660, runway_cx + 160, height=70, encrypted=is_vpn_active)

    # Moving Jet Airplane / Data Packet
    plane_y = 420 + ((t * 120) % 480)
    if fr < 90:
        # Clear-text destination visible
        draw_airplane(d, runway_cx, plane_y, heading_deg=180, scale=1.1, col=AMBER, label="DEST: PAYPAL.COM")
    elif fr < 180:
        # Unencrypted packet exposed to sniffer
        draw_airplane(d, runway_cx, plane_y, heading_deg=180, scale=1.1, col=RED, label="⚠️ VISIBLE TO WIFI")
        # Sniffer crosshair
        d.line([(runway_cx - 40, plane_y), (runway_cx + 40, plane_y)], fill=RED, width=1)
        d.line([(runway_cx, plane_y - 40), (runway_cx, plane_y + 40)], fill=RED, width=1)
    else:
        # Encapsulated in VPN envelope
        draw_airplane(d, runway_cx, plane_y, heading_deg=180, scale=1.1, col=GREEN, label="DEST: 185.220.101.5 (VPN)")
        # Outer shield ring
        d.ellipse([runway_cx - 36, plane_y - 36, runway_cx + 36, plane_y + 36], outline=alpha(GREEN, 0.7), width=2)

    # 4. Lower Caption Progression
    draw_caption_pill(d, fr, CAPTIONS, 1.0)

    return finish(img, fr)

def render_and_save_frame(args):
    fr, out_dir = args
    img = render(fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))

if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_vpn_tunnel"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered VPN Tunnel frames: {len(frames)}")
