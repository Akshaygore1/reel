#!/usr/bin/env python3
"""
Simple Garbage Collection Reel.
Visual apparatus: a glass heap jar holds object bubbles; reference strings show
what the app still uses, then a mechanical GC broom sweeps disconnected bubbles.
720x1280 @ 30fps, 10s (300 frames).
"""
import os, sys, math
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from blueprint_engine import (
    W, H, FPS, DUR, NF, BG, AMBER, TEAL, BLUE, WHITE, MUTED, DIM, RED,
    GREEN, GREEN_D, MONO, MONOB, SANS, SANSB, ease, alpha, lerp, track,
    finish, draw_caption_pill, draw_telemetry_hud,
)

CAPTIONS = [
    (0,   "your app creates objects and stores them in memory."),
    (60,  "a line means the app is still using that object."),
    (124, "no line? that object is garbage — but it still takes space."),
    (188, "the garbage collector finds objects nobody is using."),
    (250, "it removes them automatically and frees memory."),
]

HEAP = (74, 486, 646, 876)
POSITIONS = [
    (150, 548), (286, 536), (430, 552), (560, 540),
    (128, 650), (270, 634), (418, 660), (566, 640),
    (162, 758), (310, 744), (450, 766), (574, 748),
]
SIZES = [(78, 44), (92, 52), (72, 46), (82, 48), (88, 50), (70, 44),
         (96, 52), (74, 46), (84, 48), (90, 54), (72, 44), (82, 50)]
LIVE_AFTER = {0, 1, 4, 5, 8, 9}


def bubble_points(cx, cy, w, h):
    """Soft eight-sided object bubble with a tiny reference socket."""
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    c = 12
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
            (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def visible_count(fr):
    if fr < 90:
        return min(8, 2 + int(6 * ease((fr - 14) / 64)))
    return min(12, 8 + int(4 * ease((fr - 90) / 58)))


def draw_app_bar(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    col = GREEN if beat3 else (RED if beat2 else BLUE)
    label = "APP RUNNING AGAIN" if fr >= 248 else ("APP PAUSED" if beat2 else "YOUR APP")
    d.rounded_rectangle([236, 414, 484, 456], radius=21, fill=(12, 16, 24),
                        outline=alpha(col, a), width=2)
    d.ellipse([252, 430, 262, 440], fill=alpha(col, a))
    d.text((370, 435), label, font=MONOB(11), fill=alpha(col, a), anchor="mm")


def draw_reference_lines(d, fr, a):
    count = visible_count(fr)
    sweep_x = lerp(HEAP[0] + 16, HEAP[2] - 16, ease((fr - 186) / 56))
    for idx, (x, y) in enumerate(POSITIONS[:count]):
        connected = fr < 90 or idx in LIVE_AFTER
        if connected:
            col = GREEN if fr >= 180 else BLUE
            d.line([(360, 456), (x, y - SIZES[idx][1] / 2)], fill=alpha(col, a * .48), width=2)
            # small moving reference pulse
            p = (fr * .025 + idx * .13) % 1.0
            px, py = lerp(360, x, p), lerp(456, y - SIZES[idx][1] / 2, p)
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=alpha(col, a))
        elif fr < 180:
            # A broken string makes "unused" readable without terminology.
            bx, by = lerp(360, x, .55), lerp(456, y, .55)
            d.line([(x, y - SIZES[idx][1] / 2), (bx + 12, by + 10)], fill=alpha(RED, a * .6), width=1)
            d.line([(360, 456), (bx - 12, by - 10)], fill=alpha(RED, a * .35), width=1)
        elif x > sweep_x:
            d.line([(x, y - SIZES[idx][1] / 2), (x, y - 42)], fill=alpha(DIM, a * .25), width=1)


def draw_heap(d, fr, a):
    x0, y0, x1, y1 = HEAP
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = .55 + .45 * math.sin(fr * .45)
    col = GREEN if beat3 else (RED if beat2 else TEAL)
    ca = a * (pulse if beat2 else 1.0)
    d.rounded_rectangle([x0, y0, x1, y1], radius=28, fill=(10, 14, 20),
                        outline=alpha(col, ca), width=3)
    # Jar neck and simple fill ruler make the heap feel like a physical container.
    d.line([(266, y0), (266, y0 - 16), (454, y0 - 16), (454, y0)], fill=alpha(col, ca), width=2)
    d.text((360, y0 + 24), "MEMORY HEAP", font=MONOB(11), fill=alpha(col, ca), anchor="mm")
    for y in range(y0 + 62, y1 - 22, 52):
        d.line([(x0 + 12, y), (x0 + 25, y)], fill=alpha(DIM, a), width=1)
    d.text((x0 + 18, y1 - 18), "EMPTY", font=MONO(8), fill=alpha(DIM, a), anchor="lm")
    d.text((x1 - 18, y1 - 18), "FULL", font=MONO(8), fill=alpha(col, ca), anchor="rm")


def draw_bubbles(d, fr, a):
    count = visible_count(fr)
    sweep_x = lerp(HEAP[0] + 16, HEAP[2] - 16, ease((fr - 186) / 56))
    for idx, ((x, y), (w, h)) in enumerate(zip(POSITIONS[:count], SIZES[:count])):
        used = fr < 90 or idx in LIVE_AFTER
        born_at = 12 + idx * (7 if idx < 8 else 10)
        born = ease((fr - born_at) / 8)
        swept = fr >= 186 and not used and x <= sweep_x
        vanish = 1 - ease((sweep_x - x) / 42) if swept else 1.0
        if vanish <= .01:
            continue
        col = GREEN if fr >= 180 and used else (BLUE if used else RED)
        oa = a * born * vanish
        pts = bubble_points(x, y, w, h)
        d.polygon(pts, fill=alpha(col, oa * .12))
        d.line(pts + [pts[0]], fill=alpha(col, oa), width=2, joint="curve")
        d.ellipse([x + w * .25 - 4, y - 4, x + w * .25 + 4, y + 4], fill=alpha(col, oa))
        word = "USED" if used else "TRASH"
        d.text((x, y), word, font=MONOB(9), fill=alpha(WHITE, oa), anchor="mm")
        if swept:
            rr = 6 + 18 * (1 - vanish)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=alpha(RED, oa), width=1)


def draw_gc_broom(d, fr, a):
    if fr < 180:
        return
    t = ease((fr - 180) / 64)
    x = lerp(HEAP[0] + 18, HEAP[2] - 20, t)
    # Mechanical broom head and bristles; one action, immediately understandable.
    d.rounded_rectangle([x - 22, 512, x + 22, 830], radius=12, fill=alpha(GREEN_D, a * .85),
                        outline=alpha(GREEN, a), width=2)
    d.text((x, 536), "GC", font=MONOB(11), fill=alpha(WHITE, a), anchor="mm")
    for y in range(570, 826, 30):
        d.line([(x - 22, y), (x - 38, y + 9)], fill=alpha(GREEN, a * .8), width=2)
    d.polygon([(x - 10, 500), (x + 10, 500), (x, 486)], fill=alpha(GREEN, a))
    if fr >= 244:
        d.rounded_rectangle([492, 890, 632, 932], radius=20, fill=(12, 16, 24),
                            outline=alpha(GREEN, a), width=2)
        d.text((562, 911), "SPACE FREED ✓", font=MONOB(10), fill=alpha(GREEN, a), anchor="mm")


def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)
    intro = ease(fr / 14)
    a = ease((fr - 8) / 18)
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = .55 + .45 * math.sin(fr * .45)

    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 192), "USED OBJECTS  vs  UNUSED OBJECTS", MONOB(11),
          alpha(MUTED, intro), sp=2, anchor="mm")
    tw1 = d.textlength("GARBAGE ", font=SANSB(42))
    tw2 = d.textlength("COLLECTION", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 228), "GARBAGE ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 228), "COLLECTION", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "how your runtime automatically cleans unused memory",
           font=SANS(14), fill=alpha(BLUE, intro), anchor="mm")
    if a <= .01:
        return base

    if beat3:
        used, free, c1, c2 = "38%", "62%", GREEN, GREEN
        status, sc = "3. GC SWEEPS UNUSED OBJECTS AWAY", GREEN
    elif beat2:
        used = f"{int(lerp(58, 95, ease((fr - 90) / 80)))}%"
        free = f"{100 - int(lerp(58, 95, ease((fr - 90) / 80)))}%"
        c1, c2 = RED, AMBER
        status, sc = "2. UNUSED OBJECTS FILL THE HEAP", RED
    else:
        used, free, c1, c2 = "40%", "60%", TEAL, BLUE
        status, sc = "1. APP CREATES OBJECTS", BLUE
    draw_telemetry_hud(d, "HEAP USED", used, "FREE SPACE", free, a, m1_col=c1, m2_col=c2)
    track(d, (W / 2, 390), status, MONOB(10), alpha(sc, a * (pulse if beat2 else 1)), sp=2, anchor="mm")

    draw_app_bar(d, fr, a)
    draw_heap(d, fr, a)
    draw_reference_lines(d, fr, a)
    draw_bubbles(d, fr, a)
    draw_gc_broom(d, fr, a)

    if 108 <= fr <= 170:
        q = ease((fr - 108) / 8) * (1 - ease((fr - 162) / 8))
        track(d, (W / 2, 914), "NO REFERENCE = SAFE TO DELETE",
              MONOB(12), alpha(RED, a * q * pulse), sp=2, anchor="mm")
    elif fr >= 244:
        track(d, (W / 2, 950), "THE APP KEEPS RUNNING WITH MORE FREE MEMORY",
              MONOB(10), alpha(GREEN, a), sp=2, anchor="mm")

    draw_caption_pill(d, fr, CAPTIONS, a)
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "CREATE → USE → FORGET → CLEAN",
              MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "JAVA  ·  GO  ·  JAVASCRIPT  ·  .NET",
              MONO(10), alpha(DIM, o), sp=2, anchor="mm")
    return base


def render_and_save_frame(args):
    fr, out_dir = args
    finish(render(fr), fr).save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_garbage_collection_simple"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, [(fr, out_dir) for fr in frames]))
    print(f"Rendered Simple Garbage Collection frames: {len(frames)}")
