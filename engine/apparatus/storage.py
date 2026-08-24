#!/usr/bin/env python3
"""
Storage Modular Apparatus Primitive: Silicon DRAM vs Magnetic Platter.
Simulates spinning magnetic hard disks with mechanical seek arms
and solid-state DRAM silicon memory transistor matrices.
"""
import math
from engine.blueprint_engine import alpha, BG, WHITE, MUTED, DIM, TEAL, AMBER, RED, GREEN, BLUE, MONO, MONOB, SANS, SANSB

def draw_magnetic_platter(d, cx, cy, radius=85, rotation_deg=0.0, arm_angle_deg=25.0, col=AMBER):
    """Draws a mechanical hard disk platter with tracks, spindle, and seek actuator arm"""
    # Drive chassis base
    d.rounded_rectangle([cx - radius - 20, cy - radius - 20, cx + radius + 35, cy + radius + 20],
                        radius=12, fill=(10, 13, 18), outline=alpha(DIM, 0.8), width=2)

    # Concentric magnetic tracks
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=(14, 18, 26), outline=alpha(col, 0.8), width=2)
    for r_ratio in [0.85, 0.70, 0.55, 0.40]:
        r = radius * r_ratio
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=alpha(col, 0.3), width=1)

    # Spinning sector spokes
    for i in range(8):
        a = math.radians(rotation_deg + i * 45)
        d.line([(cx + 25 * math.cos(a), cy + 25 * math.sin(a)),
                (cx + radius * math.cos(a), cy + radius * math.sin(a))],
               fill=alpha(col, 0.25), width=1)

    # Center motor spindle
    d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=(22, 28, 40), outline=WHITE, width=2)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=WHITE)

    # Stepper motor actuator pivot & voice coil
    piv_x, piv_y = cx + radius + 15, cy - radius + 15
    d.ellipse([piv_x - 14, piv_y - 14, piv_x + 14, piv_y + 14], fill=(20, 26, 38), outline=alpha(col, 0.8), width=2)

    # Actuator arm reaching toward platter tracks
    arm_rad = math.radians(180 + arm_angle_deg)
    head_x = piv_x + (radius * 1.15) * math.cos(arm_rad)
    head_y = piv_y + (radius * 1.15) * math.sin(arm_rad)
    d.line([(piv_x, piv_y), (head_x, head_y)], fill=WHITE, width=3)
    # Read/write head slider tip
    d.ellipse([head_x - 4, head_y - 4, head_x + 4, head_y + 4], fill=AMBER)

    # Platter label
    d.text((cx, cy + radius + 36), "MECHANICAL DISK (45ms)", font=MONOB(10), fill=AMBER, anchor="mm")

def draw_dram_silicon_stick(d, cx, cy, width=190, height=80, active_cell=(1, 2), col=TEAL):
    """Draws a solid-state DRAM memory module with silicon IC packages and gold contacts"""
    x0, y0 = cx - width / 2, cy - height / 2
    x1, y1 = cx + width / 2, cy + height / 2

    # Green/Teal PCB substrate
    d.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=(10, 18, 18), outline=alpha(col, 0.9), width=2)

    # Gold edge connector pins (bottom)
    num_pins = 24
    pin_w = (width - 20) / num_pins
    for i in range(num_pins):
        px = x0 + 10 + i * pin_w
        d.rectangle([px + 1, y1 - 8, px + pin_w - 2, y1], fill=(245, 190, 60))

    # Silicon IC memory chips (4 black epoxy blocks)
    num_chips = 4
    chip_w = (width - 40) / num_chips
    for i in range(num_chips):
        cx0 = x0 + 10 + i * chip_w + 4
        cx1 = cx0 + chip_w - 8
        cy0 = y0 + 12
        cy1 = y1 - 20
        is_active = (active_cell and active_cell[0] == i)
        chip_col = TEAL if is_active else (20, 26, 36)
        d.rectangle([cx0, cy0, cx1, cy1], fill=(12, 16, 22), outline=alpha(chip_col, 0.9), width=2 if is_active else 1)
        # Laser etched label
        d.text(((cx0 + cx1)/2, (cy0 + cy1)/2), f"RAM-{i+1}", font=MONO(9), fill=chip_col, anchor="mm")

    # Trace lines / data bus
    d.line([(x0 + 10, y0 + 6), (x1 - 10, y0 + 6)], fill=alpha(col, 0.5), width=1)

    # DRAM Module label
    d.text((cx, y1 + 18), "IN-MEMORY RAM (0.12ms)", font=MONOB(10), fill=TEAL, anchor="mm")
