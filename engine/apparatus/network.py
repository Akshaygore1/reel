#!/usr/bin/env python3
"""
Network, Transit & Hashing Modular Apparatus Primitive.
Simulates 360-degree hash rings, encrypted laser transit tunnels (VPN wrapping),
and overhead motorized cranes for autoscaling server pods.
"""
import math
from engine.blueprint_engine import alpha, BG, WHITE, MUTED, DIM, TEAL, AMBER, RED, GREEN, BLUE, MONO, MONOB, SANS, SANSB

def draw_hash_ring(d, cx, cy, radius=90, nodes=4, active_key_angle=None, col=BLUE):
    """Draws a 360-degree circular consistent hashing ring with server nodes and partitions"""
    # Outer ring
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=(8, 12, 18), outline=alpha(col, 0.8), width=2)
    d.ellipse([cx - radius + 8, cy - radius + 8, cx + radius - 8, cy + radius - 8],
              outline=alpha(DIM, 0.4), width=1)

    # 360 degree tick marks
    for deg in range(0, 360, 30):
        rad = math.radians(deg)
        x0 = cx + (radius - 6) * math.cos(rad)
        y0 = cy + (radius - 6) * math.sin(rad)
        x1 = cx + radius * math.cos(rad)
        y1 = cy + radius * math.sin(rad)
        d.line([(x0, y0), (x1, y1)], fill=MUTED, width=1)

    # Server node buckets on ring
    for i in range(nodes):
        deg = (i * 360.0 / nodes) + 45
        rad = math.radians(deg)
        nx = cx + radius * math.cos(rad)
        ny = cy + radius * math.sin(rad)
        # Node badge
        d.ellipse([nx - 12, ny - 12, nx + 12, ny + 12], fill=(18, 24, 36), outline=TEAL, width=2)
        d.text((nx, ny), f"S{i+1}", font=MONOB(10), fill=WHITE, anchor="mm")

    # Moving request hash key
    if active_key_angle is not None:
        k_rad = math.radians(active_key_angle)
        kx = cx + radius * math.cos(k_rad)
        ky = cy + radius * math.sin(k_rad)
        d.ellipse([kx - 8, ky - 8, kx + 8, ky + 8], fill=AMBER)
        # Arrow pointing clockwise to next node
        d.line([(cx, cy), (kx, ky)], fill=alpha(AMBER, 0.5), width=1)

def draw_vpn_tunnel(d, x_start, y, x_end, height=60, encrypted=True, col=GREEN):
    """
    Draws an encrypted laser transit tunnel with outer wrapper casing.
    Hides destination IP metadata inside outer VPN envelope.
    """
    tunnel_w = x_end - x_start
    y0, y1 = y - height / 2, y + height / 2

    # Outer armored tunnel sheath
    d.rounded_rectangle([x_start, y0, x_end, y1], radius=8, fill=(8, 14, 16),
                        outline=alpha(col if encrypted else RED, 0.9), width=2)

    # Laser conduit rings along the tunnel
    num_rings = 8
    step = tunnel_w / (num_rings + 1)
    for i in range(1, num_rings + 1):
        rx = x_start + i * step
        d.ellipse([rx - 6, y0 + 4, rx + 6, y1 - 4], outline=alpha(col if encrypted else RED, 0.35), width=1)

    # Padlock security indicator on top
    lock_x = (x_start + x_end) / 2
    if encrypted:
        d.text((lock_x, y0 - 14), "🔒 ENCRYPTED VPN TUNNEL (AES-256-GCM)", font=MONOB(10), fill=GREEN, anchor="mm")
    else:
        d.text((lock_x, y0 - 14), "⚠️ UNENCRYPTED CLEAR-TEXT (DESTINATION VISIBLE)", font=MONOB(10), fill=RED, anchor="mm")

def draw_overhead_crane(d, cx, cy, span=460, trolley_x=0.0, hook_y_offset=0.0, pod_payload=None, col=AMBER):
    """
    Draws an industrial overhead gantry crane that rolls and drops server pods into pool.
    """
    x0, x1 = cx - span / 2, cx + span / 2
    beam_y = cy

    # Overhead gantry bridge girder
    d.line([(x0, beam_y), (x1, beam_y)], fill=WHITE, width=4)
    d.line([(x0, beam_y - 12), (x1, beam_y - 12)], fill=alpha(col, 0.7), width=2)
    # Girder cross-trusses
    for tx in range(int(x0), int(x1), 24):
        d.line([(tx, beam_y), (tx + 12, beam_y - 12)], fill=alpha(col, 0.4), width=1)

    # Moving motorized trolley
    tx = cx + trolley_x
    d.rectangle([tx - 20, beam_y - 16, tx + 20, beam_y + 4], fill=(20, 26, 38), outline=col, width=2)

    # Hoist steel cables
    hook_y = beam_y + 40 + hook_y_offset
    d.line([(tx - 10, beam_y + 4), (tx - 10, hook_y)], fill=alpha(WHITE, 0.8), width=1)
    d.line([(tx + 10, beam_y + 4), (tx + 10, hook_y)], fill=alpha(WHITE, 0.8), width=1)

    # Crane hook / spreader bar
    d.line([(tx - 16, hook_y), (tx + 16, hook_y)], fill=WHITE, width=3)

    # Suspended Server Pod Payload
    if pod_payload:
        px0, py0 = tx - 28, hook_y + 4
        px1, py1 = tx + 28, hook_y + 54
        d.rounded_rectangle([px0, py0, px1, py1], radius=4, fill=(12, 18, 28), outline=TEAL, width=2)
        d.text((tx, (py0 + py1)/2), pod_payload, font=MONOB(9), fill=WHITE, anchor="mm")
