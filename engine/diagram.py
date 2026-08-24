"""Reusable product-quality architecture diagram primitives for blueprint reels.

Logical diagrams opt into this module. Existing apparatus generators remain
unchanged. Geometry is separated from drawing so routes and ports can be tested
and shared by visual animation and sound-event timelines.
"""
from dataclasses import dataclass, field
import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter

from blueprint_engine import (
    BG, WHITE, MUTED, DIM, BLUE, AMBER, RED, TEAL, GREEN,
    MONO, MONOB, SANS, SANSB, alpha, ease, lerp,
)

Point = Tuple[float, float]
Bounds = Tuple[float, float, float, float]

STATE_COLORS = {
    "neutral": MUTED, "request": BLUE, "waiting": AMBER,
    "failure": RED, "protocol": TEAL, "success": GREEN,
}


def text_width(draw, text, font):
    return float(draw.textlength(text, font=font))


def truncate_text(draw, text, font, max_width):
    if text_width(draw, text, font) <= max_width:
        return text
    ellipsis = "…"
    while text and text_width(draw, text + ellipsis, font) > max_width:
        text = text[:-1]
    return text + ellipsis if text else ellipsis


def wrap_text(draw, text, font, max_width, max_lines=2):
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines - 1:
                break
    if current and len(lines) < max_lines:
        consumed = " ".join(lines + [current])
        remaining = text[len(consumed):].strip()
        lines.append(truncate_text(draw, current + ((" " + remaining) if remaining else ""), font, max_width))
    return lines or [""]


def point_on_path(path: Sequence[Point], progress: float):
    """Return a distance-correct point and tangent angle on a polyline."""
    if len(path) < 2:
        raise ValueError("A connector path needs at least two points")
    lengths = [math.dist(a, b) for a, b in zip(path, path[1:])]
    total = sum(lengths)
    target = max(0.0, min(1.0, progress)) * total
    walked = 0.0
    for index, ((a, b), length) in enumerate(zip(zip(path, path[1:]), lengths)):
        if target <= walked + length or index == len(lengths) - 1:
            t = 0 if length == 0 else (target - walked) / length
            return (lerp(a[0], b[0], t), lerp(a[1], b[1], t)), math.atan2(b[1] - a[1], b[0] - a[0])
        walked += length
    a, b = path[-2], path[-1]
    return b, math.atan2(b[1] - a[1], b[0] - a[0])


@dataclass(frozen=True)
class NodeLayout:
    bounds: Bounds
    ports: Dict[str, Point]


@dataclass
class ServiceNode:
    x: float
    y: float
    width: float
    height: float
    title: str
    subtitle: str = ""
    icon: str = "server"
    state: str = "neutral"
    badge: str = ""
    port_names: Dict[str, str] = field(default_factory=lambda: {"in": "left", "out": "right"})

    def layout(self) -> NodeLayout:
        w, h = max(126, self.width), max(82, self.height)
        x0, y0, x1, y1 = self.x, self.y, self.x + w, self.y + h
        sides = {
            "left": (x0, (y0 + y1) / 2), "right": (x1, (y0 + y1) / 2),
            "top": ((x0 + x1) / 2, y0), "bottom": ((x0 + x1) / 2, y1),
        }
        return NodeLayout((x0, y0, x1, y1), {name: sides[side] for name, side in self.port_names.items()})

    def draw(self, image, opacity=1.0, active=True):
        d = ImageDraw.Draw(image)
        layout = self.layout()
        x0, y0, x1, y1 = layout.bounds
        col = STATE_COLORS.get(self.state, MUTED)
        # Subtle offset shadow, inner surface, and an accent rail establish depth.
        d.rounded_rectangle([x0 + 4, y0 + 6, x1 + 4, y1 + 6], radius=14, fill=(5, 7, 11))
        d.rounded_rectangle(layout.bounds, radius=14, fill=(14, 18, 27), outline=alpha(col, opacity * .72), width=2)
        d.rounded_rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], radius=13, outline=alpha(DIM, opacity * .45), width=1)
        d.line([(x0 + 14, y0 + 2), (x1 - 14, y0 + 2)], fill=alpha(col, opacity), width=3)
        tile = (x0 + 14, y0 + 18, x0 + 54, y0 + 58)
        d.rounded_rectangle(tile, radius=9, fill=(8, 12, 19), outline=alpha(col, opacity * .65), width=1)
        draw_icon(d, self.icon, (x0 + 34, y0 + 38), col, opacity)
        max_text = x1 - (x0 + 66) - 12
        title = truncate_text(d, self.title, SANSB(13), max_text)
        d.text((x0 + 66, y0 + 24), title, font=SANSB(13), fill=alpha(WHITE, opacity), anchor="lm")
        for i, line in enumerate(wrap_text(d, self.subtitle, SANS(9), max_text, 2)):
            d.text((x0 + 66, y0 + 43 + i * 12), line, font=SANS(9), fill=alpha(MUTED, opacity), anchor="lm")
        if self.badge:
            bw = min(self.width - 28, text_width(d, self.badge, MONOB(8)) + 18)
            bx1, by0 = x1 - 12, y1 - 24
            d.rounded_rectangle([bx1 - bw, by0, bx1, by0 + 16], radius=8, fill=(9, 13, 19), outline=alpha(col, opacity * .65))
            d.text((bx1 - bw / 2, by0 + 8), truncate_text(d, self.badge, MONOB(8), bw - 10), font=MONOB(8), fill=alpha(col, opacity), anchor="mm")
        for name, (px, py) in layout.ports.items():
            d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=BG, outline=alpha(col, opacity), width=2)
        return layout


def draw_icon(d, kind, center, col=TEAL, opacity=1.0):
    """Small procedural silhouettes; intentionally no external icon dependency."""
    x, y = center
    c, m = alpha(col, opacity), alpha(MUTED, opacity * .7)
    if kind in ("ai", "client"):
        d.ellipse([x-11, y-11, x+11, y+11], outline=c, width=2)
        d.line([(x-6,y),(x+6,y),(x,y-7),(x,y+7)], fill=c, width=2)
        if kind == "client": d.arc([x-15,y-15,x+15,y+15], 210, 330, fill=m, width=2)
    elif kind in ("server", "tool"):
        for oy in (-10, 1):
            d.rounded_rectangle([x-13,y+oy,x+13,y+oy+8], radius=2, outline=c, width=2)
            d.ellipse([x+7,y+oy+2,x+10,y+oy+5], fill=c)
        if kind == "tool": d.line([(x-4,y-13),(x+9,y+10)], fill=m, width=2)
    elif kind == "files":
        d.polygon([(x-12,y-12),(x+4,y-12),(x+12,y-4),(x+12,y+12),(x-12,y+12)], outline=c)
        d.line([(x+4,y-12),(x+4,y-4),(x+12,y-4)], fill=c)
    elif kind == "database":
        d.ellipse([x-13,y-12,x+13,y-4], outline=c, width=2); d.ellipse([x-13,y+4,x+13,y+12], outline=c, width=2)
        d.line([(x-13,y-8),(x-13,y+8),(x+13,y+8),(x+13,y-8)], fill=c, width=2)
    elif kind == "weather":
        d.ellipse([x-12,y-3,x+4,y+10], outline=c, width=2); d.ellipse([x-2,y-9,x+11,y+9], outline=c, width=2)
        d.line([(x-12,y+10),(x+12,y+10)], fill=c, width=2); d.line([(x-5,y+14),(x-8,y+19)], fill=m, width=2)
    elif kind == "user":
        d.ellipse([x-6,y-13,x+6,y-1], outline=c, width=2); d.arc([x-13,y-1,x+13,y+17], 180, 360, fill=c, width=2)
    elif kind == "message":
        d.rounded_rectangle([x-14,y-9,x+14,y+8], radius=4, outline=c, width=2); d.polygon([(x-5,y+8),(x-1,y+14),(x+3,y+8)], fill=c)
    else:
        d.ellipse([x-10,y-10,x+10,y+10], outline=c, width=2)


def orthogonal_path(source: Point, destination: Point, waypoints: Optional[Sequence[Point]] = None):
    if waypoints:
        pts = [source, *waypoints, destination]
    else:
        mid_x = (source[0] + destination[0]) / 2
        pts = [source, (mid_x, source[1]), (mid_x, destination[1]), destination]
    compact = [pts[0]]
    for p in pts[1:]:
        if p != compact[-1]: compact.append(p)
    for a, b in zip(compact, compact[1:]):
        if a[0] != b[0] and a[1] != b[1]:
            raise ValueError("Logical connector segments must be orthogonal")
    return compact


def path_intersects_bounds(path: Sequence[Point], bounds: Bounds, include_endpoints=False):
    """True when an orthogonal path enters a rectangle's interior."""
    x0,y0,x1,y1=bounds
    for index,(a,b) in enumerate(zip(path,path[1:])):
        if not include_endpoints and (index==0 or index==len(path)-2):
            continue
        if a[0]==b[0] and x0<a[0]<x1 and max(min(a[1],b[1]),y0)<min(max(a[1],b[1]),y1): return True
        if a[1]==b[1] and y0<a[1]<y1 and max(min(a[0],b[0]),x0)<min(max(a[0],b[0]),x1): return True
    return False


def draw_connector(image, source: Point, destination: Point, color=BLUE, waypoints=None,
                   reveal=1.0, glow=True, arrow=True):
    """Draw beneath nodes and return the full final path for packet/audio reuse."""
    path = orthogonal_path(source, destination, waypoints)
    reveal = max(0.0, min(1.0, reveal))
    lengths = [math.dist(a, b) for a, b in zip(path, path[1:])]
    budget, shown = sum(lengths) * reveal, [path[0]]
    for a, b, length in zip(path, path[1:], lengths):
        if budget <= 0: break
        if budget >= length:
            shown.append(b); budget -= length
        else:
            t = budget / length if length else 0
            shown.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t))); break
    d = ImageDraw.Draw(image)
    if glow and len(shown) > 1:
        d.line(shown, fill=alpha(color, .16), width=9, joint="curve")
    if len(shown) > 1:
        d.line(shown, fill=alpha(color, .72), width=3, joint="curve")
    if arrow and reveal >= .995:
        tip, angle = point_on_path(path, 1)
        left = (tip[0] - 10*math.cos(angle-.55), tip[1] - 10*math.sin(angle-.55))
        right = (tip[0] - 10*math.cos(angle+.55), tip[1] - 10*math.sin(angle+.55))
        d.polygon([tip, left, right], fill=color)
    return path


def draw_packet(image, path, progress, label, color=BLUE, opacity=1.0, reverse=False):
    p = 1 - progress if reverse else progress
    (x, y), _ = point_on_path(path, ease(p))
    d = ImageDraw.Draw(image)
    f = MONOB(8)
    w = max(56, text_width(d, label, f) + 18)
    d.rounded_rectangle([x-w/2,y-12,x+w/2,y+12], radius=7, fill=(8,12,19), outline=alpha(color,opacity), width=2)
    d.text((x,y), label, font=f, fill=alpha(WHITE,opacity), anchor="mm")
    for trail in (.08, .15):
        (tx,ty),_ = point_on_path(path, max(0,min(1,p-trail if not reverse else p+trail)))
        d.ellipse([tx-2,ty-2,tx+2,ty+2], fill=alpha(color, opacity*(.45-trail)))
    return x, y


def draw_group(d, bounds, label, color=TEAL, opacity=1.0):
    x0,y0,x1,y1 = bounds
    d.rounded_rectangle(bounds, radius=18, fill=(10,14,21), outline=alpha(color,opacity*.45), width=1)
    d.rounded_rectangle([x0+12,y0-10,x0+12+text_width(d,label,MONOB(9))+20,y0+10], radius=10, fill=(12,17,24), outline=alpha(color,opacity*.6))
    d.text((x0+22,y0),label,font=MONOB(9),fill=alpha(color,opacity),anchor="lm")


def draw_protocol_bus(d, bounds, label="MCP · JSON-RPC", opacity=1.0):
    x0,y0,x1,y1 = bounds
    d.rounded_rectangle(bounds, radius=(y1-y0)/2, fill=(8,20,22), outline=alpha(TEAL,opacity), width=2)
    for x in range(int(x0+18), int(x1-12), 24): d.ellipse([x-2,(y0+y1)/2-2,x+2,(y0+y1)/2+2],fill=alpha(TEAL,opacity*.55))
    d.text(((x0+x1)/2,(y0+y1)/2),label,font=MONOB(9),fill=alpha(WHITE,opacity),anchor="mm")


def draw_step_badge(d, center, step, label, color=TEAL, opacity=1.0):
    x,y=center; d.ellipse([x-12,y-12,x+12,y+12],fill=(10,15,22),outline=alpha(color,opacity),width=2)
    d.text((x,y),str(step),font=MONOB(9),fill=alpha(color,opacity),anchor="mm")
    d.text((x+19,y),label,font=MONOB(8),fill=alpha(MUTED,opacity),anchor="lm")


def draw_prompt_bubble(d, bounds, text, opacity=1.0):
    x0,y0,x1,y1=bounds
    d.rounded_rectangle(bounds,radius=12,fill=(13,18,27),outline=alpha(BLUE,opacity*.7),width=1)
    d.polygon([(x0+24,y1),(x0+34,y1),(x0+28,y1+9)],fill=alpha(BLUE,opacity*.7))
    for i,line in enumerate(wrap_text(d,text,SANSB(10),x1-x0-24,2)):
        d.text((x0+12,y0+16+i*14),line,font=SANSB(10),fill=alpha(WHITE,opacity),anchor="lm")


def draw_result_panel(d, bounds, title, value, opacity=1.0, color=GREEN):
    x0,y0,x1,y1=bounds
    d.rounded_rectangle(bounds,radius=11,fill=(9,18,18),outline=alpha(color,opacity),width=2)
    d.text((x0+12,y0+15),title,font=MONOB(8),fill=alpha(MUTED,opacity),anchor="lm")
    d.text((x0+12,(y0+y1)/2+10),truncate_text(d,value,SANSB(15),x1-x0-24),font=SANSB(15),fill=alpha(color,opacity),anchor="lm")
