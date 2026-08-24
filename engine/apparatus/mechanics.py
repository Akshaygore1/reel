#!/usr/bin/env python3
"""
Mechanical Gears, Clocks & Sliding Gates Modular Apparatus Primitive.
Simulates interlocking spur gears, rotating clock dials, and crontab sliding gates.
"""
import math
from engine.blueprint_engine import alpha, BG, WHITE, MUTED, DIM, TEAL, AMBER, RED, GREEN, BLUE, MONO, MONOB, SANS, SANSB

def draw_spur_gear(d, cx, cy, radius=40, teeth=12, angle_deg=0.0, col=DIM, fill_col=(12, 16, 24)):
    """Draws a mechanical gear wheel with extruded teeth"""
    tooth_depth = radius * 0.22
    pts = []
    num_pts = teeth * 4
    base_rad = radius - tooth_depth / 2
    tip_rad = radius + tooth_depth / 2

    for i in range(num_pts):
        a = math.radians(angle_deg + (i / num_pts) * 360.0)
        # 4 states per tooth: base1, tip1, tip2, base2
        state = i % 4
        r = tip_rad if (state in (1, 2)) else base_rad
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    # Outer gear contour
    d.polygon(pts, fill=fill_col, outline=alpha(col, 0.9))

    # Center shaft & mounting holes
    d.ellipse([cx - radius*0.35, cy - radius*0.35, cx + radius*0.35, cy + radius*0.35],
              fill=(8, 10, 14), outline=alpha(col, 0.7), width=1)
    d.ellipse([cx - radius*0.12, cy - radius*0.12, cx + radius*0.12, cy + radius*0.12],
              fill=alpha(col, 0.9))

def draw_clock_dial(d, cx, cy, radius=70, hour_angle=0.0, minute_angle=0.0, col=WHITE):
    """Draws a precision technical clock dial with ticks and hands"""
    # Outer housing
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=(10, 14, 20), outline=alpha(col, 0.8), width=2)
    d.ellipse([cx - radius + 4, cy - radius + 4, cx + radius - 4, cy + radius - 4],
              outline=alpha(DIM, 0.5), width=1)

    # 12-hour tick marks
    for h in range(12):
        a = math.radians(h * 30 - 90)
        is_major = (h % 3 == 0)
        t_len = 10 if is_major else 5
        x0 = cx + (radius - 8 - t_len) * math.cos(a)
        y0 = cy + (radius - 8 - t_len) * math.sin(a)
        x1 = cx + (radius - 8) * math.cos(a)
        y1 = cy + (radius - 8) * math.sin(a)
        d.line([(x0, y0), (x1, y1)], fill=WHITE if is_major else MUTED, width=2 if is_major else 1)

    # Hour hand
    hr_rad = math.radians(hour_angle - 90)
    hx = cx + radius * 0.50 * math.cos(hr_rad)
    hy = cy + radius * 0.50 * math.sin(hr_rad)
    d.line([(cx, cy), (hx, hy)], fill=WHITE, width=3)

    # Minute hand
    min_rad = math.radians(minute_angle - 90)
    mx = cx + radius * 0.75 * math.cos(min_rad)
    my = cy + radius * 0.75 * math.sin(min_rad)
    d.line([(cx, cy), (mx, my)], fill=TEAL, width=2)

    # Center pinion
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=AMBER)

def draw_cron_gates(d, cx, cy, width=440, height=220, gates_open=[True, True, True, True, True], col=DIM):
    """
    Draws 5 sliding mechanical gates for crontab syntax:
    [MIN, HOUR, DOM, MON, DOW]
    """
    labels = ["MIN", "HOUR", "DOM", "MON", "DOW"]
    gate_w = (width - 40) / 5
    x_start = cx - width / 2 + 20

    # Housing frame
    d.rounded_rectangle([cx - width/2, cy - height/2, cx + width/2, cy + height/2],
                        radius=12, fill=(10, 13, 18), outline=alpha(col, 0.8), width=2)

    # Laser alignment beam across center
    all_open = all(gates_open)
    laser_col = GREEN if all_open else RED
    d.line([(cx - width/2 + 10, cy), (cx + width/2 - 10, cy)], fill=alpha(laser_col, 0.9), width=2)

    for i in range(5):
        gx = x_start + i * gate_w + gate_w / 2
        is_open = gates_open[i]
        gate_col = GREEN if is_open else AMBER

        # Column channel
        d.rectangle([gx - gate_w/2 + 4, cy - height/2 + 30, gx + gate_w/2 - 4, cy + height/2 - 30],
                    fill=(6, 8, 12), outline=alpha(DIM, 0.5), width=1)

        # Sliding gate plate (slides down when open)
        offset = 40 if is_open else 0
        d.rounded_rectangle([gx - gate_w/2 + 6, cy - 25 + offset, gx + gate_w/2 - 6, cy + 25 + offset],
                            radius=4, fill=(18, 24, 34), outline=alpha(gate_col, 0.9), width=2)

        # Slot aperture in the center
        d.ellipse([gx - 6, cy - 6 + offset, gx + 6, cy + 6 + offset], fill=laser_col if is_open else (6, 8, 12))

        # Gate label
        d.text((gx, cy - height/2 + 16), labels[i], font=MONOB(10), fill=MUTED, anchor="mm")
        # Star or value badge
        d.text((gx, cy + height/2 - 14), "*" if is_open else "MATCH", font=MONOB(10), fill=gate_col, anchor="mm")
