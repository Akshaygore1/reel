#!/usr/bin/env python3
"""
Flagship System Design Reel: Database Indexing (Sequential Scan vs B+Tree Index)
Visual Apparatus: Row-slab table with a creeping sequential scan gate that times
out one row before the match, then a B+Tree crystallizes and a seek orb hops
root -> internal -> leaf -> rowid pointer in exactly 3 page reads.
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
    (0,   "your API needs one user row out of 10,000,000."),
    (60,  "without an index, Postgres reads every row top to bottom."),
    (124, "8.4 million row reads later... 850ms of disk I/O. Timeout."),
    (188, "one CREATE INDEX builds a sorted B+Tree over the email column."),
    (250, "3 page reads. 0.12ms. the seek lands directly on the row."),
]

TOTAL_ROWS = 10_000_000
TARGET_RID = 8_432_911
TX0, TX1 = 60, 660          # table x span
NROWS = 10                  # visible row slabs

# B+Tree layout: root keys route the seek; leaves hold email -> rowid pointers.
ROOT   = (365, 505, 150, 44, ["k", "t"])
INTERN = [(161, 592, ["c"]), (365, 592, ["p"]), (569, 592, ["x"])]
LEAF_W, LEAF_H = 92, 36
LEAVES = [(110, "8.4M"), (212, "550k"), (314, "31M"), (416, "3.1M"), (518, "9.7M"), (620, "12M")]

# Seek orb hops (start_frame, end_frame, from_pt, to_pt)
HOPS = [
    (196, 202, (360, 465), (365, 483)),   # query pill -> root top
    (204, 218, (365, 527), (161, 573)),   # root -> internal-0
    (222, 236, (131, 611), (110, 658)),   # internal-0 -> leaf-0
    (240, 254, (110, 694), (188, 862)),   # leaf-0 -> table row (rowid ptr)
]
PAGES = [(202, 452, 505, "PAGE 1"), (218, 226, 592, "PAGE 2"), (236, 166, 676, "PAGE 3")]


def draw_query_pill(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    col = GREEN if beat3 else (RED if beat2 else BLUE)
    ca = a * (pulse if beat2 else 1.0)
    d.rounded_rectangle([90, 415, 630, 465], radius=10, fill=(12, 16, 24),
                        outline=alpha(col, ca * 0.9), width=2)
    d.ellipse([104, 433, 118, 447], fill=alpha(col, ca))
    track(d, (132, 429), "SELECT * FROM users WHERE email = 'ak@dev.io';",
          MONOB(12), alpha(WHITE, a), sp=0, anchor="lm")
    sub = ("index seek resolves it in 3 page reads" if beat3 else
           "needs exactly one row · rowid unknown without an index")
    d.text((132, 450), sub, font=SANS(10), fill=alpha(GREEN if beat3 else MUTED, a), anchor="lm")


def draw_table(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    t = ease((fr - 180) / 20)                      # condense transform (beat 3)
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    hdr_y  = lerp(500, 742, t)
    hdr_h  = lerp(26, 18, t)
    row_h  = lerp(26, 16, t)
    rows_top = hdr_y + hdr_h + lerp(14, 4, t)

    # scan bar position in row units
    if beat3:
        bar_row = -1
    elif beat2:
        bar_row = 8.432911 * ease((fr - 92) / 86)
    else:
        bar_row = 6.0 * ease((fr - 18) / 57)
    found1 = (not beat2) and fr >= 75
    target_slot = 6 if (beat3 or not beat2) else 9

    # ---- header slab
    d.rectangle([TX0, hdr_y, TX1, hdr_y + hdr_h], fill=(14, 18, 26),
                outline=alpha(WHITE, a * 0.7), width=2)
    if t < 0.7:
        ta = a * (1 - t)
        d.text((TX0 + 12, hdr_y + hdr_h / 2), "TABLE users", font=MONOB(11),
               fill=alpha(WHITE, ta), anchor="lm")
        rows_txt = "10,000,000 ROWS" if beat2 else "1,000 ROWS"
        rc = alpha(RED, pulse) if beat2 else MUTED
        d.text((TX1 - 12, hdr_y + hdr_h / 2), rows_txt, font=MONOB(11),
               fill=alpha(rc, ta), anchor="rm")
    else:
        d.text((TX0 + 12, hdr_y + hdr_h / 2), "TABLE users · 10,000,000 ROWS",
               font=MONO(9), fill=alpha(MUTED, a * t), anchor="lm")

    # ---- column labels (big table only)
    if t < 0.5:
        la = a * (1 - 2 * t)
        d.text((TX0 + 12, hdr_y + hdr_h + 8), "ROWID", font=MONO(8), fill=alpha(MUTED, la), anchor="lm")
        d.text((TX0 + 96, hdr_y + hdr_h + 8), "EMAIL", font=MONO(8), fill=alpha(MUTED, la), anchor="lm")

    # ---- row slabs
    check_col = RED if beat2 else TEAL
    for i in range(NROWS):
        y = rows_top + i * row_h
        is_target = (i == target_slot)
        if beat3:
            rid = TARGET_RID if is_target else i * 1_000_000 + 4213
        elif beat2:
            rid = TARGET_RID if i == 9 else i * 1_000_000 + 4213
        else:
            rid = 417 if i == 6 else 69 * i + 3

        slab_a = a * (0.45 + 0.55 * t) if beat3 else a
        fill = (11, 14, 20)
        d.rectangle([TX0, y, TX1, y + row_h - 2], fill=fill,
                    outline=alpha(DIM, slab_a * 0.7), width=1)
        # checked tint (rows the scan already passed)
        if not beat3 and i < bar_row:
            d.rectangle([TX0, y, TX1, y + row_h - 2], fill=alpha(check_col, a * 0.14))

        if beat3:
            if is_target:
                d.rectangle([TX0, y, TX1, y + row_h - 2], fill=alpha(GREEN, a * 0.14),
                            outline=alpha(GREEN, a * (0.6 + 0.4 * pulse)), width=2)
                d.text((TX0 + 12, y + (row_h - 2) / 2), f"{TARGET_RID:,} · ak@dev.io  ✓",
                       font=MONO(9), fill=alpha(GREEN, a), anchor="lm")
            else:
                d.text((TX0 + 12, y + (row_h - 2) / 2), f"{rid:,}", font=MONO(8),
                       fill=alpha(MUTED, a * 0.6), anchor="lm")
        else:
            email = "ak@dev.io" if is_target else f"user{rid}@mail.io"
            d.text((TX0 + 12, y + (row_h - 2) / 2), str(rid), font=MONO(10),
                   fill=alpha(MUTED, a), anchor="lm")
            if t < 0.6:
                ea = a * (1 - t)
                ecol = GREEN if (is_target and (found1 or beat2)) else WHITE
                d.text((TX0 + 96, y + (row_h - 2) / 2), email, font=MONO(10),
                       fill=alpha(ecol, ea * (0.95 if is_target else 0.7)), anchor="lm")
            if is_target:
                oc = GREEN if found1 else WHITE
                d.rectangle([TX0, y, TX1, y + row_h - 2],
                            outline=alpha(oc, a * (0.9 if found1 else 0.55)), width=2)

    # ---- sequential scan gate bar
    if not beat3:
        sa = a * (1 - t)
        if bar_row >= 0:
            by = rows_top + bar_row * row_h + (row_h - 2) / 2
            col = GREEN if found1 else (RED if beat2 else BLUE)
            d.line([(TX0, by), (TX1, by)], fill=alpha(col, sa), width=3)
            checked = int(bar_row * 1_000_000) if beat2 else int(bar_row)
            track(d, (TX0 + 8, by - 7), "SEQ SCAN ▸", MONO(8), alpha(col, sa), sp=1, anchor="lm")
            lab = f"{checked:,} rows checked" if (beat2 or bar_row > 0) else "starting scan…"
            d.text((TX1 - 8, by - 7), lab, font=MONO(8), fill=alpha(col, sa), anchor="rm")

    # ---- beat 2 opening: table growth alarm tag
    if 90 <= fr <= 132:
        ga = ease((fr - 90) / 5) * (1 - ease((fr - 122) / 10))
        track(d, (W / 2, 486), "⚠ TABLE GREW ×10,000 → 10,000,000 ROWS",
              MONOB(11), alpha(RED, a * ga * pulse), sp=2, anchor="mm")

    # ---- timeout stamp as beat 2 closes
    if 168 <= fr <= 196:
        so = ease((fr - 168) / 6) * (1 - ease((fr - 188) / 8))
        track(d, (W / 2, 668), "✗ QUERY TIMEOUT — 850ms ELAPSED",
              MONOB(16), alpha(RED, a * so * pulse), sp=2, anchor="mm")


def draw_counter_zone(d, fr, a):
    za = a * (1 - ease((fr - 180) / 10))
    if za <= 0.01:
        return
    beat2 = fr >= 90
    if beat2:
        bar_row = 8.432911 * ease((fr - 92) / 86)
        counter, col = int(bar_row * 1_000_000), RED
        denom, fill = "/ 10,000,000", counter / TOTAL_ROWS
        note = "✗ query timeout at 850ms" if fr >= 168 else "scanning… no match found yet"
    else:
        found = fr >= 75
        counter = 6 if found else int(6 * ease((fr - 18) / 57))
        col = TEAL
        denom, fill = "/ 1,000", counter / 1000
        note = "✓ match at row 417 · 0.4ms" if found else "checking rows sequentially…"
    track(d, (90, 816), "ROWS CHECKED", MONOB(11), alpha(col, za), sp=2)
    big = f"{counter:,}"
    d.text((90, 846), big, font=MONOB(30), fill=alpha(col, za), anchor="lm")
    d.text((90 + d.textlength(big, font=MONOB(30)) + 10, 852), denom,
           font=MONOB(11), fill=alpha(MUTED, za), anchor="lm")
    d.rectangle([90, 872, 630, 888], outline=alpha(DIM, za), width=1)
    d.rectangle([90, 872, 90 + 540 * fill, 888], fill=alpha(col, za * 0.8))
    ncol = col if ("✓" in note or "✗" in note) else MUTED
    d.text((90, 898), note, font=SANS(11), fill=alpha(ncol, za), anchor="lm")


def btree_node(d, cx, cy, w, h, cells, col, a, yoff=0.0, lw=2, fsize=13):
    cy += yoff
    if a <= 0.01:
        return
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=6,
                        fill=(10, 14, 20), outline=alpha(col, a), width=lw)
    n = len(cells)
    for j, txt in enumerate(cells):
        if j > 0:
            bx = cx - w / 2 + j * (w / n)
            d.line([(bx, cy - h / 2 + 4), (bx, cy + h / 2 - 4)], fill=alpha(DIM, a * 0.8), width=1)
        d.text((cx - w / 2 + (j + 0.5) * (w / n), cy), txt, font=MONOB(fsize),
               fill=alpha(WHITE, a), anchor="mm")
    for j in range(n + 1):
        px = cx - w / 2 + j * (w / n)
        d.ellipse([px - 2.5, cy + h / 2 - 3, px + 2.5, cy + h / 2 + 2], fill=alpha(col, a * 0.9))


def draw_btree(d, fr, a):
    if fr < 182:
        return
    a_root = ease((fr - 182) / 8)
    a_int  = ease((fr - 187) / 8)
    a_leaf = ease((fr - 192) / 8)
    a_edge = ease((fr - 194) / 8)

    track(d, (W / 2, 478), "idx_users_email · B+TREE (SORTED BY email)",
          MONO(10), alpha(TEAL, a_root), sp=2, anchor="mm")

    # edges first (under nodes)
    if a_edge > 0.01:
        root_x = [ROOT[0] - 75, ROOT[0], ROOT[0] + 75]
        edges = []
        for j, icx in enumerate([i[0] for i in INTERN]):
            edges.append(((root_x[j], ROOT[1] + 22), (icx, 572)))
        for j, (icx, _, _) in enumerate(INTERN):
            for k, lcx in enumerate([LEAVES[2 * j][0], LEAVES[2 * j + 1][0]]):
                edges.append(((icx - 30 + 60 * k, 611), (lcx, 657)))
        # seek path edges glow green once orb has traversed them
        path_done = [fr >= 218, fr >= 236]
        for ei, (p0, p1) in enumerate(edges):
            on_path = (ei == 0 and path_done[0]) or (ei == 3 and path_done[1])
            col = GREEN if on_path else DIM
            d.line([p0, p1], fill=alpha(col, a_edge * (0.95 if on_path else 0.7)),
                   width=3 if on_path else 1)

    btree_node(d, ROOT[0], ROOT[1], ROOT[2], ROOT[3], ROOT[4], TEAL, a * a_root,
               yoff=(1 - a_root) * -12)
    for cx, cy, keys in INTERN:
        hit = (cx == 161 and fr >= 218)
        btree_node(d, cx, cy, 110, 38, keys, GREEN if hit else TEAL, a * a_int,
                   yoff=(1 - a_int) * -12)
    for cx, txt in LEAVES:
        hit = (cx == 110 and fr >= 236)
        btree_node(d, cx, 676, LEAF_W, LEAF_H, [txt], GREEN if hit else TEAL, a * a_leaf,
                   yoff=(1 - a_leaf) * -12, fsize=11)
    d.text((110, 706), "leaves: email → rowid", font=MONO(8), fill=alpha(TEAL_D, a * a_leaf), anchor="mm")

    # page read ticks light up as the orb lands on each node
    for pf, px, py, lab in PAGES:
        if fr >= pf:
            track(d, (px, py), lab, MONO(9), alpha(GREEN, a), sp=1, anchor="lm")

    # seek orb hopping root -> internal -> leaf -> row
    for hs, he, p0, p1 in HOPS:
        if fr < hs:
            break
        ht = ease((fr - hs) / (he - hs))
        ox, oy = lerp(p0[0], p1[0], ht), lerp(p0[1], p1[1], ht)
        if ht < 1.0:
            d.line([p0, (ox, oy)], fill=alpha(GREEN, a * 0.5), width=2)
        elif hs == 240:  # leaf -> row pointer stays as a permanent arrow
            d.line([p0, p1], fill=alpha(GREEN, a * 0.9), width=2)
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            for da in (2.55, -2.55):
                d.line([p1, (p1[0] - 10 * math.cos(ang + da), p1[1] - 10 * math.sin(ang + da))],
                       fill=alpha(GREEN, a * 0.9), width=2)
        if ht < 1.0 or fr <= he + 2:
            d.ellipse([ox - 5, oy - 5, ox + 5, oy + 5], fill=alpha(GREEN, a))
            d.ellipse([ox - 9, oy - 9, ox + 9, oy + 9], outline=alpha(GREEN, a * 0.5), width=1)

    # rowid pointer label + found impact ring
    if 238 <= fr:
        d.text((205, 742), "ROWID PTR ▸", font=MONO(8), fill=alpha(GREEN, a * 0.9), anchor="lm")
    if 254 <= fr <= 274:
        ra = 1 - ease((fr - 254) / 20)
        rr = 8 + (fr - 254) * 1.4
        d.ellipse([188 - rr, 862 - rr, 188 + rr, 862 + rr], outline=alpha(GREEN, a * ra), width=2)

    # beat 3 bottom takeaway line
    if fr >= 200:
        if fr >= 254:
            track(d, (W / 2, 944), "✓ 0.12ms — 3 PAGE READS vs 10,000,000 ROW SCANS",
                  MONOB(11), alpha(GREEN, a), sp=1, anchor="mm")
        else:
            track(d, (W / 2, 944), "INDEX SEEK: ROOT ▸ LEAF ▸ ROWID",
                  MONOB(11), alpha(TEAL, a), sp=1, anchor="mm")


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
    track(d, (W / 2, 192), "SEQUENTIAL SCAN (10M ROWS)  vs  B-TREE INDEX (3 READS)",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    tw1 = d.textlength("DATABASE ", font=SANSB(42))
    tw2 = d.textlength("INDEXING", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 228), "DATABASE ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 228), "INDEXING", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "why one index turns an 850ms query into a 0.12ms lookup",
           font=SANS(14), fill=alpha(BLUE, intro * .95), anchor="mm")

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
        st, stc = "EXECUTION PLAN: INDEX SCAN USING idx_users_email", GREEN
    elif beat2:
        st, stc = "EXECUTION PLAN: SEQ SCAN ON users — DISK I/O SATURATED", RED
    else:
        st, stc = "EXECUTION PLAN: SEQ SCAN ON users", MUTED
    track(d, (W / 2, 390), st, MONOB(10), alpha(stc, a * (pulse if beat2 else 1.0)), sp=1, anchor="mm")

    # ---- Stage
    draw_table(d, fr, a)
    draw_btree(d, fr, a)
    draw_counter_zone(d, fr, a)
    draw_query_pill(d, fr, a)

    # ---- Caption pill + outro footer
    draw_caption_pill(d, fr, CAPTIONS, a)
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "B+TREE · O(LOG N) · ROOT → LEAF → ROWID", MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "POSTGRES  ·  MYSQL  ·  SQL SERVER  ·  COVERING INDEXES", MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base


def render_and_save_frame(args):
    fr, out_dir = args
    img = finish(render(fr), fr)
    img.save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_database_indexing"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    tasks = [(fr, out_dir) for fr in frames]
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, tasks))
    print(f"Rendered Database Indexing frames: {len(frames)}")
