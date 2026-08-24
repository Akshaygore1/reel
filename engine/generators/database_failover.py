#!/usr/bin/env python3
"""
Flagship System Design Reel: Database Failover (Primary -> Synchronous Replica)
Visual Apparatus: dual isometric database racks, a mechanical write-endpoint
switch, a live WAL conveyor, and a three-step failover controller.
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
from diagram import orthogonal_path, point_on_path


CAPTIONS = [
    (0,   "every write lands on PRIMARY and streams WAL to its replica."),
    (60,  "the sync replica replays each committed transaction."),
    (124, "primary dies. 3 missed heartbeats freeze incoming writes."),
    (188, "the controller fences the old primary and promotes the replica."),
    (250, "proxy reroutes. writes recover in 2.8s with zero data loss."),
]

LEFT_CX, RIGHT_CX = 205, 515
RACK_CY, RACK_W, RACK_H, RACK_DEPTH = 650, 210, 178, 24
LEFT_ROUTE = orthogonal_path((260, 500), (LEFT_CX, 549), [(260, 522), (LEFT_CX, 522)])
RIGHT_ROUTE = orthogonal_path((460, 500), (RIGHT_CX, 549), [(460, 522), (RIGHT_CX, 522)])


def draw_route(d, path, col, a, fr, active=False, reverse=False):
    """Orthogonal database route with a restrained glow and moving request orbs."""
    d.line(path, fill=alpha(col, a * 0.15), width=9, joint="curve")
    d.line(path, fill=alpha(col, a * 0.72), width=3, joint="curve")
    if not active:
        return
    for i in range(3):
        progress = ((fr * 0.035) + i / 3) % 1.0
        if reverse:
            progress = 1.0 - progress
        (x, y), _ = point_on_path(path, progress)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=alpha(col, a))
        d.ellipse([x - 8, y - 8, x + 8, y + 8], outline=alpha(col, a * 0.35), width=1)


def draw_proxy_switch(d, fr, a):
    """Mechanical endpoint selector that visibly flips from primary to replica."""
    beat2, beat3 = fr >= 90, fr >= 180
    switch_t = ease((fr - 206) / 30)
    col = GREEN if (beat3 and switch_t > 0.72) else (RED if beat2 and not beat3 else BLUE)

    d.rounded_rectangle([120, 410, 600, 500], radius=12, fill=(12, 16, 24),
                        outline=alpha(col, a * 0.78), width=2)
    d.line([(138, 412), (582, 412)], fill=alpha(col, a), width=3)
    track(d, (W / 2, 430), "DATABASE PROXY · WRITE ENDPOINT", MONOB(11),
          alpha(WHITE, a), sp=2, anchor="mm")
    status = ("ROUTING TO NEW PRIMARY" if beat3 and switch_t > 0.72 else
              "FAILOVER IN PROGRESS" if beat2 else "ROUTING TO PRIMARY")
    status_col = GREEN if beat3 and switch_t > 0.72 else (RED if beat2 else MUTED)
    d.text((W / 2, 451), status, font=MONO(10), fill=alpha(status_col, a), anchor="mm")

    d.line([(252, 478), (468, 478)], fill=alpha(DIM, a), width=2)
    d.ellipse([250, 468, 270, 488], fill=(8, 12, 18), outline=alpha(TEAL, a), width=2)
    d.ellipse([450, 468, 470, 488], fill=(8, 12, 18), outline=alpha(GREEN if beat3 else BLUE, a), width=2)
    d.text((230, 478), "P", font=MONOB(9), fill=alpha(MUTED, a), anchor="rm")
    d.text((490, 478), "R", font=MONOB(9), fill=alpha(MUTED, a), anchor="lm")

    lever_x = lerp(260, 460, switch_t)
    lever_col = GREEN if switch_t > 0.72 else (RED if beat2 else TEAL)
    if beat2 and not beat3:
        lever_x += math.sin(fr * 0.9) * 3
    d.line([(360, 463), (lever_x, 478)], fill=alpha(lever_col, a), width=5)
    d.ellipse([351, 454, 369, 472], fill=(18, 24, 34), outline=alpha(WHITE, a), width=2)
    d.ellipse([lever_x - 6, 472, lever_x + 6, 484], fill=alpha(lever_col, a))

    for px in (260, 460):
        d.ellipse([px - 5, 495, px + 5, 505], fill=BG, outline=alpha(col, a), width=2)


def draw_isometric_db_rack(d, cx, cy, role, state, fr, a):
    """Dual-rack silhouette matching the SQL injection reel's physical grammar."""
    if state == "dead":
        col, face = RED, (30, 13, 18)
    elif state == "fenced":
        col, face = RED, (18, 14, 20)
    elif state == "standby":
        col, face = BLUE, (12, 18, 28)
    elif state == "promoting":
        col, face = AMBER, (28, 21, 12)
    elif state == "new_primary":
        col, face = GREEN, (10, 25, 21)
    else:
        col, face = TEAL, (12, 23, 24)

    x0, y0 = cx - RACK_W / 2, cy - RACK_H / 2
    x1, y1 = cx + RACK_W / 2, cy + RACK_H / 2
    top = [(x0, y0), (x0 + RACK_DEPTH, y0 - RACK_DEPTH * 0.5),
           (x1 + RACK_DEPTH, y0 - RACK_DEPTH * 0.5), (x1, y0)]
    side = [(x1, y0), (x1 + RACK_DEPTH, y0 - RACK_DEPTH * 0.5),
            (x1 + RACK_DEPTH, y1 - RACK_DEPTH * 0.5), (x1, y1)]
    d.rectangle([x0, y0, x1, y1], fill=face, outline=alpha(col, a), width=2)
    d.polygon(top, fill=(22, 29, 39) if state not in ("dead", "fenced") else (35, 17, 23),
              outline=alpha(col, a * 0.72))
    d.polygon(side, fill=(16, 21, 31) if state not in ("dead", "fenced") else (27, 13, 19),
              outline=alpha(col, a * 0.72))

    pill_w = min(RACK_W - 24, d.textlength(role, font=MONOB(10)) + 28)
    d.rounded_rectangle([cx - pill_w / 2, y0 + 10, cx + pill_w / 2, y0 + 32], radius=11,
                        fill=(8, 12, 18), outline=alpha(col, a), width=1)
    d.ellipse([cx - pill_w / 2 + 10, y0 + 18, cx - pill_w / 2 + 16, y0 + 24],
              fill=alpha(col, a))
    d.text((cx + 5, y0 + 21), role, font=MONOB(10), fill=alpha(WHITE, a), anchor="mm")

    slot_top, slot_h = y0 + 44, 27
    for slot in range(4):
        sy = slot_top + slot * slot_h
        d.rounded_rectangle([x0 + 10, sy, x1 - 10, sy + 21], radius=3,
                            fill=(7, 10, 15), outline=alpha(col, a * 0.48), width=1)
        for led in range(4):
            lx = x0 + 22 + led * 14
            if state in ("dead", "fenced"):
                led_col = RED if (state == "dead" and led == 0) else DIM
                lit = state == "dead" and ((fr + slot * 3) % 10 < 5)
            else:
                led_col = GREEN if led < 3 else AMBER
                lit = (fr + slot * 4 + led * 3) % 12 < 7
            d.ellipse([lx - 2, sy + 8, lx + 2, sy + 12],
                      fill=alpha(led_col if lit else DIM, a))
        for vx in range(int(cx), int(x1 - 18), 8):
            d.line([(vx, sy + 5), (vx, sy + 16)], fill=alpha(DIM, a * 0.55), width=1)

    if state == "dead":
        flash = 0.45 + 0.55 * (math.sin(fr * 0.7) ** 2)
        d.line([(cx - 38, cy - 20), (cx + 38, cy + 45)], fill=alpha(RED, a * flash), width=6)
        d.line([(cx + 38, cy - 20), (cx - 38, cy + 45)], fill=alpha(RED, a * flash), width=6)
    elif state == "fenced":
        d.rectangle([cx - 70, cy + 8, cx + 70, cy + 39], fill=(28, 12, 17),
                    outline=alpha(RED, a), width=2)
        track(d, (cx, cy + 23), "FENCED", MONOB(12), alpha(RED, a), sp=2, anchor="mm")
    elif state == "promoting":
        arc_end = int(lerp(-90, 270, ease((fr - 180) / 30)))
        d.arc([cx - 42, cy - 14, cx + 42, cy + 70], -90, arc_end,
              fill=alpha(AMBER, a), width=5)
        d.text((cx, cy + 28), "PROMOTE", font=MONOB(11), fill=alpha(AMBER, a), anchor="mm")

    d.ellipse([cx - 6, y1 - 9, cx + 6, y1 + 3], fill=BG, outline=alpha(col, a), width=2)


def draw_wal_bus(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    y = 812
    if beat3:
        col, label = GREEN, "WAL CAUGHT UP · LAST LSN 84A7 · RPO 0s"
    elif beat2:
        col, label = AMBER, "WAL STREAM FROZEN · LAST ACK 84A7"
    else:
        col, label = TEAL, "SYNCHRONOUS WAL STREAM · COMMIT ACK"

    d.line([(LEFT_CX, 739), (LEFT_CX, y), (RIGHT_CX, y), (RIGHT_CX, 739)],
           fill=alpha(col, a * 0.18), width=9, joint="curve")
    d.line([(LEFT_CX, 739), (LEFT_CX, y), (RIGHT_CX, y), (RIGHT_CX, 739)],
           fill=alpha(col, a * 0.72), width=3, joint="curve")

    if not beat2:
        for i in range(4):
            t = ((fr * 0.025) + i / 4) % 1.0
            x = lerp(LEFT_CX + 8, RIGHT_CX - 8, t)
            d.rounded_rectangle([x - 12, y - 7, x + 12, y + 7], radius=3,
                                fill=(8, 14, 18), outline=alpha(col, a), width=1)
            d.text((x, y), "W", font=MONOB(7), fill=alpha(WHITE, a), anchor="mm")
    elif not beat3:
        frozen_x = 404
        d.rounded_rectangle([frozen_x - 14, y - 8, frozen_x + 14, y + 8], radius=3,
                            fill=(24, 18, 10), outline=alpha(AMBER, a), width=2)
        d.text((frozen_x, y), "84A7", font=MONOB(7), fill=alpha(AMBER, a), anchor="mm")

    d.text((W / 2, 835), label, font=MONOB(9), fill=alpha(col, a), anchor="mm")


def draw_failover_controller(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    d.rounded_rectangle([95, 854, 625, 952], radius=12, fill=(11, 15, 22),
                        outline=alpha(GREEN if beat3 else (RED if beat2 else BLUE), a * 0.58), width=1)
    track(d, (W / 2, 870), "FAILOVER CONTROLLER · QUORUM HEALTH CHECK", MONOB(9),
          alpha(MUTED, a), sp=2, anchor="mm")

    xs = [258, 360, 462]
    d.line([(xs[0], 904), (xs[-1], 904)], fill=alpha(DIM, a), width=2)
    if beat3:
        labels, thresholds, col = ["FENCE", "PROMOTE", "ROUTE"], [184, 204, 224], GREEN
        status = "NEW PRIMARY ELECTED · WRITE ENDPOINT RESTORED" if fr >= 224 else "SAFE PROMOTION IN PROGRESS"
    elif beat2:
        labels, thresholds, col = ["MISS 1", "MISS 2", "MISS 3"], [98, 110, 122], RED
        misses = sum(fr >= threshold for threshold in thresholds)
        status = f"PRIMARY HEARTBEAT LOST · {misses}/3 MISSED"
    else:
        labels, thresholds, col = ["HB 1", "HB 2", "HB 3"], [0, 0, 0], TEAL
        status = "PRIMARY HEALTHY · REPLICA READY"

    for x, label, threshold in zip(xs, labels, thresholds):
        active = fr >= threshold
        node_col = col if active else DIM
        glow = 0.55 + 0.45 * (math.sin(fr * 0.38 + x) ** 2)
        d.ellipse([x - 20, 884, x + 20, 924], fill=(8, 12, 18),
                  outline=alpha(node_col, a * (glow if active else 0.5)), width=3 if active else 1)
        d.text((x, 904), label, font=MONOB(8), fill=alpha(node_col, a), anchor="mm")
    d.text((W / 2, 938), status, font=MONOB(9), fill=alpha(col, a), anchor="mm")


def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag = ease((fr - 8) / 18)
    a = diag
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    # ---- Header: deliberately mirrors the successful SQL injection composition.
    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 192), "PRIMARY DATABASE  vs  SYNCHRONOUS REPLICA",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    tw1 = d.textlength("DATABASE ", font=SANSB(42))
    tw2 = d.textlength("FAILOVER", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2) / 2
    d.text((sx, 228), "DATABASE ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 228), "FAILOVER", font=SANSB(42),
           fill=alpha(GREEN if beat3 else (RED if beat2 else TEAL), intro), anchor="lm")
    d.text((W / 2, 264), "your primary database just died. now what?",
           font=SANS(14), fill=alpha(BLUE, intro * 0.95), anchor="mm")

    if diag <= 0.01:
        return base

    # ---- Quantified telemetry follows the same three-beat state machine.
    if beat3:
        recovered = int(lerp(0, 100, ease((fr - 192) / 36)))
        m1_label, m1_val, m1_col = "WRITE SUCCESS", f"{recovered}%", GREEN
        m2_label, m2_val, m2_col = "RECOVERY TIME", "2.8s", GREEN
    elif beat2:
        queued = int(lerp(0, 12_480, ease((fr - 92) / 78)))
        m1_label, m1_val, m1_col = "WRITE SUCCESS", "0%", RED
        m2_label, m2_val, m2_col = "WRITES QUEUED", f"{queued:,}", RED
    else:
        m1_label, m1_val, m1_col = "WRITE SUCCESS", "100%", GREEN
        m2_label, m2_val, m2_col = "REPLICA LAG", "12ms", TEAL
    draw_telemetry_hud(d, m1_label, m1_val, m2_label, m2_val, a,
                       m1_col=m1_col, m2_col=m2_col)

    if beat3:
        status = "FENCED OLD PRIMARY → PROMOTE REPLICA → FLIP ENDPOINT"
        status_col = GREEN
    elif beat2:
        status = "PRIMARY UNREACHABLE · WRITE TRAFFIC FROZEN"
        status_col = RED
    else:
        status = "PRIMARY ACCEPTS WRITES · REPLICA REPLAYS WAL"
        status_col = MUTED
    track(d, (W / 2, 390), status, MONOB(10),
          alpha(status_col, a * (pulse if beat2 and not beat3 else 1.0)), sp=1, anchor="mm")

    # ---- Connectors first, then the physical endpoint switch and racks.
    left_active = not beat3
    right_active = beat3 and fr >= 218
    left_col = RED if beat2 and not beat3 else (DIM if beat3 else BLUE)
    right_col = GREEN if beat3 else DIM
    draw_route(d, LEFT_ROUTE, left_col, a, fr, active=left_active and not beat2)
    draw_route(d, RIGHT_ROUTE, right_col, a, fr, active=right_active)

    if beat2 and not beat3:
        bx, by = 232, 522
        d.line([(bx - 9, by - 9), (bx + 9, by + 9)], fill=alpha(RED, a * pulse), width=4)
        d.line([(bx + 9, by - 9), (bx - 9, by + 9)], fill=alpha(RED, a * pulse), width=4)
        for i in range(5):
            qx = 184 + i * 34
            d.rounded_rectangle([qx, 485, qx + 22, 495], radius=3,
                                fill=alpha(AMBER, a * (0.45 + 0.1 * i)), outline=alpha(RED, a), width=1)

    draw_proxy_switch(d, fr, a)

    if beat3:
        left_role, left_state = "OLD PRIMARY", "fenced"
        right_role = "NEW PRIMARY" if fr >= 210 else "PROMOTING"
        right_state = "new_primary" if fr >= 210 else "promoting"
        left_sub, right_sub = "FENCED · SPLIT-BRAIN SAFE", "READ/WRITE · ACTIVE" if fr >= 210 else "REPLAYING LAST WAL"
    elif beat2:
        left_role, left_state = "PRIMARY", "dead"
        right_role, right_state = "SYNC REPLICA", "standby"
        left_sub, right_sub = "OFFLINE · NO HEARTBEAT", "READY · LAST LSN 84A7"
    else:
        left_role, left_state = "PRIMARY", "primary"
        right_role, right_state = "SYNC REPLICA", "standby"
        left_sub, right_sub = "READ/WRITE · ACTIVE", "READ ONLY · WAL REPLAY"

    draw_wal_bus(d, fr, a)
    draw_isometric_db_rack(d, LEFT_CX, RACK_CY, left_role, left_state, fr, a)
    draw_isometric_db_rack(d, RIGHT_CX, RACK_CY, right_role, right_state, fr + 11, a)
    d.text((LEFT_CX, 764), left_sub, font=MONOB(9),
           fill=alpha(RED if left_state in ("dead", "fenced") else TEAL, a), anchor="mm")
    d.text((RIGHT_CX, 764), right_sub, font=MONOB(9),
           fill=alpha(GREEN if right_state == "new_primary" else BLUE, a), anchor="mm")

    if 92 <= fr <= 148:
        alarm_a = ease((fr - 92) / 7) * (1 - ease((fr - 138) / 10))
        missed = sum(fr >= threshold for threshold in (98, 110, 122))
        track(d, (W / 2, 535), f"⚠ PRIMARY HEARTBEAT LOST · {missed}/3 MISSED",
              MONOB(10), alpha(RED, a * alarm_a * pulse), sp=2, anchor="mm")
    if 178 <= fr <= 212:
        stamp_a = ease((fr - 178) / 7) * (1 - ease((fr - 204) / 8))
        track(d, (W / 2, 535), "FENCE CONFIRMED · SAFE TO PROMOTE",
              MONOB(10), alpha(GREEN, a * stamp_a), sp=2, anchor="mm")

    draw_failover_controller(d, fr, a)
    draw_caption_pill(d, fr, CAPTIONS, a)

    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "RTO 2.8s · RPO 0s · SYNCHRONOUS FAILOVER",
              MONOB(11), alpha(GREEN, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "POSTGRES  ·  MYSQL  ·  AURORA  ·  PATRONI",
              MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base


def render_and_save_frame(args):
    fr, out_dir = args
    finish(render(fr), fr).save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_database_failover"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, [(fr, out_dir) for fr in frames]))
    print(f"Rendered Database Failover frames: {len(frames)}")
