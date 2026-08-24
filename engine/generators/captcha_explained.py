#!/usr/bin/env python3
"""
Flagship System Design Reel: How CAPTCHA Works
Visual apparatus: split human-vs-bot checkbox simulator feeding a mechanical
risk-scoring rotor with PASS, CHALLENGE, and BLOCK gates.
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
    (0,   "the checkbox starts a risk check — it is not the whole test."),
    (48,  "a human pauses, corrects the cursor, then clicks."),
    (94,  "a bot jumps straight to the box in 8ms — then repeats."),
    (142, "machine-like timing plus request context raises the risk."),
    (188, "low risk passes; uncertain traffic receives a challenge."),
    (250, "CAPTCHA raises automation cost — one click proves nothing."),
]

HUMAN_PATH = [
    (292, 492), (277, 512), (252, 507), (232, 526), (207, 521),
    (185, 542), (164, 537), (142, 558), (106, 576),
]
BOT_PATH = [(615, 492), (420, 576)]


def point_on_polyline(points, progress):
    progress = max(0.0, min(1.0, progress))
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    total = sum(lengths)
    target, walked = progress * total, 0.0
    for i, length in enumerate(lengths):
        if target <= walked + length or i == len(lengths) - 1:
            t = 0 if length == 0 else (target - walked) / length
            a, b = points[i], points[i + 1]
            return (lerp(a[0], b[0], t), lerp(a[1], b[1], t)), i, t
        walked += length
    return points[-1], len(points) - 2, 1.0


def partial_polyline(points, progress):
    pos, seg, _ = point_on_polyline(points, progress)
    return points[:seg + 1] + [pos]


def draw_cursor(d, x, y, col, a, scale=1.0):
    pts = [
        (x, y), (x, y + 28 * scale), (x + 7 * scale, y + 21 * scale),
        (x + 13 * scale, y + 34 * scale), (x + 20 * scale, y + 30 * scale),
        (x + 14 * scale, y + 18 * scale), (x + 25 * scale, y + 18 * scale),
    ]
    d.polygon(pts, fill=alpha(BG, a), outline=alpha(col, a))
    d.line(pts + [pts[0]], fill=alpha(col, a), width=2)


def draw_actor(d, cx, cy, kind, col, a):
    if kind == "human":
        d.ellipse([cx - 12, cy - 20, cx + 12, cy + 4], outline=alpha(col, a), width=2)
        d.arc([cx - 24, cy - 1, cx + 24, cy + 38], 180, 360, fill=alpha(col, a), width=2)
        d.ellipse([cx - 5, cy - 10, cx - 2, cy - 7], fill=alpha(col, a))
        d.ellipse([cx + 3, cy - 10, cx + 6, cy - 7], fill=alpha(col, a))
    else:
        d.rounded_rectangle([cx - 22, cy - 19, cx + 22, cy + 17], radius=9,
                            fill=(10, 14, 21), outline=alpha(col, a), width=2)
        d.line([(cx, cy - 19), (cx, cy - 29)], fill=alpha(col, a), width=2)
        d.ellipse([cx - 4, cy - 34, cx + 4, cy - 26], fill=alpha(col, a))
        d.ellipse([cx - 11, cy - 7, cx - 5, cy - 1], fill=alpha(col, a))
        d.ellipse([cx + 5, cy - 7, cx + 11, cy - 1], fill=alpha(col, a))
        d.line([(cx - 10, cy + 8), (cx + 10, cy + 8)], fill=alpha(col, a), width=2)


def draw_check_mark(d, x, y, col, a):
    d.line([(x - 9, y), (x - 2, y + 8), (x + 12, y - 10)],
           fill=alpha(col, a), width=4, joint="curve")


def draw_checkbox_card(d, bounds, checked, col, a, flagged=False):
    x0, y0, x1, y1 = bounds
    d.rounded_rectangle([x0 + 3, y0 + 5, x1 + 3, y1 + 5], radius=10, fill=(5, 7, 11))
    d.rounded_rectangle(bounds, radius=10, fill=(14, 18, 27), outline=alpha(col, a * .65), width=2)
    bx0, by0, bx1, by1 = x0 + 16, y0 + 16, x0 + 48, y0 + 48
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=5, fill=(8, 11, 17),
                        outline=alpha(col, a), width=2)
    if checked:
        draw_check_mark(d, (bx0 + bx1) / 2, (by0 + by1) / 2, col, a)
    d.text((x0 + 62, y0 + 32), "I'M NOT A ROBOT", font=SANSB(12),
           fill=alpha(WHITE, a), anchor="lm")
    state = "CLICK CAPTURED" if checked else "WAITING FOR CLICK"
    d.text((x0 + 62, y0 + 49), state, font=MONO(8),
           fill=alpha(col if checked else MUTED, a * .9), anchor="lm")
    if flagged:
        d.rounded_rectangle([x1 - 70, y0 + 8, x1 - 10, y0 + 23], radius=7,
                            fill=(24, 9, 14), outline=alpha(RED, a))
        d.text((x1 - 40, y0 + 15), "FLAGGED", font=MONOB(7), fill=alpha(RED, a), anchor="mm")


def draw_timing_strip(d, x0, x1, y, values, col, a, uniform=False):
    d.line([(x0, y), (x1, y)], fill=alpha(DIM, a), width=1)
    span = x1 - x0
    for i in range(9):
        if uniform:
            px = x0 + 18 + i * ((span - 36) / 8)
        else:
            offsets = [0.04, .16, .22, .38, .43, .62, .72, .79, .96]
            px = x0 + offsets[i] * span
        h = 4 + (i % 3) * 3
        d.line([(px, y - h), (px, y + h)], fill=alpha(col, a), width=2)
    d.text(((x0 + x1) / 2, y + 18), values, font=MONO(8), fill=alpha(col, a), anchor="mm")


def draw_simulator(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * .48)
    x0, y0, x1, y1 = 48, 420, 672, 686
    d.rounded_rectangle([x0 + 4, y0 + 6, x1 + 4, y1 + 6], radius=16, fill=(5, 7, 11))
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=(11, 15, 22),
                        outline=alpha(TEAL if beat3 else BLUE, a * .7), width=2)
    d.line([(x0, 454), (x1, 454)], fill=alpha(DIM, a), width=1)
    d.line([(360, 454), (360, y1)], fill=alpha(DIM, a), width=1)
    for i, c in enumerate((RED, AMBER, GREEN)):
        d.ellipse([64 + i * 16, 435, 71 + i * 16, 442], fill=alpha(c, a * .85))
    track(d, (W / 2, 437), "INTERACTION SIMULATOR", MONOB(9), alpha(MUTED, a), sp=2, anchor="mm")

    human_dim = .5 if beat2 and not beat3 else 1.0
    bot_dim = .45 if not beat2 else 1.0
    draw_actor(d, 92, 502, "human", TEAL, a * human_dim)
    d.text((128, 486), "HUMAN SESSION", font=MONOB(11), fill=alpha(TEAL, a * human_dim), anchor="lm")
    d.text((128, 506), "pause · correction · click", font=SANS(9), fill=alpha(MUTED, a * human_dim), anchor="lm")

    draw_actor(d, 410, 502, "bot", RED, a * bot_dim)
    d.text((448, 486), "BOT SCRIPT", font=MONOB(11), fill=alpha(RED, a * bot_dim), anchor="lm")
    d.text((448, 506), "target → click() → repeat", font=SANS(9), fill=alpha(MUTED, a * bot_dim), anchor="lm")

    human_clicked = fr >= 72
    bot_clicked = fr >= 102
    draw_checkbox_card(d, (74, 544, 332, 610), human_clicked, GREEN if human_clicked else TEAL,
                       a * human_dim)
    draw_checkbox_card(d, (388, 544, 646, 610), bot_clicked, RED if bot_clicked else AMBER,
                       a * bot_dim, flagged=fr >= 124)

    hp = ease((fr - 18) / 54)
    if fr >= 18:
        htrail = partial_polyline(HUMAN_PATH, hp)
        d.line(htrail, fill=alpha(TEAL, a * human_dim * .45), width=2, joint="curve")
        hx, hy = htrail[-1]
        draw_cursor(d, hx, hy, WHITE, a * human_dim, .55)
        if 69 <= fr <= 82:
            rr = 8 + (fr - 69) * 1.2
            d.ellipse([106 - rr, 576 - rr, 106 + rr, 576 + rr],
                      outline=alpha(GREEN, a * (1 - ease((fr - 69) / 13))), width=2)

    if fr >= 90:
        bp = ease((fr - 90) / 12)
        btrail = partial_polyline(BOT_PATH, bp)
        d.line(btrail, fill=alpha(RED, a * .7), width=2)
        bx, by = btrail[-1]
        draw_cursor(d, bx, by, WHITE, a, .55)
        if 99 <= fr <= 150:
            for k in range(3):
                local = (fr - 102 - k * 13) / 9
                if 0 <= local <= 1:
                    rr = 7 + 24 * ease(local)
                    d.ellipse([420 - rr, 576 - rr, 420 + rr, 576 + rr],
                              outline=alpha(RED, a * (1 - ease(local)) * pulse), width=2)

    draw_timing_strip(d, 78, 328, 640, "643ms · 812ms · 704ms", TEAL, a * human_dim, uniform=False)
    draw_timing_strip(d, 392, 642, 640, "8ms · 8ms · 8ms", RED, a * bot_dim, uniform=True)


def draw_input_chip(d, y, title, value, col, a):
    d.rounded_rectangle([54, y - 20, 242, y + 20], radius=9, fill=(12, 16, 24),
                        outline=alpha(col, a * .65), width=1)
    d.ellipse([66, y - 6, 78, y + 6], fill=alpha(col, a))
    d.text((88, y - 6), title, font=MONOB(8), fill=alpha(MUTED, a), anchor="lm")
    d.text((88, y + 8), value, font=MONOB(9), fill=alpha(col, a), anchor="lm")
    d.line([(242, y), (292, y)], fill=alpha(col, a * .75), width=2)
    for px in (252, 268, 284):
        d.ellipse([px - 2, y - 2, px + 2, y + 2], fill=alpha(col, a * .65))


def draw_gate(d, y, label, note, col, active, a):
    strength = 1.0 if active else .28
    d.line([(428, y), (476, y)], fill=alpha(col, a * strength), width=2)
    d.polygon([(476, y), (486, y - 7), (486, y + 7)], fill=alpha(col, a * strength))
    d.rounded_rectangle([486, y - 21, 662, y + 21], radius=9, fill=(11, 15, 22),
                        outline=alpha(col, a * strength), width=2 if active else 1)
    d.ellipse([499, y - 6, 511, y + 6], fill=alpha(col, a * strength))
    d.text((522, y - 6), label, font=MONOB(9), fill=alpha(col, a * strength), anchor="lm")
    d.text((522, y + 9), note, font=MONO(7), fill=alpha(MUTED, a * strength), anchor="lm")


def draw_risk_engine(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * .45)
    if beat3:
        risk = .42
        current_col = TEAL
        values = [("CURSOR PATH", "behavior signal"), ("CLICK TIMING", "cadence signal"),
                  ("REQUEST CONTEXT", "browser + network")]
    elif beat2:
        risk = lerp(.12, .78, ease((fr - 90) / 72))
        current_col = RED if risk >= .65 else AMBER
        values = [("CURSOR PATH", "perfect straight line"), ("CLICK TIMING", "8ms × repeated"),
                  ("REQUEST CONTEXT", "burst traffic")]
    else:
        risk = lerp(.48, .12, ease((fr - 22) / 55))
        current_col = GREEN if risk < .3 else TEAL
        values = [("CURSOR PATH", "curved + corrected"), ("CLICK TIMING", "natural pause"),
                  ("REQUEST CONTEXT", "normal request")]

    ys = (742, 811, 880)
    for y, (title, value) in zip(ys, values):
        draw_input_chip(d, y, title, value, current_col, a)

    cx, cy, r = 360, 811, 67
    # Mechanical rotor teeth and risk arc.
    for k in range(16):
        ang = 2 * math.pi * k / 16 + fr * .002
        x0, y0 = cx + (r + 2) * math.cos(ang), cy + (r + 2) * math.sin(ang)
        x1, y1 = cx + (r + 9) * math.cos(ang), cy + (r + 9) * math.sin(ang)
        d.line([(x0, y0), (x1, y1)], fill=alpha(current_col, a * .45), width=3)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 14, 21),
              outline=alpha(current_col, a * (.7 + .3 * pulse)), width=3)
    d.arc([cx - 51, cy - 51, cx + 51, cy + 51], 200, 246, fill=alpha(GREEN, a), width=6)
    d.arc([cx - 51, cy - 51, cx + 51, cy + 51], 247, 294, fill=alpha(AMBER, a), width=6)
    d.arc([cx - 51, cy - 51, cx + 51, cy + 51], 295, 340, fill=alpha(RED, a), width=6)
    needle = math.radians(200 + 140 * risk)
    nx, ny = cx + 42 * math.cos(needle), cy + 42 * math.sin(needle)
    d.line([(cx, cy), (nx, ny)], fill=alpha(WHITE, a), width=3)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=alpha(current_col, a))
    d.text((cx, cy + 18), "RISK ENGINE", font=MONOB(8), fill=alpha(MUTED, a), anchor="mm")
    readout = "POLICY" if beat3 else f"{int(risk * 100)}%"
    d.text((cx, cy + 37), readout, font=MONOB(15), fill=alpha(current_col, a), anchor="mm")

    if beat3:
        pass_on, challenge_on, block_on = True, True, False
    elif beat2:
        pass_on, challenge_on, block_on = False, risk >= .55, False
    else:
        pass_on, challenge_on, block_on = risk < .3, False, False
    draw_gate(d, 742, "PASS", "signed server token", GREEN, pass_on, a)
    draw_gate(d, 811, "CHALLENGE", "image / interaction", AMBER, challenge_on, a)
    draw_gate(d, 880, "BLOCK", "deny or rate-limit", RED, block_on, a)

    if beat3:
        # Two session tokens leave the same risk engine through different gates.
        pt = ease((fr - 188) / 42)
        bx = lerp(428, 622, pt)
        d.ellipse([bx - 6, 736, bx + 6, 748], fill=alpha(GREEN, a))
        d.text((bx, 726), "HUMAN", font=MONOB(7), fill=alpha(GREEN, a), anchor="mm")
        bt = ease((fr - 207) / 42)
        rx = lerp(428, 622, bt)
        d.ellipse([rx - 6, 805, rx + 6, 817], fill=alpha(AMBER, a))
        d.text((rx, 795), "BOT?", font=MONOB(7), fill=alpha(AMBER, a), anchor="mm")

    track(d, (W / 2, 944), "THE CHECKBOX IS ONE INPUT — THE SERVER MAKES THE DECISION",
          MONOB(9), alpha(GREEN if beat3 else current_col, a), sp=1, anchor="mm")


def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)
    intro = ease(fr / 14)
    diag = ease((fr - 8) / 18)
    a = diag
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * .45)

    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 192), "HUMAN INTERACTION  vs  BOT AUTOMATION",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    tw1 = d.textlength("CAPTCHA ", font=SANSB(42))
    tw2 = d.textlength("DECISION", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 228), "CAPTCHA ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 228), "DECISION", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "how one checkbox becomes a server-side automation risk test",
           font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")

    if diag <= .01:
        return base

    if beat3:
        m1v, m1c, m2v, m2c = "PASS TOKEN", GREEN, "CHALLENGE", AMBER
        status, status_col = "POLICY: LOW RISK PASSES · UNCERTAIN TRAFFIC GETS A PUZZLE", GREEN
    elif beat2:
        risk = int(lerp(12, 78, ease((fr - 90) / 72)))
        m1v, m1c, m2v, m2c = "8ms", RED, f"{risk}% FLAGGED", RED
        status, status_col = "BOT PATTERN: INSTANT + REPEATED + MACHINE-LIKE", RED
    else:
        click_ms = int(lerp(0, 812, ease((fr - 18) / 54)))
        risk = int(lerp(48, 12, ease((fr - 22) / 55)))
        m1v, m1c, m2v, m2c = f"{click_ms}ms", TEAL, f"{risk}% LOW", GREEN if risk < 30 else TEAL
        status, status_col = "OBSERVE: POINTER MOTION + TIMING + REQUEST CONTEXT", MUTED
    draw_telemetry_hud(d, "CLICK TIME", m1v, "SIMULATED RISK", m2v, a,
                       m1_col=m1c, m2_col=m2c)
    track(d, (W / 2, 390), status, MONOB(9),
          alpha(status_col, a * (pulse if beat2 else 1)), sp=1, anchor="mm")

    draw_simulator(d, fr, a)
    draw_risk_engine(d, fr, a)
    draw_caption_pill(d, fr, CAPTIONS, a)

    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "CHECKBOX IS NOT PROOF · CAPTCHA = RISK + CHALLENGE",
              MONOB(11), alpha(TEAL, o), sp=2, anchor="mm")
        track(d, (W / 2, 1112), "BEHAVIOR · BROWSER SIGNALS · RATE LIMITS · SERVER TOKEN",
              MONO(9), alpha(DIM, o), sp=2, anchor="mm")

    return base


def render_and_save_frame(args):
    fr, out_dir = args
    finish(render(fr), fr).save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_captcha_explained"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, [(fr, out_dir) for fr in frames]))
    print(f"Rendered CAPTCHA Explained frames: {len(frames)}")
