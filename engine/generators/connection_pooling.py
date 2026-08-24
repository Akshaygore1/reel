#!/usr/bin/env python3
"""
Flagship System Design Reel: Connection Pooling (Fresh-Handshake Factory vs Warm Pool Rack)
Visual Apparatus: a three-station robotic handshake gantry (TCP -> TLS -> AUTH)
builds a brand-new connection for every request until a x50 traffic spike blows
past Postgres max_connections; then a patch-panel pool rack of 20 warm
pre-authenticated plugs crystallizes — requests check a plug out, ride the trunk
cable to the database silo, and return it. Zero handshakes, 0.8ms checkouts.
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
    (0,   "every API request opens a fresh DB connection. at 800 req/s: fine."),
    (60,  "traffic spikes x50 — every request rebuilds TCP + TLS + auth from scratch."),
    (124, "1,847 connection attempts in 3s. Postgres max_connections = 100."),
    (188, "the fix: a pool of 20 warm, pre-authenticated connections."),
    (250, "checkout ▸ query ▸ return. 0.8ms. zero new handshakes."),
]

MAX_CONNS   = 100        # Postgres max_connections
POOL_SIZE   = 20         # warm pooled connections
ATTEMPTS_B2 = 1_847      # calibrated: on-screen counter hits exactly this at fr 178
CHECKOUTS   = 176_400    # calibrated: on-screen counter hits exactly this at fr 300

# ---- naive-world geometry (beats 1-2): the handshake factory
STATIONS = [  # cx, hex-cy, tag, sublabel
    (250, 604, "TCP",  "3-WAY HANDSHAKE"),
    (360, 604, "TLS",  "HELLO x2 RTT"),
    (470, 604, "AUTH", "PG CREDENTIALS"),
]
HEX_RX, HEX_RY = 44, 40
ORB_Y = 556                                        # request orbs travel above the hexes
INTAKE = [(70, 420), (70, 472), (168, 472), (168, 560), (206, 588)]
SILO_CX, SILO_YT, SILO_YB, SILO_RY = 590, 520, 655, 13   # database silo body span
PROC_SPAWNS = [18 + 14 * i for i in range(6)] + [92 + 12 * k for k in range(7)]

NAIVE_PHASES = [("in", 12), ("s1", 10), ("h1", 3), ("s2", 12), ("h2", 3),
                ("s3", 10), ("h3", 3), ("db", 5), ("q", 8), ("bye", 4)]

# ---- pooled-world geometry (beat 3): the warm pool rack
RACK = (84, 502, 416, 718)
BAY_W, BAY_H = 56, 36
BAYS = [(100 + 61 * c, 530 + 44 * r) for r in range(4) for c in range(5)]
TRUNK = ((RACK[2], 610), (522, 590))
INTAKE3 = [(70, 420), (70, 472), (140, 472), (140, 600)]
POOL_SPAWN0, POOL_EVERY = 184, 5

POOL_PHASES = [("in", 10), ("grab", 8), ("pop", 3), ("ride", 12), ("query", 8),
               ("back", 12), ("drop", 3), ("exit", 10)]


# ---------------------------------------------------------------- helpers
def poly_pos(pts, t):
    """Walk a polyline path by normalized arc length t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    segs, total = [], 0.0
    for i in range(len(pts) - 1):
        L = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        segs.append((pts[i], pts[i + 1], L))
        total += L
    dist = t * total
    for p0, p1, L in segs:
        if dist <= L:
            u = dist / L if L else 0.0
            return (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u))
        dist -= L
    return pts[-1]


def phase_at(spawn, fr, phases):
    """Return (phase_name, t_in_phase) for a request born at `spawn`, or None."""
    el = fr - spawn
    acc = 0
    for name, dur in phases:
        if el < acc + dur:
            return name, (el - acc) / dur
        acc += dur
    return None


def attempt_count(fr):
    """Fresh connections opened — calibrated to land on exactly 1,847 at fr 178."""
    if fr < 92:
        return 0 if fr < 18 else min(6, int((fr - 18) / 14) + 1)
    return 6 + int(1.841 * ease((fr - 92) / 86) * 1000)


def checkout_count(fr):
    """Pool checkouts — calibrated to land on exactly 176,400 at fr 300."""
    return int(176.4 * ease((fr - 182) / 118) * 1000)


def arrowhead(d, p, ang, col, s=7):
    for da in (2.55, -2.55):
        d.line([p, (p[0] - s * math.cos(ang + da), p[1] - s * math.sin(ang + da))],
               fill=col, width=2)


def lane_label(d, a):
    track(d, (84, 424), "REQUESTS ▸", MONO(8), alpha(MUTED, a), sp=1, anchor="lm")


# ---------------------------------------------------------------- naive world
def draw_intake(d, fa):
    if fa <= 0.01:
        return
    d.line(INTAKE, fill=alpha(BLUE, fa * 0.5), width=2, joint="curve")
    arrowhead(d, INTAKE[-1], math.atan2(588 - 560, 206 - 168), alpha(BLUE, fa * 0.7))


def naive_pos(name, t):
    s = [st[:2] for st in STATIONS]
    if name == "in":
        return poly_pos(INTAKE, ease(t))
    if name == "s1":
        return (s[0][0], ORB_Y)
    if name == "h1":
        return (lerp(s[0][0], s[1][0], t), ORB_Y - 10 * math.sin(t * math.pi))
    if name == "s2":
        return (s[1][0], ORB_Y)
    if name == "h2":
        return (lerp(s[1][0], s[2][0], t), ORB_Y - 10 * math.sin(t * math.pi))
    if name == "s3":
        return (s[2][0], ORB_Y)
    if name == "h3":
        return (lerp(s[2][0], 514, t), ORB_Y - 10 * math.sin(t * math.pi))
    if name == "db":
        return (lerp(514, 530, t), ORB_Y)
    return (538, ORB_Y)  # q / bye


def draw_factory(d, fr, fa):
    if fa <= 0.01:
        return
    beat2 = fr >= 90
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    ca = fa * (pulse if beat2 else 1.0)
    col = RED if beat2 else TEAL

    track(d, (W / 2, 528), "CONNECTION FACTORY · ONE NEW CONN PER REQUEST",
          MONO(10), alpha(col if beat2 else MUTED, ca), sp=2, anchor="mm")

    # which stations currently hold a request
    occ = set()
    for sp in PROC_SPAWNS:
        st = phase_at(sp, fr, NAIVE_PHASES)
        if st and st[0] in ("s1", "s2", "s3"):
            occ.add(int(st[0][1]) - 1)

    spin = 0.85 if beat2 else 0.30
    for k, (sx, sy, tag, sub) in enumerate(STATIONS):
        busy = k in occ
        pts = [(sx - HEX_RX, sy), (sx - HEX_RX / 2, sy - HEX_RY), (sx + HEX_RX / 2, sy - HEX_RY),
               (sx + HEX_RX, sy), (sx + HEX_RX / 2, sy + HEX_RY), (sx - HEX_RX / 2, sy + HEX_RY)]
        d.polygon(pts, fill=(12, 16, 24))
        if busy:
            d.polygon(pts, fill=alpha(col, ca * 0.12))
        d.line(pts + [pts[0]], fill=alpha(col if busy else WHITE, ca * (0.95 if busy else 0.5)),
               width=2, joint="curve")
        # docking notch where the request orb plugs in
        d.line([(sx - 9, sy - HEX_RY), (sx, sy - HEX_RY + 7)], fill=alpha(col, ca * 0.8), width=2)
        d.line([(sx + 9, sy - HEX_RY), (sx, sy - HEX_RY + 7)], fill=alpha(col, ca * 0.8), width=2)
        # spinning winder arm
        ang = fr * spin + k * 1.1
        acy = sy + 4
        for da in (0, math.pi):
            d.line([(sx, acy), (sx + 15 * math.cos(ang + da), acy + 15 * math.sin(ang + da))],
                   fill=alpha(col, ca * 0.85), width=2)
        d.ellipse([sx - 4, acy - 4, sx + 4, acy + 4], fill=alpha(col, ca))
        d.text((sx, sy - 20), tag, font=MONOB(12), fill=alpha(WHITE, ca), anchor="mm")
        d.text((sx, sy + 26), sub, font=MONO(7), fill=alpha(col, ca * 0.75), anchor="mm")
        if k < 2:
            nx = STATIONS[k + 1][0] - HEX_RX
            d.line([(sx + HEX_RX, sy), (nx, sy)], fill=alpha(DIM, fa * 0.8), width=1)
            arrowhead(d, (nx, sy), 0.0, alpha(DIM, fa * 0.9), s=5)

    note = ("FACTORY SATURATED · HANDSHAKES THRASHING" if beat2 else
            "EVERY REQUEST PAYS ~50ms OF SETUP BEFORE ITS 2ms QUERY")
    track(d, (W / 2, 660), note, MONO(9), alpha(RED if beat2 else MUTED, ca), sp=1, anchor="mm")


def draw_naive_orbs(d, fr, fa):
    if fa <= 0.01:
        return
    for sp in PROC_SPAWNS:
        st = phase_at(sp, fr, NAIVE_PHASES)
        if not st:
            continue
        name, t = st
        col = AMBER if sp >= 90 else BLUE
        oa = fa
        if name == "bye":
            oa *= 1 - t
        if name == "in":
            oa *= min(1.0, t * 3)
        x, y = naive_pos(name, t)
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=alpha(col, oa))
        d.ellipse([x - 10, y - 10, x + 10, y + 10], outline=alpha(col, oa * 0.4), width=1)


def draw_wedge(d, fr, fa):
    """Beat 2: requests stacking up with no free connection slot."""
    if fr < 92 or fa <= 0.01:
        return
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    qlen = int(30 * ease((fr - 92) / 70))
    for i in range(min(qlen, 30)):
        c, r = i % 2, i // 2
        x, y = 84 + 22 * c, 622 + 10.5 * r
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=alpha(RED, fa * pulse))
    track(d, (95, 786), "WAITING", MONO(8), alpha(RED, fa), sp=1, anchor="mm")


def draw_heap(d, fr, fa):
    """Beat 2: scrapped half-built handshakes piling up under the database."""
    if fr < 100 or fa <= 0.01:
        return
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    att = attempt_count(fr)
    n = min(24, max(0, att - MAX_CONNS))
    for i in range(n):
        r, c = i // 4, i % 4
        x, y = 516 + 38 * c, 722 + 13 * r
        tilt = -6 if (r + c) % 2 == 0 else 6
        d.line([(x - 12, y), (x + 12, y + tilt)], fill=alpha(RED_D if i % 2 else RED, fa * 0.9), width=3)
    track(d, (586, 800), f"SCRAPPED {max(0, att - MAX_CONNS):,}", MONO(8),
          alpha(RED, fa * pulse), sp=1, anchor="mm")


# ---------------------------------------------------------------- database silo
def draw_silo(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    col = GREEN if beat3 else (RED if beat2 else TEAL)
    ca = a * (pulse if beat2 else 1.0)
    x0, x1 = SILO_CX - 65, SILO_CX + 65

    # antenna
    d.line([(SILO_CX, SILO_YT - SILO_RY), (SILO_CX, SILO_YT - SILO_RY - 18)],
           fill=alpha(col, ca * 0.8), width=2)
    d.ellipse([SILO_CX - 3.5, SILO_YT - SILO_RY - 25, SILO_CX + 3.5, SILO_YT - SILO_RY - 18],
              fill=alpha(col, ca))

    # cylindrical body
    d.ellipse([x0, SILO_YB - 2 * SILO_RY, x1, SILO_YB], fill=(12, 16, 24),
              outline=alpha(col, ca * 0.7), width=1)
    d.rectangle([x0, SILO_YT, x1, SILO_YB - SILO_RY], fill=(12, 16, 24))
    d.line([(x0, SILO_YT), (x0, SILO_YB - SILO_RY)], fill=alpha(col, ca * 0.8), width=2)
    d.line([(x1, SILO_YT), (x1, SILO_YB - SILO_RY)], fill=alpha(col, ca * 0.8), width=2)
    d.ellipse([x0, SILO_YT - SILO_RY, x1, SILO_YT + SILO_RY], fill=(16, 22, 32),
              outline=alpha(col, ca), width=2)
    for gy in (555, 575):
        d.line([(x0 + 2, gy), (x1 - 2, gy)], fill=alpha(DIM, a * 0.6), width=1)
    d.text((SILO_CX, SILO_YT), "POSTGRES", font=MONOB(10), fill=alpha(WHITE, a), anchor="mm")

    # connection gauge
    if beat3:
        gtxt, fill, gcol = "POOL LINK · WARM", 1.0, GREEN
    else:
        g = min(MAX_CONNS, attempt_count(fr))
        gtxt = (f"MAX · REJECTING" if g >= MAX_CONNS else f"OPENED {g}/100")
        fill = g / MAX_CONNS
        gcol = RED if g >= MAX_CONNS else TEAL
    d.text((SILO_CX, 606), gtxt, font=MONO(8), fill=alpha(gcol, ca), anchor="mm")
    d.rectangle([x0 + 12, 614, x1 - 12, 626], outline=alpha(DIM, a), width=1)
    d.rectangle([x0 + 12, 614, x0 + 12 + (x1 - x0 - 24) * fill, 626], fill=alpha(gcol, ca * 0.85))
    note = "one trunk · 20 muxed conns" if beat3 else "max_connections = 100"
    d.text((SILO_CX, 640), note, font=MONO(7),
           fill=alpha(TEAL_D if beat3 else DIM, a), anchor="mm")


# ---------------------------------------------------------------- pooled world
def draw_plug(d, cx, cy, col, a):
    d.rounded_rectangle([cx - 16, cy - 6, cx + 16, cy + 6], radius=3,
                        fill=(10, 14, 20), outline=alpha(col, a), width=2)
    for px in (-8, 0, 8):
        d.line([(cx + px, cy + 6), (cx + px, cy + 12)], fill=alpha(col, a * 0.9), width=2)


def pool_pos(name, t, ph):
    if name == "in":
        return poly_pos(INTAKE3, ease(t))
    if name == "grab":
        return (lerp(140, ph[0] - 34, ease(t)), lerp(600, ph[1], ease(t)))
    if name == "pop" or name == "drop":
        return ph
    if name == "ride":
        return (lerp(ph[0], 524, t), lerp(ph[1], 560, t))
    if name == "query":
        return (538, 560)
    if name == "back":
        return (lerp(524, ph[0], t), lerp(560, ph[1], t))
    return poly_pos(INTAKE3, 1 - ease(t))  # exit


def draw_pool(d, fr, pa):
    if pa <= 0.01:
        return

    # intake lane toward the rack
    d.line(INTAKE3, fill=alpha(BLUE, pa * 0.5), width=2, joint="curve")
    arrowhead(d, INTAKE3[-1], 0.0, alpha(BLUE, pa * 0.7))

    # trunk cable rack -> database (glow pass + flowing pulses)
    (tx0, ty0), (tx1, ty1) = TRUNK
    d.line([TRUNK[0], TRUNK[1]], fill=alpha(TEAL, pa * 0.25), width=10)
    d.line([TRUNK[0], TRUNK[1]], fill=alpha(TEAL, pa * 0.5), width=5)
    for k in range(5):
        t = (fr * 0.045 + k / 5.0) % 1.0
        px, py = lerp(tx0, tx1, t), lerp(ty0, ty1, t)
        d.ellipse([px - 2.5, py - 2.5, px + 2.5, py + 2.5], fill=alpha(GREEN, pa))

    # rack panel
    d.rounded_rectangle(list(RACK), radius=10, fill=(12, 16, 24),
                        outline=alpha(TEAL, pa * 0.9), width=2)
    track(d, ((RACK[0] + RACK[2]) / 2, 516), "WARM POOL · 20 PRE-AUTH CONNS",
          MONO(10), alpha(TEAL, pa), sp=2, anchor="mm")

    # resolve which bay each live request holds + plug lift
    bay_lift = [0.0] * POOL_SIZE
    orb_draws = []
    for j in range(40):
        sp = POOL_SPAWN0 + POOL_EVERY * j
        st = phase_at(sp, fr, POOL_PHASES)
        if not st:
            continue
        name, t = st
        b = j % POOL_SIZE
        bx, by = BAYS[b]
        ph = (bx + BAY_W / 2, by + 20)
        if name == "pop":
            bay_lift[b] = max(bay_lift[b], 14 * t)
        elif name in ("ride", "query", "back"):
            bay_lift[b] = 14.0
        elif name == "drop":
            bay_lift[b] = max(bay_lift[b], 14 * (1 - t))
        orb_draws.append((name, t, b, ph))

    for b, (bx, by) in enumerate(BAYS):
        lift = bay_lift[b]
        busy = lift > 0.5
        col = GREEN if busy else TEAL
        d.rounded_rectangle([bx, by, bx + BAY_W, by + BAY_H], radius=6, fill=(10, 14, 20),
                            outline=alpha(GREEN if busy else DIM, pa * 0.8), width=2)
        d.ellipse([bx + 6, by + 6, bx + 12, by + 12], fill=alpha(col, pa * (0.95 if busy else 0.3)))
        d.text((bx + BAY_W - 7, by + 9), f"{b + 1:02d}", font=MONO(7),
               fill=alpha(MUTED, pa * 0.55), anchor="rm")
        pcx, pcy = bx + BAY_W / 2, by + 20 - lift
        if busy:  # flex cable from lifted plug down into its bay
            d.line([(pcx, pcy + 12), (bx + BAY_W / 2, by + 28)], fill=alpha(col, pa * 0.5), width=1)
        draw_plug(d, pcx, pcy, col, pa)

    in_use = sum(1 for L in bay_lift if L > 0.5)
    track(d, ((RACK[0] + RACK[2]) / 2, 706), f"IN USE {in_use}/{POOL_SIZE}",
          MONO(8), alpha(GREEN, pa), sp=1, anchor="mm")

    # request orbs: approach, pop a plug, ride the trunk, come back, exit
    for name, t, b, ph in orb_draws:
        x, y = pool_pos(name, t, ph)
        oa = pa
        if name == "exit":
            oa *= 1 - t
        if name == "in":
            oa *= min(1.0, t * 4)
        col = GREEN if name in ("pop", "ride", "query", "back") else BLUE
        if name in ("ride", "back"):
            d.line([ph, (x, y)], fill=alpha(GREEN, pa * 0.5), width=1)
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=alpha(col, oa))
        d.ellipse([x - 10, y - 10, x + 10, y + 10], outline=alpha(col, oa * 0.4), width=1)


# ---------------------------------------------------------------- counter zone
def draw_counter_zone(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180

    za = a * (1 - ease((fr - 180) / 10))   # naive-world counter fades out
    if za > 0.01:
        att = attempt_count(fr)
        if beat2:
            col, label = RED, "CONNECTION ATTEMPTS"
            suffix, fill = "/ 3 SECONDS", min(1.0, att / ATTEMPTS_B2)
            note = ("✗ FATAL: TOO MANY CONNECTIONS · 95% REJECTED" if fr >= 168 else
                    "handshake factory thrashing · DB rejecting")
        else:
            col, label = TEAL, "FRESH CONNECTIONS OPENED"
            suffix, fill = "· 50ms SETUP EACH", att / 6
            note = "each one rebuilt TCP + TLS + auth from scratch"
        track(d, (90, 816), label, MONOB(11), alpha(col, za), sp=2)
        big = f"{att:,}"
        d.text((90, 846), big, font=MONOB(30), fill=alpha(col, za), anchor="lm")
        d.text((90 + d.textlength(big, font=MONOB(30)) + 10, 852), suffix,
               font=MONOB(11), fill=alpha(MUTED, za), anchor="lm")
        d.rectangle([90, 872, 630, 888], outline=alpha(DIM, za), width=1)
        d.rectangle([90, 872, 90 + 540 * fill, 888], fill=alpha(col, za * 0.8))
        ncol = col if "✗" in note else MUTED
        d.text((90, 898), note, font=SANS(11), fill=alpha(ncol, za), anchor="lm")

    ea = a * ease((fr - 184) / 10)          # pooled-world counter fades in
    if ea > 0.01:
        co = checkout_count(fr)
        track(d, (90, 816), "POOL CHECKOUTS", MONOB(11), alpha(GREEN, ea), sp=2)
        big = f"{co:,}"
        d.text((90, 846), big, font=MONOB(30), fill=alpha(GREEN, ea), anchor="lm")
        d.text((90 + d.textlength(big, font=MONOB(30)) + 10, 852), "· 0 NEW HANDSHAKES",
               font=MONOB(11), fill=alpha(GREEN, ea * 0.8), anchor="lm")
        d.rectangle([90, 872, 630, 888], outline=alpha(DIM, ea), width=1)
        d.rectangle([90, 872, 90 + 540 * co / CHECKOUTS, 888], fill=alpha(GREEN, ea * 0.8))
        d.text((90, 898), "✓ 0.8ms avg checkout · each conn reused 8,820x",
               font=SANS(11), fill=alpha(GREEN, ea), anchor="lm")


# ---------------------------------------------------------------- frame
def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    fa = a * (1 - ease((fr - 180) / 12))   # naive world dissolves into beat 3
    pa = a * ease((fr - 184) / 10)         # pooled world crystallizes

    # ---- Header (flagship grammar)
    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 192), "NAIVE: NEW CONN PER REQUEST  vs  WARM POOL OF 20",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    tw1 = d.textlength("CONNECTION ", font=SANSB(42))
    tw2 = d.textlength("POOLING", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 228), "CONNECTION ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 228), "POOLING", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "why one warm socket beats a 50ms TCP + TLS + auth handshake",
           font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")

    if diag <= 0.01:
        return base

    # ---- Telemetry HUD
    if beat3:
        lat, latc, thr, thrc = "0.8ms", GREEN, "45k req/s", GREEN
    elif beat2:
        lat = f"{int(lerp(52, 4200, ease((fr - 90) / 85))):,}ms"
        spike = ease((fr - 90) / 12)
        crash = ease((fr - 112) / 60)
        thr = f"{int(lerp(lerp(800, 40_000, spike), 1_200, crash)):,} req/s"
        latc, thrc = RED, RED if fr > 112 else AMBER
    else:
        lat, latc, thr, thrc = "52ms", TEAL, "800 req/s", BLUE
    draw_telemetry_hud(d, "LATENCY", lat, "THROUGHPUT", thr, a, m1_col=latc, m2_col=thrc)

    # ---- Runtime status line
    if beat3:
        st, stc = "APP RUNTIME · POOLED · CHECKOUT ▸ QUERY ▸ RETURN", GREEN
    elif beat2:
        st, stc = "APP RUNTIME · CONNECTION STORM · MAX_CONNECTIONS BLOWN", RED
    else:
        st, stc = "APP RUNTIME · NAIVE DRIVER · OPEN 1 CONN PER REQUEST", MUTED
    track(d, (W / 2, 390), st, MONOB(10), alpha(stc, a * (pulse if beat2 else 1.0)), sp=1, anchor="mm")

    # ---- Stage
    lane_label(d, max(fa, pa))
    draw_intake(d, fa)
    draw_factory(d, fr, fa)
    draw_wedge(d, fr, fa)
    draw_heap(d, fr, fa)
    draw_naive_orbs(d, fr, fa)

    # beat 2 opening: traffic spike alarm tag
    if 90 <= fr <= 132:
        ga = ease((fr - 90) / 5) * (1 - ease((fr - 122) / 10))
        track(d, (W / 2, 436), "⚠ TRAFFIC SPIKE x50 → 40,000 REQ/S",
              MONOB(11), alpha(RED, a * ga * pulse), sp=2, anchor="mm")

    # beat 2 closing: fatal stamp
    if 168 <= fr <= 196:
        so = ease((fr - 168) / 6) * (1 - ease((fr - 188) / 8))
        track(d, (W / 2, 692), "✗ FATAL: TOO MANY CONNECTIONS (MAX 100)",
              MONOB(14), alpha(RED, a * so * pulse), sp=2, anchor="mm")

    draw_silo(d, fr, a)      # the database persists across all three beats
    draw_pool(d, fr, pa)
    draw_counter_zone(d, fr, a)

    # beat 3 takeaway line
    if fr >= 200:
        if fr >= 254:
            track(d, (W / 2, 944), "✓ 0.8ms CHECKOUT — 20 WARM CONNS vs 50ms HANDSHAKE",
                  MONOB(11), alpha(GREEN, a), sp=1, anchor="mm")
        else:
            track(d, (W / 2, 944), "POOL CYCLE: CHECKOUT ▸ QUERY ▸ RETURN ▸ REUSE",
                  MONOB(11), alpha(TEAL, a), sp=1, anchor="mm")

    # ---- Caption pill + outro footer
    draw_caption_pill(d, fr, CAPTIONS, a)
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "POOL SIZE ~ (CORES x 2) + SPINDLES · THINK TIME 30s",
              MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "HIKARICP · PGBOUNCER · RDS PROXY · PGXPOOL · MAX_LIFETIME",
              MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base


def render_and_save_frame(args):
    fr, out_dir = args
    finish(render(fr), fr).save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_connection_pooling"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, [(fr, out_dir) for fr in frames]))
    print(f"Rendered Connection Pooling frames: {len(frames)}")
