#!/usr/bin/env python3
"""
Flagship System Design Reel: WebSockets vs Polling (HTTP Poll Flood vs Full-Duplex Push Pipe)
Visual Apparatus: a phone client polling a server through request/response lanes — hollow 204
rings return empty until a poll flood jams the lanes and fills a waste bin — then one
101-switch handshake seals a pneumatic full-duplex pipe and events stream straight through.
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
    (0,   "the client re-downloads the entire feed every 5 seconds."),
    (60,  "traffic ×10 — 4,700 clients hammer the same endpoint."),
    (124, "8,640 empty 204s · 92% of CPU cycles burned for nothing."),
    (188, "one handshake opens a permanent full-duplex push pipe."),
    (250, "events arrive in 23ms · zero wasted requests."),
]

# geometry
PH = (80, 530, 220, 770)          # phone client
RK = (505, 560, 655, 740)         # server rack
LK_X0, LK_X1 = 224, 501           # lane travel span
Y_REQ, Y_RESP, Y_MID = 570, 640, 605

# beat 1 poll cycles: request out -> server check -> response back
CYCLES = [
    {"req": (18, 28), "chk": (28, 32), "resp": (32, 42), "hit": False},
    {"req": (44, 54), "chk": (54, 58), "resp": (58, 68), "hit": False},
    {"req": (66, 75), "chk": (75, 78), "resp": (78, 87), "hit": True},
]
DROP = (48, 56)                    # event token falls into the hopper
HIT_200_S = 140                    # beat 2's single lucky poll


def orb(d, x, y, col, a, r=4.5, hollow=False):
    if hollow:
        d.ellipse([x - r, y - r, x + r, y + r], outline=alpha(col, a), width=2)
    else:
        d.ellipse([x - r, y - r, x + r, y + r], fill=alpha(col, a))
        d.ellipse([x - r - 3, y - r - 3, x + r + 3, y + r + 3],
                  outline=alpha(col, a * 0.4), width=1)


def token(d, x, y, a, col=AMBER):
    d.rounded_rectangle([x - 4, y - 4, x + 4, y + 4], radius=2, fill=alpha(col, a))


def draw_transport_pill(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    col = GREEN if beat3 else (RED if beat2 else BLUE)
    ca = a * (pulse if beat2 else 1.0)
    d.rounded_rectangle([90, 415, 630, 465], radius=10, fill=(12, 16, 24),
                        outline=alpha(col, ca * 0.9), width=2)
    d.ellipse([104, 433, 118, 447], fill=alpha(col, ca))
    if beat3:
        track(d, (132, 429), 'new WebSocket("wss://api/feed")',
              MONOB(12), alpha(WHITE, a), sp=0, anchor="lm")
        d.text((132, 450), "one connection · server pushes instantly",
               font=SANS(10), fill=alpha(GREEN, a), anchor="lm")
    else:
        track(d, (132, 429), 'while (true) { fetch("/feed"); sleep(5s); }',
              MONOB(12), alpha(WHITE, a), sp=0, anchor="lm")
        sub = "4,700 clients · same poll cadence" if beat2 else "every 5 seconds · feed re-checked from scratch"
        d.text((132, 450), sub, font=SANS(10), fill=alpha(RED if beat2 else MUTED, a), anchor="lm")


def draw_phone(d, fr, a):
    x0, y0, x1, y1 = PH
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    # antenna
    d.line([(150, y0), (150, y0 - 20)], fill=alpha(WHITE, a * 0.7), width=2)
    glow = beat3 and any(s + 16 <= fr <= s + 24 for s in range(214, 293, 9))
    d.ellipse([145, y0 - 28, 155, y0 - 18], fill=alpha(GREEN if glow else WHITE, a))
    d.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=(11, 14, 20),
                        outline=alpha(RED if beat2 else WHITE, a * (pulse if beat2 else 0.9)), width=2)
    d.rectangle([92, 555, 208, 715], fill=(6, 8, 12), outline=alpha(DIM, a * 0.8), width=1)

    # screen header
    hdr = "FEED · LIVE" if beat3 else ("FEED · STALE" if beat2 else "FEED")
    hc = GREEN if beat3 else (RED if beat2 else MUTED)
    track(d, (150, 570), hdr, MONOB(9), alpha(hc, a * (pulse if beat2 else 1.0)), sp=1, anchor="mm")

    # feed rows (avatar + bar), flash green when a real event lands
    dim = 0.4 if beat2 else 0.85
    for i in range(3):
        ry = 590 + i * 32
        just_hit = False
        if beat3:
            for k, s in enumerate(range(214, 293, 9)):
                ar = s + 16
                if ar <= fr <= ar + 8 and k % 3 == i:
                    just_hit = True
        elif 85 <= fr <= 97 and i == 0:
            just_hit = True
        col = GREEN if just_hit else MUTED
        d.rectangle([100, ry - 5, 110, ry + 5], outline=alpha(col, a * (1.0 if just_hit else dim)), width=1)
        d.line([(118, ry - 2), (200, ry - 2)], fill=alpha(col, a * (1.0 if just_hit else dim)), width=3)
        if just_hit:
            d.rectangle([94, ry - 11, 216, ry + 11], outline=alpha(GREEN, a * 0.8), width=1)

    # status line
    st = "LIVE · 23ms" if beat3 else ("STALE · 8s OLD" if beat2 else "POLL · 5s")
    sc = GREEN if beat3 else (RED if beat2 else TEAL)
    d.text((150, 695), st, font=MONOB(9), fill=alpha(sc, a * (pulse if beat2 else 1.0)), anchor="mm")
    # bezel
    d.rounded_rectangle([135, 728, 165, 733], radius=2, fill=alpha(DIM, a * 0.8))
    d.text((150, 752), "CLIENT · BROWSER", font=MONO(8), fill=alpha(MUTED, a * 0.8), anchor="mm")


def draw_server(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    x0, y0, x1, y1 = RK
    d.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=(11, 14, 20),
                        outline=alpha(RED if beat2 else WHITE, a * (pulse if beat2 else 0.9)), width=2)
    led = RED if beat2 else (GREEN if beat3 else TEAL)
    for b in range(3):
        by0, by1 = y0 + 8 + b * 58, y0 + 58 + b * 58
        d.rectangle([x0 + 8, by0, x1 - 8, by1], outline=alpha(DIM, a * 0.8), width=1)
        if b < 2:
            blink = 0.35 + 0.55 * math.sin(fr * (0.9 if beat2 else 0.22) + b * 2.1)
            d.ellipse([x0 + 16, (by0 + by1) / 2 - 4, x0 + 24, (by0 + by1) / 2 + 4],
                      fill=alpha(led, a * blink))
            for v in range(3):
                d.line([(x0 + 40 + v * 14, by0 + 12), (x0 + 40 + v * 14, by1 - 12)],
                       fill=alpha(DIM, a * 0.9), width=2)
    d.text(((x0 + x1) / 2, 709), "SERVER · api", font=MONO(8),
           fill=alpha(MUTED, a * 0.8), anchor="mm")
    # CPU badge during the poll flood
    if beat2:
        d.rectangle([x0 + 28, y0 + 26, x1 - 28, y0 + 50], fill=(18, 10, 14),
                    outline=alpha(RED, a * pulse), width=1)
        track(d, ((x0 + x1) / 2, y0 + 38), "CPU 98%", MONOB(10),
              alpha(RED, a * pulse), sp=1, anchor="mm")

    # event hopper feeding the rack
    d.polygon([(535, 500), (625, 500), (600, 552), (560, 552)],
              outline=alpha(WHITE, a * 0.75), width=2)
    d.line([(568, 552), (568, y0)], fill=alpha(DIM, a * 0.9), width=2)
    d.line([(592, 552), (592, y0)], fill=alpha(DIM, a * 0.9), width=2)

    # resting event tokens inside the hopper
    if beat3:
        for i in range(3):
            token(d, 560 + i * 20, 522, a * 0.9)
    elif 56 <= fr < 75 or (126 <= fr < HIT_200_S):
        token(d, 580, 522, a)


def draw_lanes(d, fr, a):
    """beat 1–2 request/response lanes and their orbs."""
    fade = 1 - ease((fr - 180) / 16)
    ta = a * fade
    if ta <= 0.01:
        return
    beat2 = fr >= 90
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    if not beat2:
        # subtle lane guides
        for ly in (Y_REQ, Y_RESP):
            d.line([(LK_X0, ly), (LK_X1, ly)], fill=alpha(DIM, ta * 0.5), width=1)

    if not beat2:
        # ---- beat 1: three clean poll cycles
        for ci, c in enumerate(CYCLES):
            rs, re_ = c["req"]
            if rs <= fr <= re_:
                t = ease((fr - rs) / (re_ - rs))
                ox = lerp(LK_X0, LK_X1, t)
                d.line([(max(LK_X0, ox - 20), Y_REQ), (ox, Y_REQ)], fill=alpha(BLUE, ta * 0.4), width=2)
                orb(d, ox, Y_REQ, BLUE, ta)
            cs, ce = c["chk"]
            if cs <= fr <= ce:
                rr = 4 + (fr - cs) * 2.5
                d.ellipse([LK_X1 - rr, Y_MID - rr, LK_X1 + rr, Y_MID + rr],
                          outline=alpha(TEAL, ta * 0.8), width=2)
            ps, pe = c["resp"]
            if ps <= fr <= pe:
                t = ease((fr - ps) / (pe - ps))
                ox = lerp(LK_X1, LK_X0, t)
                if c["hit"]:
                    orb(d, ox, Y_RESP, GREEN, ta)
                    token(d, ox, Y_RESP, ta)
                    if fr <= pe:
                        d.text((ox, Y_RESP + 16), "200 · POST", font=MONO(8),
                               fill=alpha(GREEN, ta), anchor="mm")
                else:
                    orb(d, ox, Y_RESP, MUTED, ta, hollow=True)
                    if ci == 0:
                        d.text((ox, Y_RESP + 16), "204 · NO DATA", font=MONO(8),
                               fill=alpha(MUTED, ta), anchor="mm")
        # event token falls into the hopper
        ds, de = DROP
        if ds <= fr <= de:
            t = ease((fr - ds) / (de - ds))
            token(d, 580, lerp(468, 518, t), ta)
    else:
        # ---- beat 2: poll flood — dense requests out, hollow 204s jamming back
        for s in range(92, 177, 5):
            if s <= fr <= s + 12:
                t = ease((fr - s) / 12)
                ox = lerp(LK_X0, LK_X1, t)
                col = RED if s >= 112 else BLUE
                d.line([(max(LK_X0, ox - 18), Y_REQ), (ox, Y_REQ)], fill=alpha(col, ta * 0.4), width=2)
                orb(d, ox, Y_REQ, col, ta, r=4)
        for s in range(100, 179, 6):
            dur = 26 if s >= 150 else 14
            if s <= fr <= s + dur:
                t = ease((fr - s) / dur)
                ox = lerp(LK_X1, LK_X0, t)
                if s == HIT_200_S:
                    orb(d, ox, Y_RESP, GREEN, ta)
                    token(d, ox, Y_RESP, ta)
                    d.text((ox, Y_RESP + 16), "200 · ONLY HIT", font=MONO(8),
                           fill=alpha(GREEN, ta), anchor="mm")
                else:
                    orb(d, ox, Y_RESP, RED, ta * (0.6 + 0.4 * pulse), hollow=True)


def draw_waste_bin(d, fr, a):
    fade = 1 - ease((fr - 180) / 16)
    ta = a * fade
    if fr < 92 or ta <= 0.01:
        return
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    d.line([(488, 780), (480, 868)], fill=alpha(DIM, ta), width=2)
    d.line([(642, 780), (650, 868)], fill=alpha(DIM, ta), width=2)
    d.line([(480, 868), (650, 868)], fill=alpha(DIM, ta), width=2)
    n = min(10, 2 + int(8 * ease((fr - 92) / 80)))
    for i in range(n):
        rx = 512 + (i % 5) * 28
        ry = 812 + (i // 5) * 30
        orb(d, rx, ry, RED, ta * 0.8, r=5.5, hollow=True)
    q = 8.64 * ease((fr - 92) / 86)
    track(d, (565, 770), f"×{int(q * 1000):,} WASTED", MONOB(11), alpha(RED, ta * pulse), sp=1, anchor="mm")
    track(d, (565, 886), "EMPTY 204s", MONO(9), alpha(MUTED, ta), sp=2, anchor="mm")


def draw_counter_zone(d, fr, a):
    za = a * (1 - ease((fr - 180) / 10))
    if za <= 0.01:
        return
    if fr >= 90:
        q = 8.64 * ease((fr - 92) / 86)
        counter, col = int(q * 1000), RED
        fill = q * 1000 / 9400.0
        label = "EMPTY 204 RESPONSES"
        note = "✗ POLL QUEUE — USERS SEE STALE FEED" if fr >= 168 else "92% of 9,400 polls return nothing"
    else:
        r = 2 * ease((fr - 32) / 36)
        counter, col, fill = int(r), MUTED, r / 3.0
        label = "EMPTY 204 RESPONSES"
        note = "✓ event on poll 3 · staleness under 5s" if fr >= 78 else "feed unchanged — nothing new to send"
    track(d, (90, 816), label, MONOB(11), alpha(col, za), sp=2)
    big = f"{counter:,}"
    d.text((90, 846), big, font=MONOB(30), fill=alpha(col, za), anchor="lm")
    d.rectangle([90, 872, 430, 888], outline=alpha(DIM, za), width=1)
    d.rectangle([90, 872, 90 + 340 * min(fill, 1.0), 888], fill=alpha(col, za * 0.8))
    ncol = col if ("✓" in note or "✗" in note) else MUTED
    d.text((90, 898), note, font=SANS(11), fill=alpha(ncol, za), anchor="lm")


def draw_pipe(d, fr, a):
    """beat 3: handshake, sealed full-duplex pipe, streaming push frames."""
    if fr < 182:
        return
    a_t = ease((fr - 200) / 10)          # tube walls
    a_badge = ease((fr - 208) / 6) * (1 - ease((fr - 230) / 8))

    track(d, (W / 2, 478), "ONE PIPE · FULL-DUPLEX PUSH",
          MONO(10), alpha(TEAL, a * ease((fr - 182) / 8)), sp=2, anchor="mm")

    # handshake
    if 184 <= fr <= 194:
        t = ease((fr - 184) / 10)
        ox = lerp(LK_X0, LK_X1, t)
        orb(d, ox, Y_REQ, BLUE, a)
        d.text((360, 556), "GET /ws", font=MONO(9), fill=alpha(BLUE, a), anchor="mm")
    if 196 <= fr <= 210:
        t = ease((fr - 196) / 10)
        ox = lerp(LK_X1, LK_X0, t)
        orb(d, ox, Y_RESP, GREEN, a)
        d.text((360, 662), "101 · SWITCHING PROTOCOLS", font=MONOB(10),
               fill=alpha(GREEN, a), anchor="mm")

    # sealed tube
    if a_t > 0.01:
        d.rectangle([LK_X0, Y_REQ, LK_X1, Y_RESP], fill=alpha(TEAL, a * a_t * 0.06))
        d.line([(LK_X0, Y_REQ), (LK_X1, Y_REQ)], fill=alpha(TEAL, a * a_t), width=2)
        d.line([(LK_X0, Y_RESP), (LK_X1, Y_RESP)], fill=alpha(TEAL, a * a_t), width=2)
        for lx in (LK_X0, LK_X1):
            d.line([(lx, Y_REQ - 5), (lx, Y_RESP + 5)], fill=alpha(GREEN, a * a_t), width=3)
        track(d, (360, 556), "WSS:// · FULL-DUPLEX PIPE", MONO(9),
              alpha(TEAL, a * a_t), sp=2, anchor="mm")
    if a_badge > 0.01:
        track(d, (360, 690), "✓ UPGRADED · PIPE SEALED", MONOB(11),
              alpha(GREEN, a * a_badge), sp=2, anchor="mm")

    # incoming event tokens feeding the hopper
    for s in range(206, 293, 12):
        if s <= fr <= s + 6:
            t = ease((fr - s) / 6)
            token(d, 580, lerp(468, 518, t), a)

    # server push frames: hopper -> pipe -> phone
    for s in range(214, 293, 9):
        if s <= fr <= s + 16:
            t = ease((fr - s) / 16)
            ox = lerp(LK_X1, LK_X0, t)
            d.line([(min(LK_X1, ox + 16), 618), (ox, 618)], fill=alpha(AMBER, a * 0.5), width=2)
            token(d, ox, 618, a)
    # small client frames riding back (typing / acks)
    for s in range(224, 293, 14):
        if s <= fr <= s + 16:
            t = ease((fr - s) / 16)
            ox = lerp(LK_X0, LK_X1, t)
            orb(d, ox, 585, BLUE, a * 0.9, r=3)

    # frame log
    logs = [(220, "PUSH ▸ {\"type\":\"post\",\"id\":918}", GREEN),
            (236, "SENT → {\"type\":\"typing\"}", BLUE),
            (252, "PUSH ▸ {\"type\":\"like\",\"id\":204}", GREEN),
            (268, "PUSH ▸ {\"type\":\"post\",\"id\":919}", GREEN)]
    for i, (ls, txt, lc) in enumerate(logs):
        if fr >= ls:
            last = (i == len(logs) - 1) or fr < logs[i + 1][0]
            d.text((90, 824 + i * 22), txt, font=MONO(10),
                   fill=alpha(lc, a * (1.0 if last else 0.45)), anchor="lm")

    # routing ticks
    if fr >= 206:
        d.text((90, 782), "1 TCP CONNECTION · REUSED", font=MONO(9), fill=alpha(TEAL, a), anchor="lm")
    if fr >= 228:
        d.text((90, 800), "0 EMPTY RESPONSES ✓", font=MONO(9), fill=alpha(GREEN, a), anchor="lm")


def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag = ease((fr - 8) / 18)
    a = diag
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    # ---- Header (flagship grammar)
    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 192), "HTTP POLLING  vs  WEBSOCKETS",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    tw1 = d.textlength("POLLING ", font=SANSB(42))
    tw2 = d.textlength("vs ", font=SANSB(32))
    tw3 = d.textlength("WEBSOCKETS", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2 + tw3) / 2
    d.text((sx, 228), "POLLING ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 230), "vs ", font=SANSB(32), fill=alpha(DIM, intro), anchor="lm")
    d.text((sx + tw1 + tw2, 228), "WEBSOCKETS", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "why asking 'anything new?' 24/7 melts your server",
           font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")
    d.line([(48, 290), (W - 48, 290)], fill=alpha(DIM, 0.6), width=1)

    if diag <= 0.01:
        return base

    # ---- Telemetry HUD
    if beat3:
        lat, latc, thr, thrc = "23ms", GREEN, "150k msg/s", GREEN
    elif beat2:
        lat = f"{lerp(5.0, 18.4, ease((fr - 90) / 85)):.1f}s"
        thr = f"{int(lerp(12, 1, ease((fr - 90) / 85)))}k req/s"
        latc, thrc = RED, RED if fr > 120 else AMBER
    else:
        lat, latc, thr, thrc = "2.5s", TEAL, "12k req/s", BLUE
    draw_telemetry_hud(d, "LATENCY", lat, "THROUGHPUT", thr, a, m1_col=latc, m2_col=thrc)

    # ---- Transport status line
    if beat3:
        st, stc = "TRANSPORT: WEBSOCKET · WSS PUSH · FULL-DUPLEX", GREEN
    elif beat2:
        st, stc = "⚠ POLL FLOOD · 98% CPU BURNED ON EMPTY 204s", RED
    else:
        st, stc = "TRANSPORT: HTTP POLLING · GET /feed EVERY 5s", MUTED
    track(d, (W / 2, 390), st, MONOB(10), alpha(stc, a * (pulse if beat2 else 1.0)),
          sp=1, anchor="mm")

    # ---- Stage
    draw_transport_pill(d, fr, a)
    if 90 <= fr <= 132:
        ga = ease((fr - 90) / 5) * (1 - ease((fr - 122) / 10))
        track(d, (W / 2, 486), "⚠ TRAFFIC ×10 — 4,700 CLIENTS POLLING EVERY 5s",
              MONOB(11), alpha(RED, a * ga * pulse), sp=2, anchor="mm")
    draw_phone(d, fr, a)
    draw_server(d, fr, a)
    draw_lanes(d, fr, a)
    draw_waste_bin(d, fr, a)
    if 168 <= fr <= 196:
        so = ease((fr - 168) / 6) * (1 - ease((fr - 188) / 8))
        d.rounded_rectangle([210, 588, 510, 622], radius=8, fill=(16, 10, 12),
                            outline=alpha(RED, a * so), width=1)
        track(d, (W / 2, 605), "✗ POLL FLOOD — 92% WASTED CYCLES",
              MONOB(15), alpha(RED, a * so * pulse), sp=2, anchor="mm")
    draw_counter_zone(d, fr, a)
    draw_pipe(d, fr, a)

    # ---- Beat 3 takeaway line
    if fr >= 200:
        if fr >= 254:
            track(d, (W / 2, 944), "✓ 23ms PUSH · 0 EMPTY 204s · 1 OPEN PIPE",
                  MONOB(11), alpha(GREEN, a), sp=1, anchor="mm")
        else:
            track(d, (W / 2, 944), "PUSH PATH: SERVER ▸ PIPE ▸ SCREEN",
                  MONOB(11), alpha(TEAL, a), sp=1, anchor="mm")

    # ---- Caption pill + outro footer
    draw_caption_pill(d, fr, CAPTIONS, a)
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "ONE HANDSHAKE · FULL-DUPLEX · ZERO WASTE",
              MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "RFC 6455 · SOCKET.IO · MQTT · GRAPHQL SUBSCRIPTIONS",
              MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base


def render_and_save_frame(args):
    fr, out_dir = args
    img = finish(render(fr), fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_websockets_vs_polling"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered WebSockets vs Polling frames: {len(frames)}")
