#!/usr/bin/env python3
"""
Hydraulic & Fluid Modular Apparatus Primitive.
Simulates pressure pipes, fluid valves, token bucket tanks,
and leaking faucets for rate limiting, memory leaks, and backpressure.
"""
import math
from engine.blueprint_engine import alpha, BG, WHITE, MUTED, DIM, TEAL, AMBER, RED, GREEN, BLUE, MONO, MONOB, SANS, SANSB

def draw_pipe(d, x0, y0, x1, y1, width=24, col=DIM, fluid_col=TEAL, flow_phase=0.0):
    """Draws an industrial pipe with moving fluid pulses"""
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1: return
    nx, ny = -dy / length * (width / 2), dx / length * (width / 2)

    # Pipe casing
    d.polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)],
              fill=(10, 14, 20), outline=alpha(col, 0.8))

    # Fluid core flow
    num_pulses = max(2, int(length / 28))
    for i in range(num_pulses):
        t = (i / num_pulses + flow_phase) % 1.0
        px = x0 + dx * t
        py = y0 + dy * t
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=alpha(fluid_col, 0.8))

def draw_fluid_tank(d, cx, cy, width=120, height=180, fill_ratio=0.5, col=DIM, fluid_col=TEAL, label=""):
    """Draws a vertical cylindrical pressure vessel / token bucket with liquid level"""
    x0, y0 = cx - width / 2, cy - height / 2
    x1, y1 = cx + width / 2, cy + height / 2

    # Vessel outer glass/metal frame
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=(8, 11, 16), outline=alpha(col, 0.9), width=2)

    # Measurement gauge tick marks
    num_ticks = 8
    for i in range(num_ticks + 1):
        ty = y1 - (i / num_ticks) * (height - 20) - 10
        t_len = 10 if (i % 2 == 0) else 5
        d.line([(x0 + 4, ty), (x0 + 4 + t_len, ty)], fill=alpha(MUTED, 0.5), width=1)
        d.line([(x1 - 4 - t_len, ty), (x1 - 4, ty)], fill=alpha(MUTED, 0.5), width=1)

    # Fluid column
    fill_ratio = max(0.0, min(1.0, fill_ratio))
    fluid_h = (height - 12) * fill_ratio
    if fluid_h > 2:
        fy0 = y1 - 6 - fluid_h
        fy1 = y1 - 6
        d.rectangle([x0 + 6, fy0, x1 - 6, fy1], fill=alpha(fluid_col, 0.75))
        # Surface wave meniscus
        d.line([(x0 + 6, fy0), (x1 - 6, fy0)], fill=WHITE, width=2)

    # Tank labels
    if label:
        d.text((cx, y0 - 16), label, font=MONOB(11), fill=WHITE, anchor="mm")
    # Percentage badge
    d.text((cx, y1 + 16), f"{int(fill_ratio * 100)}%", font=MONO(11), fill=fluid_col, anchor="mm")

def draw_valve(d, cx, cy, radius=18, open_angle=0.0, is_open=True, col=AMBER):
    """Draws a mechanical rotary valve wheel"""
    # Outer wheel rim
    vcol = GREEN if is_open else RED
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=(14, 18, 26), outline=alpha(vcol, 0.9), width=2)
    # Spokes
    for i in range(4):
        a = math.radians(open_angle + i * 90)
        sx, sy = cx + radius * math.cos(a), cy + radius * math.sin(a)
        d.line([(cx, cy), (sx, sy)], fill=alpha(vcol, 0.8), width=2)
    # Center nut
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=WHITE)
