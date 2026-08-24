#!/usr/bin/env python3
"""
Flagship System Design Reel: React Under the Hood (Fiber Tree vs Real DOM)
Visual Apparatus: A hexagonal fiber component tree (the in-memory virtual tree)
fed by a setState pill, reconciled against a concurrent-scheduler governor wheel,
with only the diff painted onto a real DOM browser screen.
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
    ease, alpha, lerp, track, finish, screen, draw_caption_pill, draw_telemetry_hud,
)

CAPTIONS = [
    (0,   "every setState rebuilds a virtual tree in memory — not the DOM."),
    (60,  "only the 1 changed node is committed to the real browser DOM."),
    (124, "a root update forces 10,000 fibers to re-render in one sync pass."),
    (188, "React 18 time-slices the work: 5ms, yield, paint, repeat."),
    (250, "frame budget holds at 16.6ms · 60fps · DOM touched exactly once."),
]

# Fiber component tree: (label, cx, cy, radius, pop_start_frame)
NODES = [
    ("App",    250, 515, 28, 12),
    ("Header", 145, 608, 24, 18),
    ("Content",355, 608, 24, 18),
    ("Logo",    95, 690, 20, 26),
    ("Nav",    200, 690, 20, 26),
    ("Card",   305, 690, 20, 26),
    ("List",   408, 690, 20, 26),
]
THREADS = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]

# Commit orbs: (start_fr, end_fr, from, mid, screen)
HOPS = [
    (68, 86,  (305, 710), (470, 688), (535, 602)),   # beat1: Card -> DOM
    (232, 258, (355, 632), (470, 700), (535, 602)),  # beat3: Content -> DOM
]


def fiber_cell(d, cx, cy, r, label, col, a, lw=2, fill=(12, 16, 24)):
    if a <= 0.01:
        return
    pts = []
    for k in range(6):
        ang = -math.pi / 2 + k * math.pi / 3
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=alpha(col, a), width=lw, joint="curve")
    d.text((cx, cy), label, font=MONOB(9), fill=alpha(WHITE, a), anchor="mm")
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=alpha(col, a))


def thread(d, p0, p1, col, a, w=1):
    mx = (p0[0] + p1[0]) / 2
    my = (p0[1] + p1[1]) / 2 + 16
    pts = []
    for i in range(15):
        t = i / 15
        qx = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * mx + t ** 2 * p1[0]
        qy = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * my + t ** 2 * p1[1]
        pts.append((qx, qy))
    d.line(pts, fill=alpha(col, a), width=w, joint="curve")


def draw_setstate_pill(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    if beat2:
        col, ca = RED, a * pulse
        txt1, txt2 = "setState at ROOT <App/>", "one giant synchronous pass"
    elif beat3:
        col, ca = GREEN, a
        txt1, txt2 = "setState at ROOT", "sliced into 5ms chunks"
    else:
        col, ca = BLUE, a
        txt1, txt2 = "onClick → setCount(1)", "state change inside <Card/>"
    d.rounded_rectangle([110, 420, 610, 462], radius=10, fill=(12, 16, 24),
                        outline=alpha(col, ca * 0.85), width=2)
    d.ellipse([124, 430, 138, 444], fill=alpha(col, ca))
    d.text((150, 435), txt1, font=MONOB(12), fill=alpha(WHITE, a), anchor="lm")
    d.text((150, 452), txt2, font=SANS(10), fill=alpha(col, a), anchor="lm")


def draw_tree(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    card_changed = (not beat2) and (not beat3) and fr >= 55
    card_committed = beat3 and fr >= 205

    # threads first (under nodes)
    for pi, ci in THREADS:
        p0 = (NODES[pi][1], NODES[pi][2] + NODES[pi][3])
        p1 = (NODES[ci][1], NODES[ci][2] - NODES[ci][3])
        on_path = (pi == 0 and ci == 2) or (pi == 2 and ci == 5)
        if beat2:
            col, ta, w = RED, a * 0.45, 1
        elif on_path and (card_changed or card_committed):
            col, ta, w = TEAL, a * 0.9, 2
        else:
            col, ta, w = DIM, a * 0.75, 1
        thread(d, p0, p1, col, ta, w)

    for i, (lab, cx, cy, r, sf) in enumerate(NODES):
        na = a * ease((fr - sf) / 8)
        if na <= 0.01:
            continue
        if beat2:
            col, lw, ca = RED, 2, na * pulse
            fill = (int(alpha(RED_D, na * 0.35)[0]), int(alpha(RED_D, na * 0.35)[1]), int(alpha(RED_D, na * 0.35)[2]))
        else:
            col, lw, ca = WHITE, 2, na
            fill = (12, 16, 24)
            if i == 5 and card_changed:
                col, lw = TEAL, 3
            if i == 5 and card_committed:
                col, lw = GREEN, 3
        fiber_cell(d, cx, cy, r, lab, col, ca, lw, fill)


def draw_dom_screen(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    x0, x1, ytop, ybot = 480, 675, 465, 585
    col = RED if beat2 else (GREEN if beat3 else WHITE)
    screen(d, x0, x1, ytop, ybot, -10, alpha(col, a * 0.9), alpha(col, 0.3))

    # browser chrome + url bar
    d.rounded_rectangle([x0 + 16, ytop + 18, x1 - 16, ytop + 40], radius=6,
                        fill=(16, 20, 30), outline=alpha(DIM, a * 0.8), width=1)
    d.text((x0 + 26, ytop + 29), "app.dev", font=MONO(8), fill=alpha(MUTED, a), anchor="lm")

    # content view
    vx0, vy0, vx1, vy1 = x0 + 16, ytop + 48, x1 - 16, ybot - 18
    d.rectangle([vx0, vy0, vx1, vy1], fill=(12, 16, 24), outline=alpha(DIM, a * 0.7), width=1)
    cxc, cyc = (vx0 + vx1) / 2, (vy0 + vy1) / 2
    if beat2:
        ctxt, ccol = ("✗ FRAME MISSED" if int(fr / 6) % 2 == 0 else "…stuttering"), RED
    elif beat3 and fr >= 240:
        ctxt, ccol = "✓ 1 node painted", GREEN
    elif (not beat3) and fr >= 86:
        ctxt, ccol = "✓ <Card/> painted", GREEN
    else:
        ctxt, ccol = "<App /> · <Card/>", MUTED
    d.text((cxc, cyc), ctxt, font=MONOB(9), fill=alpha(ccol, a * (pulse if beat2 else 1.0)), anchor="mm")

    # paint flash ring on commit landing
    for hs, he, _, _, _ in HOPS:
        if he <= fr <= he + 18 and not beat2:
            ra = 1 - ease((fr - he) / 18)
            rr = 10 + (fr - he) * 1.6
            d.ellipse([x1 - rr, ybot - rr, x1 + rr, ybot + rr], outline=alpha(GREEN, a * ra), width=2)


def draw_frame_budget(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    x0, x1, y0 = 130, 590, 718
    if beat2:
        load, col = 1.0, RED
        num, note = "120ms", "BLOCKED — BROWSER CANNOT PAINT"
    elif beat3:
        load, col = 0.34 + 0.08 * math.sin(fr * 0.6), GREEN
        num, note = "16.6ms", "5ms SLICE + YIELD"
    else:
        load, col = 0.30, TEAL
        num, note = "16.0ms", "RENDER <Card/> · 1 DOM MUTATION"
    d.text((x0, y0), note, font=SANS(10), fill=alpha(col, a), anchor="lm")
    track(d, (x0, y0 + 16), "MAIN THREAD", MONOB(10), alpha(MUTED, a), sp=2)
    d.text((x1, y0 + 16), num, font=MONOB(13), fill=alpha(col, a), anchor="rm")
    d.rectangle([x0, y0 + 28, x1, y0 + 44], outline=alpha(DIM, a), width=1)
    d.rectangle([x0, y0 + 28, x0 + (x1 - x0) * min(load, 1.0), y0 + 44],
                fill=alpha(col, a * (0.9 if beat2 else 0.7)))
    d.line([(x0 + (x1 - x0) * 0.7, y0 + 25), (x0 + (x1 - x0) * 0.7, y0 + 47)],
           fill=alpha(WHITE, a * 0.5), width=1)
    d.text((x0 + (x1 - x0) * 0.7 + 3, y0 + 25), "16ms budget", font=MONO(7),
           fill=alpha(MUTED, a * 0.7), anchor="lm")


def governor_wheel(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    cx, cy, R = 390, 845, 64
    col = GREEN if beat3 else (RED if beat2 else TEAL)
    if beat2:
        rot = 0.6
    elif beat3:
        rot = 0.6 + (fr - 180) * 0.35
    else:
        rot = fr * 0.08

    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=alpha(col, a * 0.6), width=2)
    d.ellipse([cx - R - 5, cy - R - 5, cx + R + 5, cy + R + 5], outline=alpha(col, a * 0.25), width=1)
    in_work = beat3 and (fr % 20) < 6
    for k in range(12):
        ang = rot + k * math.pi / 6
        r0, r1 = R - 13, R - 3
        x0 = cx + r0 * math.cos(ang); y0 = cy + r0 * math.sin(ang)
        x1 = cx + r1 * math.cos(ang); y1 = cy + r1 * math.sin(ang)
        tc = RED if in_work else col
        d.line([(x0, y0), (x1, y1)], fill=alpha(tc, a * 0.9), width=2)

    # time-slice arc
    if beat3:
        if in_work:
            d.arc([cx - R + 6, cy - R + 6, cx + R - 6, cy + R - 6],
                  rot * 57.3, rot * 57.3 + 90, fill=alpha(RED, a * 0.55), width=7)
        else:
            d.arc([cx - R + 6, cy - R + 6, cx + R - 6, cy + R - 6],
                  rot * 57.3, rot * 57.3 + 70, fill=alpha(GREEN, a * 0.35), width=4)
    elif beat2:
        d.arc([cx - R + 6, cy - R + 6, cx + R - 6, cy + R - 6],
              0, 359, fill=alpha(RED, a * 0.22 * (0.5 + 0.5 * math.sin(fr * 0.45))), width=6)

    ax, ay = cx + (R - 10) * math.cos(rot), cy + (R - 10) * math.sin(rot)
    d.line([(cx, cy), (ax, ay)], fill=alpha(col, a * 0.9), width=3)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], outline=alpha(col, a), width=2)
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=alpha(col, a))

    lab = "CONCURRENT · 5ms SLICES" if beat3 else ("SCHEDULER · JAMMED" if beat2 else "SCHEDULER · WORK LOOP")
    track(d, (cx, cy + R + 18), lab, MONO(9), alpha(MUTED, a), sp=1, anchor="mm")


def draw_commit_orb(d, fr, a):
    for hs, he, p0, pm, p1 in HOPS:
        if fr < hs:
            break
        ht = ease((fr - hs) / (he - hs))
        d0 = math.hypot(pm[0] - p0[0], pm[1] - p0[1])
        d1 = math.hypot(p1[0] - pm[0], p1[1] - pm[1])
        tot = d0 + d1
        dist = ht * tot
        if dist <= d0:
            t = dist / max(d0, 1e-6)
            ox, oy = lerp(p0[0], pm[0], t), lerp(p0[1], pm[1], t)
        else:
            t = (dist - d0) / max(d1, 1e-6)
            ox, oy = lerp(pm[0], p1[0], t), lerp(pm[1], p1[1], t)
        if ht < 1.0:
            d.line([p0, (ox, oy)], fill=alpha(GREEN, a * 0.5), width=2)
            d.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], fill=alpha(GREEN, a))
            d.ellipse([ox - 9, oy - 9, ox + 9, oy + 9], outline=alpha(GREEN, a * 0.5), width=1)
        elif hs == 232:
            for (pa, pb) in ((p0, pm), (pm, p1)):
                d.line([pa, pb], fill=alpha(GREEN, a * 0.9), width=2)
            ang = math.atan2(p1[1] - pm[1], p1[0] - pm[0])
            for da in (2.55, -2.55):
                d.line([p1, (p1[0] - 10 * math.cos(ang + da), p1[1] - 10 * math.sin(ang + da))],
                       fill=alpha(GREEN, a * 0.9), width=2)


def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    # ---- Header (flagship grammar)
    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 192), "VIRTUAL TREE (IN-MEMORY)  vs  REAL DOM (BROWSER)",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    tw1 = d.textlength("REACT ", font=SANSB(40))
    tw2 = d.textlength("UNDER THE HOOD", font=SANSB(40))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 228), "REACT ", font=SANSB(40), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 228), "UNDER THE HOOD", font=SANSB(40), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "how a virtual tree diff gets painted to the real DOM in 16ms",
           font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")

    if diag <= 0.01:
        return base

    # ---- Telemetry HUD
    if beat3:
        lat, latc, fps, fpsc = "16.6ms", GREEN, "60fps", GREEN
    elif beat2:
        lat, latc = f"{int(lerp(18, 120, ease((fr - 90) / 85)))}ms", RED
        fps, fpsc = f"{int(lerp(58, 4, ease((fr - 90) / 85)))}fps", RED
    else:
        lat, latc, fps, fpsc = "16.0ms", TEAL, "60fps", BLUE
    draw_telemetry_hud(d, "FRAME TIME", lat, "FRAME RATE", fps, a, m1_col=latc, m2_col=fpsc)

    # ---- Status line
    if beat3:
        st, stc = "RENDER: CONCURRENT · INTERRUPTIBLE · SLICED", GREEN
    elif beat2:
        st, stc = "RENDER: SYNC FULL-TREE RE-RENDER — MAIN THREAD BLOCKED", RED
    else:
        st, stc = "RENDER: <Card/> ONLY · DIFF ▸ 1 DOM MUTATION", TEAL
    track(d, (W / 2, 390), st, MONOB(10), alpha(stc, a * (pulse if beat2 else 1.0)), sp=1, anchor="mm")

    # ---- Stage
    draw_setstate_pill(d, fr, a)
    draw_tree(d, fr, a)
    draw_dom_screen(d, fr, a)
    draw_commit_orb(d, fr, a)
    draw_frame_budget(d, fr, a)
    governor_wheel(d, fr, a)

    # ---- Beat 2 alarm tag
    if 90 <= fr <= 140:
        ga = ease((fr - 90) / 5) * (1 - ease((fr - 128) / 12))
        track(d, (W / 2, 472), "⚠ ROOT UPDATE → RE-RENDER ALL 10,000 FIBERS",
              MONOB(11), alpha(RED, a * ga * pulse), sp=2, anchor="mm")

    # ---- Beat 2 timeout stamp
    if 168 <= fr <= 196:
        so = ease((fr - 168) / 6) * (1 - ease((fr - 188) / 8))
        track(d, (W / 2, 940), "✗ MAIN THREAD BLOCKED — 120ms JANK",
              MONOB(14), alpha(RED, a * so * pulse), sp=2, anchor="mm")

    # ---- Beat 3 takeaway
    if fr >= 200:
        if fr >= 258:
            track(d, (W / 2, 944), "✓ 16.6ms FRAME · 60fps · 1 DOM MUTATION",
                  MONOB(11), alpha(GREEN, a * ease((fr - 258) / 20)), sp=1, anchor="mm")
        else:
            track(d, (W / 2, 944), "SLICING: WORK ▸ YIELD ▸ PAINT",
                  MONOB(11), alpha(TEAL, a * ease((fr - 200) / 10)), sp=1, anchor="mm")

    # ---- Caption pill + outro footer
    draw_caption_pill(d, fr, CAPTIONS, a)
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "FIBER · RECONCILE · TIME SLICE · INTERRUPTIBLE RENDER",
              MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "REACT 18 · CONCURRENT MODE · VIRTUAL DOM · COMMIT PHASE",
              MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base


def render_and_save_frame(args):
    fr, out_dir = args
    img = finish(render(fr), fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_react_under_hood"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered React Under the Hood frames: {len(frames)}")