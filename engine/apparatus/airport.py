#!/usr/bin/env python3
"""
Airport & Runway Modular Apparatus Primitive.
Simulates ATC radar towers, runways, holding pattern flight paths,
and boarding gate docking for request queueing, rate limiting, and VPN routing.
"""
import math
from engine.blueprint_engine import alpha, BG, WHITE, MUTED, DIM, TEAL, AMBER, RED, GREEN, BLUE, MONO, MONOB, SANS, SANSB

def draw_runway(d, x, y_start, y_end, width=80, col=DIM, lights_phase=0.0):
    """Draws an illuminated airport landing runway with centerline dashes and edge lights"""
    x0, x1 = x - width / 2, x + width / 2
    # Dark asphalt track
    d.rectangle([x0, y_start, x1, y_end], fill=(10, 13, 18), outline=alpha(col, 0.8), width=2)

    # Edge landing lights
    num_lights = 12
    step = (y_end - y_start) / (num_lights - 1)
    for i in range(num_lights):
        ly = y_start + i * step
        lp = (i / num_lights + lights_phase) % 1.0
        light_col = AMBER if lp > 0.5 else BLUE
        d.ellipse([x0 - 5, ly - 3, x0 + 1, ly + 3], fill=alpha(light_col, 0.9))
        d.ellipse([x1 - 1, ly - 3, x1 + 5, ly + 3], fill=alpha(light_col, 0.9))

    # Centerline dashes
    dash_len = 16
    dash_gap = 14
    cy = y_start + 10
    while cy < y_end - 10:
        d.line([(x, cy), (x, cy + dash_len)], fill=alpha(WHITE, 0.7), width=3)
        cy += dash_len + dash_gap

    # Threshold markers (piano keys)
    for k in range(5):
        kx = x0 + 12 + k * 14
        d.rectangle([kx, y_start + 4, kx + 8, y_start + 24], fill=WHITE)
        d.rectangle([kx, y_end - 24, kx + 8, y_end - 4], fill=WHITE)

def draw_airplane(d, x, y, heading_deg=0, scale=1.0, col=TEAL, label=""):
    """Draws a crisp geometric vector jet aircraft with wing lights"""
    rad = math.radians(heading_deg - 90)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    def rot(dx, dy):
        return (x + (dx * cos_a - dy * sin_a) * scale,
                y + (dx * sin_a + dy * cos_a) * scale)

    # Fuselage
    nose = rot(0, -22)
    wing_l = rot(-24, 6)
    wing_r = rot(24, 6)
    tail_l = rot(-10, 20)
    tail_r = rot(10, 20)
    tail_tip = rot(0, 24)

    # Jet body polygon
    d.polygon([nose, wing_l, rot(-6, 8), tail_l, tail_tip, tail_r, rot(6, 8), wing_r],
              fill=(14, 18, 26), outline=col, width=2)
    # Cockpit window
    d.line([rot(0, -14), rot(0, -8)], fill=WHITE, width=2)

    # Wingtip navigation lights (Red port, Green starboard)
    d.ellipse([wing_l[0]-3, wing_l[1]-3, wing_l[0]+3, wing_l[1]+3], fill=RED)
    d.ellipse([wing_r[0]-3, wing_r[1]-3, wing_r[0]+3, wing_r[1]+3], fill=GREEN)

    if label:
        d.text((x, y + 28 * scale), label, font=MONO(10), fill=WHITE, anchor="mm")

def draw_radar_scope(d, cx, cy, radius=65, sweep_deg=45, col=GREEN):
    """Draws an Air Traffic Control radar circle with rotating sweep beam and blips"""
    # Outer radar dial
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=(6, 12, 10), outline=alpha(col, 0.7), width=2)
    # Range rings
    d.ellipse([cx - radius*0.66, cy - radius*0.66, cx + radius*0.66, cy + radius*0.66],
              outline=alpha(col, 0.35), width=1)
    d.ellipse([cx - radius*0.33, cy - radius*0.33, cx + radius*0.33, cy + radius*0.33],
              outline=alpha(col, 0.2), width=1)
    # Crosshairs
    d.line([(cx - radius, cy), (cx + radius, cy)], fill=alpha(col, 0.3), width=1)
    d.line([(cx, cy - radius), (cx, cy + radius)], fill=alpha(col, 0.3), width=1)

    # Rotating sweep cone
    rad = math.radians(sweep_deg)
    sx, sy = cx + radius * math.cos(rad), cy + radius * math.sin(rad)
    d.line([(cx, cy), (sx, sy)], fill=col, width=2)

    # Sweep glow gradient
    for i in range(1, 6):
        a_rad = math.radians(sweep_deg - i * 4)
        gx, gy = cx + radius * math.cos(a_rad), cy + radius * math.sin(a_rad)
        d.line([(cx, cy), (gx, gy)], fill=alpha(col, (6 - i) * 0.12), width=1)

def draw_holding_pattern(d, cx, cy, rx=70, ry=45, progress=0.0, col=AMBER):
    """Draws an elliptical holding pattern orbit with a moving aircraft"""
    # Track ring
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=alpha(col, 0.4), width=1)
    # Orbiting plane
    angle = progress * 2.0 * math.pi
    px = cx + rx * math.cos(angle)
    py = cy + ry * math.sin(angle)
    heading = math.degrees(angle) + 90
    draw_airplane(d, px, py, heading_deg=heading, scale=0.6, col=col)
