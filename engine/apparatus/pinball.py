#!/usr/bin/env python3
"""
Pinball & Pachinko Modular Apparatus Primitive.
Simulates balls/packets dropping through pin lattices, bouncing off bumpers,
actuating flippers, and sorting into collector bins.
"""
import math
from PIL import ImageDraw
from engine.blueprint_engine import alpha, BG, WHITE, MUTED, DIM, TEAL, AMBER, RED, GREEN, BLUE, MONO, MONOB, SANS, SANSB

def draw_pinball_cabinet(d, cx, cy, width=480, height=440, col=DIM):
    """Draws an isometric/angled pinball machine cabinet with side rails and glass rim"""
    x0, y0 = cx - width / 2, cy - height / 2
    x1, y1 = cx + width / 2, cy + height / 2

    # Outer wooden/metal cabinet frame
    d.rounded_rectangle([x0 - 12, y0 - 12, x1 + 12, y1 + 12], radius=16, fill=(11, 14, 20), outline=alpha(col, 0.9), width=2)
    # Inner playing field
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=(7, 9, 13), outline=alpha(col, 0.5), width=1)

    # Decorative side rails & lane dividers
    d.line([(x0 + 36, y0 + 10), (x0 + 36, y1 - 60)], fill=alpha(col, 0.4), width=2)
    d.line([(x1 - 36, y0 + 10), (x1 - 36, y1 - 60)], fill=alpha(col, 0.4), width=2)

    # Top launcher arch
    d.arc([x0 + 20, y0 - 8, x1 - 20, y0 + 80], start=180, end=0, fill=alpha(col, 0.6), width=2)

def draw_pin_lattice(d, cx, cy, rows=4, cols=7, spacing_x=52, spacing_y=42, col=DIM, active_pin=None):
    """Draws hexagonal pin array for deflection"""
    pins = []
    y_start = cy - (rows * spacing_y) / 2
    for r in range(rows):
        offset = (spacing_x / 2) if (r % 2 == 1) else 0
        x_start = cx - (cols * spacing_x) / 2 + offset
        for c in range(cols):
            px = x_start + c * spacing_x
            py = y_start + r * spacing_y
            pins.append((px, py))
            is_active = (active_pin == (r, c))
            pin_col = AMBER if is_active else col
            r_size = 4 if is_active else 3
            d.ellipse([px - r_size, py - r_size, px + r_size, py + r_size], fill=alpha(pin_col, 0.9))
            if is_active:
                d.ellipse([px - 8, py - 8, px + 8, py + 8], outline=alpha(AMBER, 0.4), width=1)
    return pins

def draw_score_bumpers(d, bumpers, flash_idx=None, flash_col=TEAL):
    """
    Draws circular electronic bumpers that flash when struck.
    bumpers: list of (x, y, radius, label)
    """
    for idx, (bx, by, rad, label) in enumerate(bumpers):
        flashing = (idx == flash_idx)
        bcol = flash_col if flashing else BLUE
        # Outer ring
        d.ellipse([bx - rad, by - rad, bx + rad, by + rad], fill=(14, 19, 28), outline=alpha(bcol, 0.9), width=2)
        if flashing:
            d.ellipse([bx - rad - 6, by - rad - 6, bx + rad + 6, by + rad + 6], outline=alpha(flash_col, 0.5), width=2)
        # Inner core
        d.ellipse([bx - rad/2, by - rad/2, bx + rad/2, by + rad/2], fill=alpha(bcol, 0.8))
        if label:
            d.text((bx, by + rad + 12), label, font=MONO(10), fill=WHITE, anchor="mm")

def draw_flippers(d, left_xy, right_xy, angle_deg=25, length=44, col=WHITE):
    """Draws left and right mechanical flipper bats"""
    # Left flipper
    lx, ly = left_xy
    rad_l = math.radians(angle_deg)
    lex, ley = lx + length * math.cos(rad_l), ly + length * math.sin(rad_l)
    d.line([(lx, ly), (lex, ley)], fill=col, width=4)
    d.ellipse([lx - 5, ly - 5, lx + 5, ly + 5], fill=col)

    # Right flipper
    rx, ry = right_xy
    rad_r = math.radians(180 - angle_deg)
    rex, rey = rx + length * math.cos(rad_r), ry + length * math.sin(rad_r)
    d.line([(rx, ry), (rex, rey)], fill=col, width=4)
    d.ellipse([rx - 5, ry - 5, rx + 5, ry + 5], fill=col)

def draw_pinball_particle(d, x, y, radius=6, col=TEAL, glow=True):
    """Draws a glowing metallic pinball / packet sphere"""
    if glow:
        d.ellipse([x - radius - 4, y - radius - 4, x + radius + 4, y + radius + 4], fill=alpha(col, 0.25))
    d.ellipse([x - radius, y - radius, x + radius, y + radius], fill=col)
    # Highlight reflection
    d.ellipse([x - radius/2, y - radius/2, x, y], fill=(255, 255, 255, 180))
