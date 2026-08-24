#!/usr/bin/env python3
"""
Flagship System Design Reel: Garbage Collection
Visual apparatus: a glass heap arena fills with linked object capsules until a
stop-the-world alarm fires; root probes drive a tri-color tracing arm, a sweep
gate dissolves unreachable islands, and a compactor piston packs survivors.
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
    (0,   "your program allocates objects into a 64MB managed heap."),
    (60,  "references disappear, but unreachable objects still occupy memory."),
    (124, "heap at 96%: allocation stops for a 180ms full collection."),
    (188, "GC traces every object reachable from stack and static roots."),
    (250, "sweep the dead, compact survivors: 38% heap, 12ms pause."),
]

ARENA = (60, 482, 660, 884)
ROOTS = [(136, 438, "STACK"), (360, 438, "STATIC"), (584, 438, "JNI")]

# Organic capsule geometry: x, y, width, height. Deliberately irregular so the
# heap reads as a physical memory arena, never a grid of generic server boxes.
OBJECTS = [
    (100, 520, 70, 34), (188, 512, 84, 42), (308, 526, 62, 30),
    (410, 510, 92, 44), (546, 526, 72, 32),
    (116, 590, 92, 38), (250, 578, 66, 46), (360, 602, 80, 32),
    (486, 578, 64, 46), (570, 618, 54, 30),
    (100, 666, 64, 42), (184, 650, 76, 32), (292, 674, 92, 42),
    (426, 654, 70, 34), (534, 684, 94, 40),
    (110, 742, 78, 34), (228, 724, 58, 44), (326, 754, 72, 30),
    (438, 724, 86, 44), (562, 758, 60, 34),
    (110, 820, 90, 36), (214, 804, 72, 44), (324, 828, 62, 34),
    (420, 812, 74, 38), (526, 826, 92, 40),
    (346, 562, 46, 28), (624, 558, 42, 30),
]

# Reachability graph discovered from the three GC roots. Everything else is
# garbage, even if it is physically adjacent to a live object.
LIVE = {0, 1, 3, 4, 5, 7, 8, 11, 12, 14, 16, 18, 21, 23, 25}
ROOT_TARGETS = [0, 3, 4]
EDGES = [
    (0, 1), (0, 5), (1, 7), (3, 8), (3, 12), (4, 14), (5, 11),
    (7, 16), (8, 18), (11, 21), (12, 23), (14, 25),
]
MARK_ORDER = [0, 3, 4, 1, 5, 8, 12, 14, 7, 11, 25, 16, 18, 21, 23]


def object_count(fr):
    if fr < 90:
        return min(12, 5 + int(7 * ease((fr - 18) / 62)))
    return min(len(OBJECTS), 12 + int(15 * ease((fr - 90) / 78)))


def compact_slot(rank):
    """Packed survivor positions in a dense left-to-right nursery band."""
    col, row = rank % 3, rank // 3
    return 110 + col * 135, 530 + row * 66


def capsule_path(cx, cy, w, h):
    """Eight-sided memory capsule with chamfered allocation ports."""
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    c = min(10, h / 3)
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
            (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def object_center(idx, fr):
    x, y, _, _ = OBJECTS[idx]
    if fr >= 238 and idx in LIVE:
        rank = sorted(LIVE).index(idx)
        tx, ty = compact_slot(rank)
        ct = ease((fr - 238) / 30)
        return lerp(x, tx, ct), lerp(y, ty, ct)
    return x, y


def draw_allocation_rail(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    rail_col = GREEN if beat3 else (RED if beat2 else BLUE)
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    ca = a * (pulse if beat2 else 1.0)
    d.line([(76, 406), (644, 406)], fill=alpha(rail_col, ca * 0.7), width=2)
    for x in range(92, 645, 46):
        off = (fr * (4 if beat2 else 2)) % 46
        px = 76 + ((x - 76 + off) % 568)
        d.line([(px, 400), (px + 10, 406), (px, 412)], fill=alpha(rail_col, ca * 0.55), width=1)
    track(d, (W / 2, 390),
          "ALLOCATOR PAUSED — FULL GC" if beat2 and not beat3 else
          ("MUTATOR RESUMED — FREE LIST READY" if fr >= 250 else
           ("COLLECTOR ACTIVE — MUTATOR PAUSED" if beat3 else "ALLOCATION RAIL — OBJECTS ENTER THE HEAP")),
          MONOB(9), alpha(rail_col, ca), sp=1, anchor="mm")


def draw_roots(d, fr, a):
    beat3 = fr >= 180
    for k, (x, y, label) in enumerate(ROOTS):
        active = beat3 and fr >= 184 + k * 5
        col = GREEN if active else (BLUE if not beat3 else MUTED)
        d.ellipse([x - 34, y - 16, x + 34, y + 16], fill=(12, 16, 24),
                  outline=alpha(col, a * (0.95 if active else 0.6)), width=2)
        d.text((x, y), label, font=MONOB(9), fill=alpha(col, a), anchor="mm")
        tx, ty = object_center(ROOT_TARGETS[k], fr)
        d.line([(x, y + 16), (tx, ty)], fill=alpha(col, a * (0.9 if active else 0.35)), width=2)
        if active:
            p = ease((fr - (184 + k * 5)) / 12)
            ox, oy = lerp(x, tx, p), lerp(y + 16, ty, p)
            d.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], fill=alpha(GREEN, a))


def draw_heap_shell(d, fr, a):
    x0, y0, x1, y1 = ARENA
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    col = GREEN if beat3 else (RED if beat2 else TEAL)
    ca = a * (pulse if beat2 else 1.0)
    # Glass vessel, side rails, address ruler, and pressure gauge.
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, fill=(10, 14, 20),
                        outline=alpha(col, ca * 0.9), width=2)
    d.line([(x0 + 18, y0 + 18), (x0 + 18, y1 - 18)], fill=alpha(DIM, a), width=1)
    d.line([(x1 - 18, y0 + 18), (x1 - 18, y1 - 18)], fill=alpha(DIM, a), width=1)
    for y in range(y0 + 34, y1 - 18, 36):
        d.line([(x0 + 10, y), (x0 + 24, y)], fill=alpha(DIM, a * 0.8), width=1)
    d.text((x0 + 12, y0 - 14), "0x0000", font=MONO(8), fill=alpha(MUTED, a), anchor="lm")
    d.text((x1 - 12, y0 - 14), "64MB MANAGED HEAP", font=MONOB(9), fill=alpha(col, ca), anchor="rm")

    if beat3:
        fill = lerp(.96, .38, ease((fr - 218) / 42))
    elif beat2:
        fill = lerp(.42, .96, ease((fr - 90) / 78))
    else:
        fill = lerp(.18, .42, ease((fr - 12) / 68))
    gx0, gy0, gx1, gy1 = 674, 502, 688, 864
    d.rounded_rectangle([gx0, gy0, gx1, gy1], radius=7, outline=alpha(DIM, a), width=1)
    fy = lerp(gy1, gy0, fill)
    d.rounded_rectangle([gx0 + 3, fy, gx1 - 3, gy1 - 3], radius=4,
                        fill=alpha(col, ca * 0.85))


def draw_graph_edges(d, fr, a):
    count = object_count(fr)
    marked_n = int(len(MARK_ORDER) * ease((fr - 184) / 48)) if fr >= 180 else 0
    marked = set(MARK_ORDER[:marked_n])
    compact = ease((fr - 238) / 30)
    for src, dst in EDGES:
        if src >= count or dst >= count:
            continue
        x0, y0 = object_center(src, fr)
        x1, y1 = object_center(dst, fr)
        live_edge = src in marked and dst in marked
        col = GREEN if live_edge else (BLUE if fr < 180 else DIM)
        ea = a * (0.85 if live_edge else (0.38 * (1 - compact * .6)))
        d.line([(x0, y0), (x1, y1)], fill=alpha(col, ea), width=2 if live_edge else 1)


def draw_objects(d, fr, a):
    count = object_count(fr)
    marked_n = int(len(MARK_ORDER) * ease((fr - 184) / 48)) if fr >= 180 else 0
    marked = set(MARK_ORDER[:marked_n])
    sweep_x = lerp(ARENA[0] + 20, ARENA[2] - 20, ease((fr - 214) / 34))
    for idx, (_, _, ow, oh) in enumerate(OBJECTS[:count]):
        live = idx in LIVE
        x, y = object_center(idx, fr)
        born = ease((fr - (12 + idx * (6 if idx < 12 else 3))) / 8)
        if born <= .01:
            continue
        dead_swept = fr >= 214 and not live and OBJECTS[idx][0] <= sweep_x
        vanish = 1 - ease((fr - (214 + int((OBJECTS[idx][0] - 60) / 17))) / 10) if dead_swept else 1.0
        oa = a * born * vanish
        if oa <= .01:
            continue
        if fr < 180:
            col = BLUE if live else AMBER
        elif idx in marked:
            col = GREEN
        elif live:
            col = WHITE
        else:
            col = RED
        pulse = 0.75 + 0.25 * math.sin(fr * .32 + idx)
        pts = capsule_path(x, y, ow, oh)
        d.polygon(pts, fill=alpha(col, oa * (0.12 if live else 0.08)))
        d.line(pts + [pts[0]], fill=alpha(col, oa * pulse), width=2, joint="curve")
        # Allocation header, object id, and twin reference ports.
        d.line([(x - ow * .28, y - oh * .12), (x + ow * .18, y - oh * .12)],
               fill=alpha(col, oa * .45), width=1)
        d.ellipse([x + ow * .24 - 3, y - 3, x + ow * .24 + 3, y + 3], fill=alpha(col, oa))
        d.text((x - ow * .28, y + oh * .15), f"o{idx:02d}", font=MONO(7),
               fill=alpha(WHITE, oa * .85), anchor="lm")
        if dead_swept and vanish > .05:
            rr = 5 + 16 * (1 - vanish)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=alpha(RED, oa), width=1)


def draw_collector(d, fr, a):
    if fr < 90:
        return
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    if fr < 180:
        # Stop-the-world clamp closes around the full heap.
        close = ease((fr - 90) / 12)
        for side in (-1, 1):
            x = lerp(30 if side < 0 else 690, 70 if side < 0 else 650, close)
            d.polygon([(x, 610), (x + side * 26, 630), (x + side * 26, 738), (x, 758)],
                      fill=alpha(RED_D, a * pulse), outline=alpha(RED, a * pulse))
        if fr >= 146:
            st = ease((fr - 146) / 8)
            track(d, (W / 2, 916), "✗ STOP-THE-WORLD · 180ms PAUSE",
                  MONOB(14), alpha(RED, a * st * pulse), sp=2, anchor="mm")
        return

    # Mark phase: a rotating tracing head follows the root graph.
    if fr < 232:
        t = ease((fr - 180) / 52)
        idx = min(len(MARK_ORDER) - 1, int(t * len(MARK_ORDER)))
        ox, oy = object_center(MARK_ORDER[idx], fr)
        ring = 14 + 4 * math.sin(fr * .5)
        d.ellipse([ox - ring, oy - ring, ox + ring, oy + ring], outline=alpha(GREEN, a), width=2)
        d.line([(ox - 18, oy), (ox + 18, oy)], fill=alpha(GREEN, a * .7), width=1)
        d.line([(ox, oy - 18), (ox, oy + 18)], fill=alpha(GREEN, a * .7), width=1)
        track(d, (W / 2, 916), f"MARK QUEUE · {min(len(MARK_ORDER), idx + 1):02d} REACHABLE OBJECTS",
              MONOB(11), alpha(GREEN, a), sp=2, anchor="mm")

    # Sweep phase: a luminous vertical reclaim gate traverses the arena.
    if 214 <= fr <= 252:
        sx = lerp(ARENA[0] + 20, ARENA[2] - 20, ease((fr - 214) / 34))
        d.line([(sx, ARENA[1] + 18), (sx, ARENA[3] - 18)], fill=alpha(RED, a * .35), width=7)
        d.line([(sx, ARENA[1] + 18), (sx, ARENA[3] - 18)], fill=alpha(WHITE, a), width=2)
        d.polygon([(sx - 10, ARENA[1] + 20), (sx + 10, ARENA[1] + 20), (sx, ARENA[1] + 34)],
                  fill=alpha(RED, a))

    # Compaction piston mechanically pushes the survivors into a dense band.
    if fr >= 238:
        ct = ease((fr - 238) / 30)
        px = lerp(ARENA[2] + 10, 465, ct)
        d.polygon([(px, 500), (px + 22, 516), (px + 22, 850), (px, 866)],
                  fill=alpha(GREEN_D, a * .8), outline=alpha(GREEN, a))
        track(d, (W / 2, 916), "✓ SWEEP COMPLETE · 37MB RECLAIMED · SURVIVORS COMPACTED",
              MONOB(10), alpha(GREEN, a * ct), sp=1, anchor="mm")


def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)
    intro = ease(fr / 14)
    diag = ease((fr - 8) / 18)
    a = diag
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 192), "UNREACHABLE OBJECTS  vs  LIVE ROOT GRAPH",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    tw1 = d.textlength("GARBAGE ", font=SANSB(42))
    tw2 = d.textlength("COLLECTION", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 228), "GARBAGE ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 228), "COLLECTION", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "how tracing GC finds dead memory and makes the heap reusable",
           font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")
    if diag <= .01:
        return base

    if beat3:
        pause = f"{int(lerp(180, 12, ease((fr - 180) / 65)))}ms"
        used = f"{int(lerp(96, 38, ease((fr - 218) / 42)))}%"
        c1 = c2 = GREEN
    elif beat2:
        pause = f"{int(lerp(3, 180, ease((fr - 90) / 78)))}ms"
        used = f"{int(lerp(42, 96, ease((fr - 90) / 78)))}%"
        c1, c2 = RED, RED if fr > 125 else AMBER
    else:
        pause, used, c1, c2 = "3ms", "42%", TEAL, BLUE
    draw_telemetry_hud(d, "PAUSE P99", pause, "HEAP USED", used, a, m1_col=c1, m2_col=c2)

    draw_allocation_rail(d, fr, a)
    draw_roots(d, fr, a)
    draw_heap_shell(d, fr, a)
    draw_graph_edges(d, fr, a)
    draw_objects(d, fr, a)
    draw_collector(d, fr, a)

    if 90 <= fr < 136:
        ga = ease((fr - 90) / 6) * (1 - ease((fr - 126) / 10))
        track(d, (W / 2, 468), "⚠ ALLOCATION FAILURE · HEAP PRESSURE 96%",
              MONOB(11), alpha(RED, a * ga * pulse), sp=2, anchor="mm")

    draw_caption_pill(d, fr, CAPTIONS, a)
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "ROOTS → MARK → SWEEP → COMPACT → RESUME",
              MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "JVM  ·  .NET  ·  GO  ·  V8  ·  MANAGED HEAPS",
              MONO(10), alpha(DIM, o), sp=2, anchor="mm")
    return base


def render_and_save_frame(args):
    fr, out_dir = args
    finish(render(fr), fr).save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_garbage_collection"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, [(fr, out_dir) for fr in frames]))
    print(f"Rendered Garbage Collection frames: {len(frames)}")
