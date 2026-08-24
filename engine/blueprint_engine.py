#!/usr/bin/env python3
"""
Core Blueprint Video Engine — Dark Warm Slate Blueprint Aesthetic.
Branded for @buildebugship (Vibrant Red #fb7185) with modular vector apparatuses.
Engineered for Seamless Infinite Looping and High-Production Technical CAD Polish.
"""
import os, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 720, 1280, 30, 10
NF = FPS * DUR

BG      = (9, 11, 16)      # Deep Warm Slate Canvas (#090b10)
AMBER   = (245, 166, 35)   # Queue, Warning, Disk Latency (#f5a623)
AMBER_D = (140, 95, 20)
TEAL    = (64, 224, 208)   # In-Memory RAM, Healthy Fast Cache (#40e0d0)
TEAL_D  = (32, 120, 112)
BLUE    = (96, 165, 250)   # Network Gateways, Router Pulses (#60a5fa)
BLUE_D  = (40, 75, 130)
WHITE   = (255, 255, 255)  # Primary Titles & Outer Bounds
MUTED   = (148, 163, 184)  # HUD Labels & Subtitles (#94a3b8)
DIM     = (51, 65, 85)     # Inactive Rulers & Borders (#334155)
RED     = (251, 113, 133)  # Buildebugship Brand, Overload Alarm, Breach (#fb7185)
RED_D   = (159, 18, 57)
GREEN   = (52, 211, 153)   # 100% Uptime, Success Resolution (#34d153)
GREEN_D = (6, 95, 70)

FD = os.path.join(os.path.dirname(__file__), "..", "fonts")
def font(name, size): return ImageFont.truetype(os.path.join(FD, name), size)
MONO   = lambda s: font("DejaVuSansMono.ttf", s)
MONOB  = lambda s: font("DejaVuSansMono-Bold.ttf", s)
SANS   = lambda s: font("DejaVuSans.ttf", s)
SANSB  = lambda s: font("DejaVuSans-Bold.ttf", s)

def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def alpha(c, a):
    a = max(0.0, min(1.0, a))
    return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))

def lerp(a, b, t): return a + (b - a) * t

def track(d, xy, text, font, fill, sp=2, anchor="lt"):
    """letter-spaced text for crisp modern technical typography"""
    ws = [d.textlength(ch, font=font) for ch in text]
    total = sum(ws) + sp * (len(text) - 1)
    x, y = xy
    if anchor[0] == "m": x -= total / 2
    elif anchor[0] == "r": x -= total
    for ch, w in zip(text, ws):
        d.text((x, y), ch, font=font, fill=fill, anchor="l" + anchor[1])
        x += w + sp
    return total

def panel(d, quad, col, width=2):
    d.line(list(quad) + [quad[0]], fill=col, width=width, joint="curve")

def screen(d, x0, x1, ytop, ybot, skew, col, glow_col):
    """A tilted display panel with legs. skew>0 = outer edge shorter (left panel)."""
    d.line([(x0 + 10, ybot), (x0 + 10, ybot + 44)], fill=alpha(col, .45), width=2)
    d.line([(x1 - 10, ybot), (x1 - 10, ybot + 44)], fill=alpha(col, .45), width=2)
    d.ellipse([x0 + 6,  ybot + 40, x0 + 14, ybot + 48], fill=alpha(col, .8))
    d.ellipse([x1 - 14, ybot + 40, x1 - 6,  ybot + 48], fill=alpha(col, .8))

    if skew > 0: # left panel
        quad = [(x0, ytop + skew), (x1, ytop), (x1, ybot), (x0, ybot - skew)]
    else:        # right panel
        quad = [(x0, ytop), (x1, ytop - skew), (x1, ybot + skew), (x0, ybot)]
    panel(d, quad, col, 2)
    inset = 8
    if skew > 0:
        in_quad = [(x0 + inset, ytop + skew + inset),
                   (x1 - inset, ytop + inset),
                   (x1 - inset, ybot - inset),
                   (x0 + inset, ybot - skew - inset)]
    else:
        in_quad = [(x0 + inset, ytop + inset),
                   (x1 - inset, ytop - skew + inset),
                   (x1 - inset, ybot + skew - inset),
                   (x0 + inset, ybot - inset)]
    return in_quad

def belt(d, ax, ay, bx, by, rungs, w, col, phase=0.0):
    """Isometric-perspective conveyor belt: two rail lines and moving rungs."""
    d.line([(ax - w, ay), (bx - w, by)], fill=alpha(col, .7), width=2)
    d.line([(ax + w, ay), (bx + w, by)], fill=alpha(col, .7), width=2)
    for i in range(rungs):
        t = (i / rungs + phase) % 1.0
        rx0, ry0 = lerp(ax - w, bx - w, t), lerp(ay, by, t)
        rx1, ry1 = lerp(ax + w, bx + w, t), lerp(ay, by, t)
        ra = (0.35 + 0.30 * math.sin(t * math.pi))
        d.line([(rx0, ry0), (rx1, ry1)], fill=alpha(col, ra), width=1)

def machine(d, cx, cy, w, h, col, label="", lab_font=None):
    """Isometric extruded box machine with cooling rotary vent."""
    if lab_font is None: lab_font = MONO(11)
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    d.rectangle([x0, y0, x1, y1], fill=(12, 16, 24), outline=WHITE, width=2)
    depth = 14
    d.polygon([(x0, y0), (x0 + depth, y0 - depth),
               (x1 + depth, y0 - depth), (x1, y0)], fill=(18, 24, 36), outline=alpha(col, .8))
    d.polygon([(x1, y0), (x1 + depth, y0 - depth),
               (x1 + depth, y1 - depth), (x1, y1)], fill=(14, 18, 28), outline=alpha(col, .8))
    # antenna
    d.line([(cx, y0 - depth), (cx, y0 - depth - 22)], fill=alpha(col, .9), width=2)
    d.ellipse([cx - 4, y0 - depth - 26, cx + 4, y0 - depth - 18], fill=alpha(col, .9))
    # rotary vent
    d.ellipse([x0 + 14, cy - 13, x0 + 40, cy + 13], outline=alpha(col, .6), width=2)
    for k in range(6):
        a = k * math.pi / 3
        d.line([(x0 + 27, cy), (x0 + 27 + 12 * math.cos(a), cy + 12 * math.sin(a))],
               fill=alpha(col, .5), width=1)
    # display window
    wx0, wx1 = cx - 42, cx + 60
    d.rectangle([wx0, cy - 12, wx1, cy + 12], fill=(6, 8, 12), outline=WHITE, width=1)
    if label:
        d.text(((wx0 + wx1) / 2, cy), label, font=lab_font, fill=WHITE, anchor="mm")

def draw_blueprint_grid(d, width=W, height=H, spacing=48):
    """Draws a subtle, high-tech architectural CAD dot grid"""
    for x in range(36, width - 36, spacing):
        for y in range(80, height - 80, spacing):
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(22, 28, 40))

def draw_cad_crosshairs(d, x, y, size=8, col=DIM):
    """Draws technical CAD alignment crosshairs"""
    d.line([(x - size, y), (x + size, y)], fill=alpha(col, 0.7), width=1)
    d.line([(x, y - size), (x, y + size)], fill=alpha(col, 0.7), width=1)

def draw_header_bar(d, intro, handle="@buildebugship", comp_left="TRADITIONAL", comp_right="OPTIMIZED",
                    title1="SYSTEM", title_vs="vs", title2="DESIGN", subhook="how distributed systems scale seamlessly",
                    brand_accent=RED):
    """
    Renders standard header with glowing @buildebugship branding pill and CAD technical layout
    """
    # Background CAD grid
    draw_blueprint_grid(d)

    # CAD Corner Registration Crosshairs
    draw_cad_crosshairs(d, 48, 140)
    draw_cad_crosshairs(d, W - 48, 140)

    # Red Handle Branding Pill with live pulsing LED
    pill_w = d.textlength(handle, font=MONOB(12)) + 36
    px0, py0 = W / 2 - pill_w / 2, 148
    px1, py1 = W / 2 + pill_w / 2, 172
    d.rounded_rectangle([px0, py0, px1, py1], radius=12, fill=(18, 14, 20), outline=alpha(brand_accent, 0.8 * intro), width=1)
    # Pulsing red LED
    d.ellipse([px0 + 10, py0 + 8, px0 + 16, py0 + 14], fill=brand_accent)
    d.text((px0 + 24, py0 + 11), handle, font=MONOB(12), fill=alpha(WHITE, intro), anchor="lm")

    # Comparison Tag Pill
    comp_str = f"{comp_left}   vs   {comp_right}"
    track(d, (W / 2, 192), comp_str, MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")

    # Large Bold Headline, fitted to the safe horizontal span.
    title_size, vs_size = 40, 32
    while True:
        title_font, vs_font = SANSB(title_size), SANSB(vs_size)
        tw1 = d.textlength(title1 + " ", font=title_font)
        tw2 = d.textlength(title_vs + " ", font=vs_font)
        tw3 = d.textlength(title2, font=title_font)
        if tw1 + tw2 + tw3 <= W - 80 or title_size <= 20:
            break
        title_size -= 1
        vs_size = max(20, title_size - 8)
    sx = W / 2 - (tw1 + tw2 + tw3) / 2
    d.text((sx, 228), title1 + " ", font=title_font, fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 230), title_vs + " ", font=vs_font, fill=alpha(DIM, intro), anchor="lm")
    d.text((sx + tw1 + tw2, 228), title2, font=title_font, fill=alpha(TEAL, intro), anchor="lm")

    # Subhook Context
    d.text((W / 2, 268), subhook, font=SANS(13), fill=alpha(BLUE, intro * 0.95), anchor="mm")

    # Lower Divider Ruler
    d.line([(48, 290), (W - 48, 290)], fill=alpha(DIM, 0.6), width=1)

def draw_telemetry_hud(d, m1_label, m1_val, m2_label, m2_val, a, m1_col=TEAL, m2_col=AMBER):
    """Draws premium left and right telemetry HUD cards with glowing accent borders"""
    # Left Metric Card
    lx0, ly0, lx1, ly1 = 48, 304, 340, 376
    d.rounded_rectangle([lx0, ly0, lx1, ly1], radius=8, fill=(12, 16, 24), outline=alpha(m1_col, a * 0.6), width=1)
    d.line([(lx0 + 8, ly0), (lx1 - 8, ly0)], fill=alpha(m1_col, a), width=2)
    track(d, (lx0 + 14, ly0 + 18), m1_label, MONOB(10), alpha(MUTED, a), sp=2)
    d.text((lx0 + 14, ly0 + 48), m1_val, font=MONOB(20), fill=alpha(m1_col, a), anchor="lm")

    # Right Metric Card
    rx0, ry0, rx1, ry1 = 380, 304, 672, 376
    d.rounded_rectangle([rx0, ry0, rx1, ry1], radius=8, fill=(12, 16, 24), outline=alpha(m2_col, a * 0.6), width=1)
    d.line([(rx0 + 8, ry0), (rx1 - 8, ry0)], fill=alpha(m2_col, a), width=2)
    track(d, (rx1 - 14, ry0 + 18), m2_label, MONOB(10), alpha(MUTED, a), sp=2, anchor="rt")
    d.text((rx1 - 14, ry0 + 48), m2_val, font=MONOB(20), fill=alpha(m2_col, a), anchor="rm")

def draw_caption_pill(d, fr, captions, a):
    """Compatibility no-op: posting captions are never burned into video frames."""
    return None

def draw_loop_particle_flow(d, path_points, t, num_particles=8, col=TEAL):
    """
    Renders smoothly circulating data particles along path_points.
    Guaranteed 100% seamless looping when t goes from 0.0 to 1.0 (or integer multiples).
    """
    total_segments = len(path_points) - 1
    if total_segments < 1: return
    for p in range(num_particles):
        progress = (t * 2.0 + p / num_particles) % 1.0
        seg_idx = int(progress * total_segments)
        seg_idx = min(seg_idx, total_segments - 1)
        sub_t = (progress * total_segments) - seg_idx
        p0 = path_points[seg_idx]
        p1 = path_points[seg_idx + 1]
        x = lerp(p0[0], p1[0], sub_t)
        y = lerp(p0[1], p1[1], sub_t)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=col)
        d.ellipse([x - 8, y - 8, x + 8, y + 8], outline=alpha(col, 0.4), width=1)

def finish(img, fr=0):
    """Lean, ultra-crisp output preserving razor-sharp typography and vector lines."""
    return img
