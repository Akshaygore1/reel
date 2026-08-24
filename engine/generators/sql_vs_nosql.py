#!/usr/bin/env python3
"""
Flagship System Design Reel: SQL vs NoSQL (Merge-Join Monolith vs Sharded Document Store)
Visual Apparatus: two relational tables linked by a mechanical JOIN gear-bridge that
runs clean at 12k req/s, jams red under a x10 query pile-up on one unshardable node,
then the stage rebuilds as a hash router fanning embedded documents across 3 shards.
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
    (0,   "every read JOINs users + orders inside one SQL node."),
    (60,  "traffic ×10 — concurrent JOINs pile onto one machine."),
    (124, "412 queries queued · P99 latency 850ms · timeouts."),
    (188, "NoSQL embeds orders inside the user document · 0 JOINs."),
    (250, "hash router spreads 4.2M docs over 3 shards · 0.12ms."),
]

USERS_ROWS = [("7", "ana"), ("42", "ak"), ("77", "riya"), ("91", "sam"), ("103", "joe"),
              ("128", "lin"), ("157", "mei"), ("180", "omar")]
ORDERS_ROWS = [("A-101", "uid:7"), ("A-109", "uid:91"), ("A-118", "uid:42"), ("A-127", "uid:77"),
               ("B-203", "uid:42"), ("B-214", "uid:103"), ("B-221", "uid:128"), ("C-302", "uid:91")]

# Beat 1 query orb hops: pill -> users -> bridge -> orders -> pill, cycle 2 freezes at the bridge
HOPS1 = [
    (22, 30, (360, 465), (190, 555)),
    (33, 39, (190, 600), (322, 585)),
    (41, 47, (398, 585), (530, 555)),
    (50, 58, (530, 600), (360, 465)),
    (62, 70, (360, 465), (190, 555)),
    (73, 80, (190, 600), (316, 585)),
]

# Beat 3 seek hops: pill -> router -> shard 1 -> document
HOPS3 = [
    (196, 206, (360, 465), (360, 492)),
    (210, 224, (360, 552), (360, 634)),
    (228, 240, (360, 730), (360, 762)),
]

DOC_JSON = [
    '{ "_id": 42, "name": "ak",',
    '  "orders": [',
    '    { "id": "A-118", "amt": 42 },',
    '    { "id": "B-204", "amt": 17 } ] }',
]


def draw_query_pill(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    col = GREEN if beat3 else (RED if beat2 else BLUE)
    ca = a * (pulse if beat2 else 1.0)
    d.rounded_rectangle([90, 415, 630, 465], radius=10, fill=(12, 16, 24),
                        outline=alpha(col, ca * 0.9), width=2)
    d.ellipse([104, 433, 118, 447], fill=alpha(col, ca))
    if beat3:
        track(d, (132, 429), "db.users.findOne({ user_id: 42 })",
              MONOB(12), alpha(WHITE, a), sp=0, anchor="lm")
        d.text((132, 450), "one document read · no JOIN needed",
               font=SANS(10), fill=alpha(GREEN, a), anchor="lm")
    else:
        track(d, (132, 429), "SELECT * FROM users JOIN orders ON id = uid;",
              MONOB(12), alpha(WHITE, a), sp=0, anchor="lm")
        sub = "joins need BOTH tables on the same node" if beat2 else "1 query = reads from users AND orders"
        d.text((132, 450), sub, font=SANS(10), fill=alpha(RED if beat2 else MUTED, a), anchor="lm")


def draw_tables(d, fr, a):
    fade = 1 - ease((fr - 180) / 16)
    ta = a * fade
    if ta <= 0.01:
        return
    beat2 = fr >= 90
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    found = (not beat2) and fr >= 58

    for (x0, x1, name, cnt) in ((60, 320, "TABLE users", "1,000 ROWS"),
                                (400, 660, "TABLE orders", "10,000 ROWS")):
        d.rectangle([x0, 505, x1, 531], fill=(14, 18, 26),
                    outline=alpha(WHITE, ta * 0.7), width=2)
        d.text((x0 + 10, 518), name, font=MONOB(10), fill=alpha(WHITE, ta), anchor="lm")
        rc = alpha(RED, ta * pulse) if beat2 else MUTED
        d.text((x1 - 10, 518), cnt, font=MONO(9), fill=alpha(rc, ta), anchor="rm")

    def row(x0, x1, i, c0, c1, cx1, hl):
        y = 545 + i * 26
        d.rectangle([x0, y, x1, y + 24], fill=(11, 14, 20),
                    outline=alpha(DIM, ta * 0.7), width=1)
        if hl:
            if not beat2 and found:
                oc, oa, tint = GREEN, 0.9, True
            elif not beat2:
                oc, oa, tint = WHITE, 0.5, False
            else:
                oc, oa, tint = WHITE, 0.25, False
            if tint:
                d.rectangle([x0, y, x1, y + 24], fill=alpha(GREEN, ta * 0.14))
            d.rectangle([x0, y, x1, y + 24], outline=alpha(oc, ta * oa), width=2)
        tcol = WHITE if hl else MUTED
        d.text((x0 + 12, y + 12), c0, font=MONO(10), fill=alpha(tcol, ta), anchor="lm")
        d.text((cx1, y + 12), c1, font=MONO(10), fill=alpha(tcol, ta * 0.85), anchor="lm")

    for i, (rid, nm) in enumerate(USERS_ROWS):
        row(60, 320, i, rid, nm, 120, i == 1)
    for i, (oid, uid) in enumerate(ORDERS_ROWS):
        row(400, 660, i, oid, uid, 548, uid == "uid:42")


def draw_bridge(d, fr, a):
    fade = 1 - ease((fr - 180) / 16)
    ta = a * fade
    if ta <= 0.01:
        return
    beat2 = fr >= 90
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    col = RED if beat2 else TEAL
    ca = ta * (pulse if beat2 else 1.0)

    # shafts + end plates
    d.line([(322, 566), (398, 566)], fill=alpha(col, ca * 0.8), width=2)
    d.line([(322, 604), (398, 604)], fill=alpha(col, ca * 0.8), width=2)
    for px in (322, 398):
        d.line([(px, 556), (px, 614)], fill=alpha(col, ca), width=3)

    # travelling link ticks (freeze when the join jams)
    ph = min(fr, 90) * 2.2
    for k in range(5):
        tx = 328 + ((k * 16 + ph) % 68)
        for ty in (566, 604):
            d.line([(tx, ty - 4), (tx, ty + 4)], fill=alpha(col, ca * 0.6), width=1)

    # drive gear
    gx, gy = 360.0, 585.0
    if beat2:
        gx += math.sin(fr * 2.3) * 1.2
    ang = fr * 0.22 if fr < 90 else 90 * 0.22 + math.sin(fr * 1.9) * 0.015
    d.ellipse([gx - 20, gy - 20, gx + 20, gy + 20], outline=alpha(col, ca), width=2)
    d.ellipse([gx - 12, gy - 12, gx + 12, gy + 12], outline=alpha(col, ca * 0.8), width=1)
    for k in range(8):
        an = ang + k * math.pi / 4
        d.line([(gx + 12 * math.cos(an), gy + 12 * math.sin(an)),
                (gx + 20 * math.cos(an), gy + 20 * math.sin(an))],
               fill=alpha(col, ca * 0.9), width=2)
    d.ellipse([gx - 3, gy - 3, gx + 3, gy + 3], fill=alpha(col, ca))
    track(d, (360, 634), "JOIN", MONOB(9), alpha(col, ca), sp=2, anchor="mm")
    if beat2:
        track(d, (360, 548), "⚠ JAM", MONOB(9), alpha(RED, ta * pulse), sp=1, anchor="mm")


def draw_orb_beat1(d, fr, a):
    fade = 1 - ease((fr - 180) / 16)
    ta = a * fade
    if ta <= 0.01 or fr >= 92:
        return
    for hs, he, p0, p1 in HOPS1:
        if fr < hs:
            break
        ht = ease((fr - hs) / (he - hs))
        ox, oy = lerp(p0[0], p1[0], ht), lerp(p0[1], p1[1], ht)
        if ht < 1.0:
            d.line([p0, (ox, oy)], fill=alpha(TEAL, ta * 0.5), width=2)
            d.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], fill=alpha(TEAL, ta))
            d.ellipse([ox - 9, oy - 9, ox + 9, oy + 9], outline=alpha(TEAL, ta * 0.5), width=1)


def draw_monolith(d, fr, a):
    if fr < 92:
        return
    fade = 1 - ease((fr - 180) / 16)
    ta = a * fade
    if ta <= 0.01:
        return
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    d.rectangle([48, 496, 672, 770], outline=alpha(RED, ta * pulse), width=2)
    d.rectangle([210, 762, 510, 778], fill=(12, 10, 14),
                outline=alpha(RED, ta * pulse), width=1)
    track(d, (360, 770), "1 NODE · 0 SHARDS · A JOIN CANNOT SHARD",
          MONOB(9), alpha(RED, ta * pulse), sp=1, anchor="mm")
    if 136 <= fr <= 182:
        so = ease((fr - 136) / 6) * (1 - ease((fr - 176) / 6))
        track(d, (360, 792), "✗ SCALE-UP: 4× CPU · SAME SINGLE JOIN QUEUE",
              MONO(9), alpha(RED, ta * so), sp=1, anchor="mm")


def draw_queue(d, fr, a):
    fade = 1 - ease((fr - 180) / 16)
    ta = a * fade
    if fr < 92 or ta <= 0.01:
        return
    n = 1 + int(4 * ease((fr - 92) / 55))
    for i in range(n):
        x = 316 - 46 * i
        y = 585 + 3 * math.sin(fr * 0.3 + i * 1.1)
        d.line([(x + 7, y), (x + 22, y)], fill=alpha(RED, ta * 0.5), width=2)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=alpha(RED, ta))
        d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=alpha(RED, ta * 0.4), width=1)


def draw_counter_zone(d, fr, a):
    za = a * (1 - ease((fr - 180) / 10))
    if za <= 0.01:
        return
    if fr >= 90:
        q = 4.12 * ease((fr - 92) / 86)
        counter, col, fill = int(q * 100), RED, q * 100 / 480.0
        label = "QUEUED QUERIES"
        note = "✗ P99 TIMEOUT — 850ms" if fr >= 168 else "joins serialize on a single CPU…"
    else:
        r = 11.0 * ease((fr - 18) / 52)
        counter, col, fill = int(r * 1000), TEAL, r / 11.0
        label = "ROWS SCANNED / QUERY"
        note = "✓ hash join materialized · 0.4ms" if fr >= 58 else "scanning users + orders…"
    track(d, (90, 816), label, MONOB(11), alpha(col, za), sp=2)
    big = f"{counter:,}"
    d.text((90, 846), big, font=MONOB(30), fill=alpha(col, za), anchor="lm")
    d.rectangle([90, 872, 630, 888], outline=alpha(DIM, za), width=1)
    d.rectangle([90, 872, 90 + 540 * min(fill, 1.0), 888], fill=alpha(col, za * 0.8))
    ncol = col if ("✓" in note or "✗" in note) else MUTED
    d.text((90, 898), note, font=SANS(11), fill=alpha(ncol, za), anchor="lm")


def draw_document_store(d, fr, a):
    if fr < 182:
        return
    a_tag = ease((fr - 182) / 8)
    a_r = ease((fr - 184) / 8)
    a_s = ease((fr - 188) / 8)
    a_e = ease((fr - 196) / 8)
    a_d = ease((fr - 198) / 8)

    track(d, (W / 2, 478), "DOCUMENT STORE · ORDERS EMBEDDED IN USER",
          MONO(10), alpha(TEAL, a * a_tag), sp=2, anchor="mm")

    # fan-out edges + travelling document packets
    edges = [((338, 540), (160, 640)), ((360, 548), (360, 640)), ((382, 540), (560, 640))]
    if a_e > 0.01:
        for ei, (p0, p1) in enumerate(edges):
            on = ei == 1 and fr >= 224
            col = GREEN if on else TEAL
            d.line([p0, p1], fill=alpha(col, a * a_e * (0.95 if on else 0.55)),
                   width=3 if on else 1)
        for ei, (p0, p1) in enumerate(edges):
            col = GREEN if (ei == 1 and fr >= 224) else TEAL
            for k in range(3):
                t = (fr * 0.018 + k / 3.0 + ei * 0.13) % 1.0
                px, py = lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t)
                d.ellipse([px - 2.5, py - 2.5, px + 2.5, py + 2.5],
                          fill=alpha(col, a * a_e * 0.8))

    # hash router
    rx, ry = 360, 522
    d.ellipse([rx - 26, ry - 26, rx + 26, ry + 26], outline=alpha(TEAL, a * a_r), width=2)
    d.ellipse([rx - 17, ry - 17, rx + 17, ry + 17], outline=alpha(TEAL, a * a_r * 0.6), width=1)
    for k in range(3):
        an = fr * 0.03 + k * 2 * math.pi / 3
        d.line([(rx, ry), (rx + 15 * math.cos(an), ry + 15 * math.sin(an))],
               fill=alpha(TEAL, a * a_r * 0.7), width=1)
    d.text((rx, ry), "#", font=MONOB(14), fill=alpha(WHITE, a * a_r), anchor="mm")
    d.text((394, 522), "ROUTER", font=MONOB(9), fill=alpha(MUTED, a * a_r), anchor="lm")

    # shard nodes
    for i, (sx0, sx1) in enumerate(((60, 240), (270, 450), (480, 660))):
        cx = (sx0 + sx1) / 2
        hit = i == 1 and fr >= 224
        col = GREEN if hit else TEAL
        if hit:
            d.rectangle([sx0 - 4, 636, sx1 + 4, 730], outline=alpha(GREEN, a * a_s * 0.3), width=2)
        d.rectangle([sx0, 640, sx1, 726], fill=(10, 14, 20),
                    outline=alpha(col, a * a_s), width=2 if hit else 1)
        d.text((cx, 655), f"SHARD {i}", font=MONOB(11), fill=alpha(WHITE, a * a_s), anchor="mm")
        d.text((cx, 672), f"uid%3={i} · 1.4M docs", font=MONO(8),
               fill=alpha(col, a * a_s * 0.9), anchor="mm")
        for j in range(3):
            mx = cx - 30 + j * 30
            d.rounded_rectangle([mx, 692, mx + 16, 706], radius=2,
                                fill=alpha(col, a * a_s * 0.2),
                                outline=alpha(col, a * a_s * 0.7), width=1)

    # the embedded document
    if a_d > 0.01:
        pop = (1 - a_d) * -12
        x0, x1 = 200, 520
        y0, y1 = 770 + pop, 916 + pop
        d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=(10, 14, 20),
                            outline=alpha(TEAL, a * a_d), width=2)
        track(d, ((x0 + x1) / 2, y0 + 16), "COLLECTION users · _id: 42",
              MONOB(9), alpha(MUTED, a * a_d), sp=1, anchor="mm")
        doc_hit = fr >= 242
        for li, line in enumerate(DOC_JSON):
            ly = y0 + 44 + li * 24
            embedded = li >= 1
            if doc_hit and li >= 2:
                d.rectangle([x0 + 14, ly - 11, x1 - 14, ly + 11], fill=alpha(GREEN, a * a_d * 0.12))
            lcol = GREEN if (doc_hit and li >= 2) else (TEAL if embedded else WHITE)
            d.text((x0 + 50, ly), line, font=MONO(11), fill=alpha(lcol, a * a_d), anchor="lm")
        track(d, ((x0 + x1) / 2, y1 - 14), "ORDERS EMBEDDED → ZERO JOINs",
              MONO(9), alpha(TEAL, a * a_d), sp=1, anchor="mm")

    # seek orb: pill -> router -> shard 1 -> document
    for hs, he, p0, p1 in HOPS3:
        if fr < hs:
            break
        ht = ease((fr - hs) / (he - hs))
        ox, oy = lerp(p0[0], p1[0], ht), lerp(p0[1], p1[1], ht)
        if ht < 1.0:
            d.line([p0, (ox, oy)], fill=alpha(GREEN, a * 0.5), width=2)
            d.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], fill=alpha(GREEN, a))
            d.ellipse([ox - 9, oy - 9, ox + 9, oy + 9], outline=alpha(GREEN, a * 0.5), width=1)
    if fr >= 240:  # shard -> document pointer stays as a permanent arrow
        d.line([(360, 730), (360, 762)], fill=alpha(GREEN, a * 0.9), width=2)
        for da in (2.55, -2.55):
            d.line([(360, 762), (360 - 10 * math.cos(da + math.pi / 2),
                                 762 - 10 * math.sin(da + math.pi / 2))],
                   fill=alpha(GREEN, a * 0.9), width=2)

    # routing ticks
    if fr >= 206:
        d.text((60, 538), "shard = hash(user_id) % 3", font=MONO(9),
               fill=alpha(TEAL, a), anchor="lm")
    if fr >= 228:
        d.text((60, 556), "1 OF 3 SHARDS READ ✓", font=MONO(9),
               fill=alpha(GREEN, a), anchor="lm")

    # document hit impact ring
    if 242 <= fr <= 262:
        ra = 1 - ease((fr - 242) / 20)
        rr = 8 + (fr - 242) * 1.4
        d.ellipse([360 - rr, 843 - rr, 360 + rr, 843 + rr],
                  outline=alpha(GREEN, a * ra), width=2)


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
    track(d, (W / 2, 192), "RELATIONAL (POSTGRES)  vs  DOCUMENT (MONGODB)",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    tw1 = d.textlength("SQL ", font=SANSB(42))
    tw2 = d.textlength("vs ", font=SANSB(32))
    tw3 = d.textlength("NoSQL", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2 + tw3) / 2
    d.text((sx, 228), "SQL ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 230), "vs ", font=SANSB(32), fill=alpha(DIM, intro), anchor="lm")
    d.text((sx + tw1 + tw2, 228), "NoSQL", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "why the JOIN decides if you scale up or scale out",
           font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")
    d.line([(48, 290), (W - 48, 290)], fill=alpha(DIM, 0.6), width=1)

    if diag <= 0.01:
        return base

    # ---- Telemetry HUD
    if beat3:
        lat, latc, thr, thrc = "0.12ms", GREEN, "150k req/s", GREEN
    elif beat2:
        lat = f"{int(lerp(12, 850, ease((fr - 90) / 85)))}ms"
        thr = f"{int(lerp(12, 1, ease((fr - 90) / 85)))}k req/s"
        latc, thrc = RED, RED if fr > 120 else AMBER
    else:
        lat, latc, thr, thrc = "0.4ms", TEAL, "12k req/s", BLUE
    draw_telemetry_hud(d, "LATENCY", lat, "THROUGHPUT", thr, a, m1_col=latc, m2_col=thrc)

    # ---- Execution plan status line
    if beat3:
        st, stc = "QUERY PLAN: findOne({user_id}) · ROUTED BY SHARD KEY", GREEN
    elif beat2:
        st, stc = "⚠ HASH JOIN SATURATED · pg-primary · 98% CPU", RED
    else:
        st, stc = "QUERY PLAN: HASH JOIN · users + orders ON uid", MUTED
    track(d, (W / 2, 390), st, MONOB(10), alpha(stc, a * (pulse if beat2 else 1.0)),
          sp=1, anchor="mm")

    # ---- Stage
    draw_query_pill(d, fr, a)
    if 90 <= fr <= 132:
        ga = ease((fr - 90) / 5) * (1 - ease((fr - 122) / 10))
        track(d, (W / 2, 486), "⚠ TRAFFIC ×10 — 480 CONCURRENT JOIN QUERIES",
              MONOB(11), alpha(RED, a * ga * pulse), sp=2, anchor="mm")
    draw_tables(d, fr, a)
    draw_bridge(d, fr, a)
    draw_orb_beat1(d, fr, a)
    draw_monolith(d, fr, a)
    draw_queue(d, fr, a)
    if 168 <= fr <= 196:
        so = ease((fr - 168) / 6) * (1 - ease((fr - 188) / 8))
        d.rounded_rectangle([215, 650, 505, 686], radius=8, fill=(16, 10, 12),
                            outline=alpha(RED, a * so), width=1)
        track(d, (W / 2, 668), "✗ JOIN TIMEOUT — 850ms P99",
              MONOB(15), alpha(RED, a * so * pulse), sp=2, anchor="mm")
    draw_counter_zone(d, fr, a)
    draw_document_store(d, fr, a)

    # ---- Beat 3 takeaway line
    if fr >= 200:
        if fr >= 254:
            track(d, (W / 2, 944), "✓ 0.12ms READS · 0 JOINs · 150k req/s",
                  MONOB(11), alpha(GREEN, a), sp=1, anchor="mm")
        else:
            track(d, (W / 2, 944), "READ PATH: ROUTER ▸ SHARD ▸ DOCUMENT",
                  MONOB(11), alpha(TEAL, a), sp=1, anchor="mm")

    # ---- Caption pill + outro footer
    draw_caption_pill(d, fr, CAPTIONS, a)
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "DENORMALIZE · EMBED · HASH-SHARD · SCALE OUT",
              MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "POSTGRES · MYSQL · MONGODB · DYNAMODB · CASSANDRA",
              MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base


def render_and_save_frame(args):
    fr, out_dir = args
    img = finish(render(fr), fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_sql_vs_nosql"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered SQL vs NoSQL frames: {len(frames)}")
