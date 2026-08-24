#!/usr/bin/env python3
"""
Flagship System Design Reel: Redis Pub/Sub vs Kafka
Visual Apparatus: an ephemeral radio broadcast tower that drops messages for an
offline subscriber versus a retained Kafka commit-log conveyor with a resumable
consumer offset.
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
    (0,   "the same event is published into Redis Pub/Sub and Kafka."),
    (60,  "online consumers receive it from both systems."),
    (124, "consumer offline: Redis drops #1042; Kafka keeps it in the log."),
    (188, "Redis has no offset. the missed event cannot be replayed."),
    (250, "Kafka resumes at offset 1042 and processes the retained event."),
]

LEFT_ROUTE = orthogonal_path((270, 470), (190, 500), [(270, 486), (190, 486)])
RIGHT_ROUTE = orthogonal_path((450, 470), (530, 500), [(450, 486), (530, 486)])
SUBSCRIBERS = [(90, "SUB A"), (190, "SUB B"), (290, "SUB C")]
LOG_OFFSETS = [1039, 1040, 1041, 1042]
LOG_XS = [410, 472, 534, 596]


def draw_event_route(d, path, col, fr, a, phase=0.0):
    """Orthogonal branch with a labelled event packet."""
    d.line(path, fill=alpha(col, a * 0.14), width=9, joint="curve")
    d.line(path, fill=alpha(col, a * 0.72), width=3, joint="curve")
    progress = (fr * 0.025 + phase) % 1.0
    (x, y), _ = point_on_path(path, progress)
    d.rounded_rectangle([x - 18, y - 9, x + 18, y + 9], radius=5,
                        fill=(8, 12, 18), outline=alpha(col, a), width=1)
    d.text((x, y), "1042" if fr >= 90 else "1041", font=MONOB(7),
           fill=alpha(WHITE, a), anchor="mm")


def draw_publisher(d, fr, a):
    beat2 = fr >= 90
    col = RED if 90 <= fr < 180 else BLUE
    event_id = "#1042" if beat2 else "#1041"
    d.rounded_rectangle([175, 410, 545, 470], radius=10, fill=(12, 16, 24),
                        outline=alpha(col, a * 0.85), width=2)
    d.line([(190, 412), (530, 412)], fill=alpha(col, a), width=3)
    track(d, (W / 2, 430), "EVENT PRODUCER", MONOB(10), alpha(MUTED, a), sp=2, anchor="mm")
    d.text((W / 2, 452), f"PUBLISH order.paid · {event_id}", font=MONOB(13),
           fill=alpha(WHITE, a), anchor="mm")
    for px in (270, 450):
        d.ellipse([px - 5, 465, px + 5, 475], fill=BG, outline=alpha(col, a), width=2)


def draw_lane_shell(d, bounds, title, subtitle, col, a):
    x0, y0, x1, y1 = bounds
    d.rounded_rectangle(bounds, radius=14, fill=(10, 14, 21),
                        outline=alpha(col, a * 0.52), width=1)
    d.line([(x0 + 12, y0 + 2), (x1 - 12, y0 + 2)], fill=alpha(col, a), width=3)
    d.rounded_rectangle([x0 + 20, y0 + 14, x1 - 20, y0 + 48], radius=10,
                        fill=(13, 18, 26), outline=alpha(col, a * 0.72), width=1)
    d.text(((x0 + x1) / 2, y0 + 27), title, font=MONOB(12), fill=alpha(WHITE, a), anchor="mm")
    d.text(((x0 + x1) / 2, y0 + 42), subtitle, font=MONO(8), fill=alpha(col, a), anchor="mm")


def draw_broadcast_tower(d, fr, a, col):
    """Redis channel as a physical radio transmitter with live wave rings."""
    cx, mast_top, mast_bottom = 190, 590, 667
    d.line([(cx, mast_top + 12), (cx, mast_bottom)], fill=alpha(col, a), width=4)
    d.line([(cx, mast_bottom), (cx - 28, mast_bottom + 28)], fill=alpha(col, a * 0.8), width=3)
    d.line([(cx, mast_bottom), (cx + 28, mast_bottom + 28)], fill=alpha(col, a * 0.8), width=3)
    d.line([(cx - 28, mast_bottom + 28), (cx + 28, mast_bottom + 28)], fill=alpha(col, a * 0.8), width=2)
    d.ellipse([cx - 8, mast_top + 2, cx + 8, mast_top + 18], fill=(9, 13, 19),
              outline=alpha(col, a), width=2)
    d.ellipse([cx - 3, mast_top + 7, cx + 3, mast_top + 13], fill=alpha(col, a))

    wave = (fr * 0.06) % 1.0
    for i in range(3):
        p = (wave + i / 3) % 1.0
        radius = 14 + 34 * p
        wa = (1 - p) * a * 0.72
        d.arc([cx - radius, mast_top + 10 - radius, cx + radius, mast_top + 10 + radius],
              205, 335, fill=alpha(col, wa), width=2)
    track(d, (cx, 570), "CHANNEL: orders", MONOB(9), alpha(col, a), sp=1, anchor="mm")


def draw_subscriber(d, x, y, label, state, fr, a):
    if state == "offline":
        col, status = RED, "OFFLINE"
    elif state == "gap":
        col, status = AMBER, "ONLINE · GAP"
    else:
        col, status = GREEN, "LIVE"
    pulse = 0.58 + 0.42 * (math.sin(fr * 0.38 + x) ** 2)
    d.ellipse([x - 24, y - 24, x + 24, y + 24], fill=(8, 12, 18),
              outline=alpha(col, a * pulse), width=3 if state != "offline" else 2)
    d.line([(x, y - 24), (x, y - 38)], fill=alpha(col, a), width=2)
    d.ellipse([x - 3, y - 42, x + 3, y - 36], fill=alpha(col, a))
    d.text((x, y - 3), label, font=MONOB(8), fill=alpha(WHITE, a), anchor="mm")
    d.text((x, y + 12), status, font=MONO(7), fill=alpha(col, a), anchor="mm")
    if state == "offline":
        d.line([(x - 15, y - 15), (x + 15, y + 15)], fill=alpha(RED, a), width=3)
        d.line([(x + 15, y - 15), (x - 15, y + 15)], fill=alpha(RED, a), width=3)


def draw_redis_lane(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    reconnected = fr >= 204
    lane_col = RED if beat2 else AMBER
    draw_lane_shell(d, (40, 500, 340, 950), "REDIS PUB/SUB", "EPHEMERAL BROADCAST CHANNEL", lane_col, a)
    draw_broadcast_tower(d, fr, a, AMBER if not beat2 else RED)

    hub = (190, 675)
    for idx, (x, label) in enumerate(SUBSCRIBERS):
        target = idx == 2
        if target and beat3 and reconnected:
            state = "gap"
        elif target and beat2:
            state = "offline"
        else:
            state = "online"
        path_col = RED if state == "offline" else (AMBER if state == "gap" else GREEN)
        d.line([hub, (x, 699)], fill=alpha(path_col, a * (0.35 if state == "offline" else 0.66)), width=2)
        if state == "online":
            p = (fr * 0.035 + idx * 0.27) % 1.0
            px, py = lerp(hub[0], x, p), lerp(hub[1], 699, p)
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=alpha(GREEN, a))
        draw_subscriber(d, x, 730, label, state, fr, a)

    if beat2 and not beat3:
        drop_t = ease((fr - 96) / 55)
        if drop_t < 0.58:
            p = drop_t / 0.58
            ox, oy = lerp(190, 290, p), lerp(675, 700, p)
        else:
            p = (drop_t - 0.58) / 0.42
            ox, oy = 290, lerp(700, 820, p)
        d.ellipse([ox - 6, oy - 6, ox + 6, oy + 6], fill=alpha(RED, a))
        d.ellipse([ox - 11, oy - 11, ox + 11, oy + 11], outline=alpha(RED, a * 0.45), width=1)
        if drop_t > 0.82:
            rr = 8 + 20 * (drop_t - 0.82) / 0.18
            d.ellipse([290 - rr, 820 - rr, 290 + rr, 820 + rr],
                      outline=alpha(RED, a * (1 - drop_t)), width=2)

    d.line([(62, 806), (318, 806)], fill=alpha(DIM, a), width=1)
    if beat3:
        redis_status, status_col = "NO OFFSET · #1042 CANNOT REPLAY", RED
        d.rounded_rectangle([230, 786, 326, 816], radius=8, fill=(25, 14, 13),
                            outline=alpha(AMBER, a), width=1)
        d.text((278, 801), "GAP: #1042", font=MONOB(8), fill=alpha(AMBER, a), anchor="mm")
    elif beat2:
        redis_status, status_col = "NO BUFFER · #1042 VANISHED", RED
        d.line([(257, 812), (323, 812)], fill=alpha(RED, a), width=3)
        d.line([(269, 822), (311, 822)], fill=alpha(RED, a * 0.65), width=2)
        d.text((290, 840), "NO BUFFER", font=MONOB(9), fill=alpha(RED, a), anchor="mm")
    else:
        redis_status, status_col = "3 LIVE SUBSCRIBERS · INSTANT FAN-OUT", GREEN

    track(d, (190, 868), "DELIVERY STATE", MONOB(9), alpha(MUTED, a), sp=2, anchor="mm")
    d.text((190, 891), redis_status, font=MONOB(8), fill=alpha(status_col, a), anchor="mm")
    d.text((190, 916), "PERSISTENCE: NONE  ·  REPLAY: NONE", font=MONO(8),
           fill=alpha(RED if beat2 else MUTED, a), anchor="mm")
    d.text((190, 936), "BEST FOR: TRANSIENT LIVE SIGNALS", font=MONOB(8),
           fill=alpha(AMBER, a), anchor="mm")


def draw_log_cell(d, x, y, offset, present, highlighted, fr, a):
    col = GREEN if highlighted else (TEAL if present else DIM)
    fill = (11, 22, 22) if highlighted else (12, 17, 24)
    d.rounded_rectangle([x, y, x + 54, y + 66], radius=5, fill=fill,
                        outline=alpha(col, a * (1.0 if highlighted else 0.62)), width=2 if highlighted else 1)
    d.text((x + 27, y + 14), f"off:{offset}", font=MONO(7), fill=alpha(MUTED, a), anchor="mm")
    if present:
        d.rounded_rectangle([x + 8, y + 25, x + 46, y + 51], radius=4,
                            fill=(8, 14, 18), outline=alpha(col, a), width=1)
        d.text((x + 27, y + 38), "PAID", font=MONOB(8), fill=alpha(WHITE, a), anchor="mm")
    else:
        d.text((x + 27, y + 38), "EMPTY", font=MONO(7), fill=alpha(DIM, a), anchor="mm")
    d.ellipse([x + 22, y + 56, x + 32, y + 66], fill=(8, 12, 18), outline=alpha(col, a), width=1)


def draw_kafka_consumer(d, fr, a, state):
    if state == "offline":
        col, status = RED, "OFFLINE · LAG 1"
    elif state == "replaying":
        col, status = GREEN, "REPLAYING #1042"
    else:
        col, status = TEAL, "ONLINE · CAUGHT UP"
    x0, y0, x1, y1 = 420, 748, 640, 817
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=(12, 16, 24),
                        outline=alpha(col, a), width=2)
    d.ellipse([x0 + 14, y0 + 15, x0 + 50, y0 + 51], fill=(8, 12, 18),
              outline=alpha(col, a), width=2)
    d.ellipse([x0 + 25, y0 + 26, x0 + 39, y0 + 40], outline=alpha(col, a), width=2)
    for k in range(4):
        ang = fr * 0.06 + k * math.pi / 2
        d.line([(x0 + 32, y0 + 33), (x0 + 32 + 14 * math.cos(ang), y0 + 33 + 14 * math.sin(ang))],
               fill=alpha(col, a * 0.65), width=1)
    d.text((x0 + 64, y0 + 24), "CONSUMER GROUP", font=MONOB(9), fill=alpha(MUTED, a), anchor="lm")
    d.text((x0 + 64, y0 + 43), "payments-cg", font=MONOB(11), fill=alpha(WHITE, a), anchor="lm")
    d.text((x0 + 64, y0 + 59), status, font=MONO(8), fill=alpha(col, a), anchor="lm")
    if state == "offline":
        d.line([(x0 + 19, y0 + 20), (x0 + 45, y0 + 46)], fill=alpha(RED, a), width=3)
        d.line([(x0 + 45, y0 + 20), (x0 + 19, y0 + 46)], fill=alpha(RED, a), width=3)


def draw_kafka_lane(d, fr, a):
    beat2, beat3 = fr >= 90, fr >= 180
    replayed = fr >= 224
    draw_lane_shell(d, (380, 500, 680, 950), "KAFKA", "DURABLE PARTITIONED EVENT LOG", TEAL if not beat2 else GREEN, a)

    track(d, (530, 570), "TOPIC orders · PARTITION 0", MONOB(9), alpha(TEAL, a), sp=1, anchor="mm")
    d.line([(400, 590), (660, 590)], fill=alpha(TEAL, a * 0.7), width=3)
    d.line([(400, 678), (660, 678)], fill=alpha(TEAL, a * 0.7), width=3)
    for i, (x, offset) in enumerate(zip(LOG_XS, LOG_OFFSETS)):
        present = offset < 1042 or beat2
        highlighted = (offset == 1041 and not beat2) or (offset == 1042 and beat2)
        draw_log_cell(d, x, 600, offset, present, highlighted, fr, a)
    for gx in (404, 656):
        d.ellipse([gx - 8, 670, gx + 8, 686], fill=(9, 13, 19), outline=alpha(TEAL, a), width=2)
        d.ellipse([gx - 3, 675, gx + 3, 681], fill=alpha(TEAL, a))

    target_x = LOG_XS[2] + 27 if not beat2 else LOG_XS[3] + 27
    if not beat2:
        d.line([(target_x, 666), (target_x, 714), (530, 714), (530, 748)],
               fill=alpha(TEAL, a * 0.75), width=2)
        p = (fr * 0.035) % 1.0
        if p < 0.5:
            ox, oy = target_x, lerp(666, 714, p * 2)
        else:
            ox, oy = lerp(target_x, 530, (p - 0.5) * 2), lerp(714, 748, (p - 0.5) * 2)
        d.ellipse([ox - 4, oy - 4, ox + 4, oy + 4], fill=alpha(TEAL, a))
    elif beat3:
        connector_a = ease((fr - 190) / 14)
        d.line([(target_x, 666), (target_x, 714), (530, 714), (530, 748)],
               fill=alpha(GREEN, a * connector_a), width=3)
        if 196 <= fr <= 228:
            p = ease((fr - 196) / 32)
            if p < 0.5:
                ox, oy = target_x, lerp(666, 714, p * 2)
            else:
                ox, oy = lerp(target_x, 530, (p - 0.5) * 2), lerp(714, 748, (p - 0.5) * 2)
            d.ellipse([ox - 6, oy - 6, ox + 6, oy + 6], fill=alpha(GREEN, a))
            d.ellipse([ox - 10, oy - 10, ox + 10, oy + 10], outline=alpha(GREEN, a * 0.45), width=1)

    consumer_state = "replaying" if beat3 else ("offline" if beat2 else "online")
    draw_kafka_consumer(d, fr, a, consumer_state)

    if beat3:
        offset_text, offset_col = ("COMMITTED OFFSET: 1042 ✓", GREEN) if replayed else ("RESUME FROM OFFSET: 1042", AMBER)
        replay_text = "#1042 REPLAYED FROM RETAINED LOG" if replayed else "#1042 STILL RETAINED · LAG 1"
    elif beat2:
        offset_text, offset_col = "COMMITTED OFFSET: 1041", AMBER
        replay_text = "#1042 RETAINED · CONSUMER LAG 1"
    else:
        offset_text, offset_col = "COMMITTED OFFSET: 1041", TEAL
        replay_text = "LOG CAUGHT UP · CONSUMER LAG 0"

    d.rounded_rectangle([410, 836, 650, 864], radius=8, fill=(8, 14, 18),
                        outline=alpha(offset_col, a), width=1)
    d.text((530, 850), offset_text, font=MONOB(9), fill=alpha(offset_col, a), anchor="mm")
    d.text((530, 889), replay_text, font=MONOB(8), fill=alpha(offset_col, a), anchor="mm")
    d.text((530, 916), "RETENTION: CONFIGURED  ·  REPLAY: YES", font=MONO(8),
           fill=alpha(GREEN, a), anchor="mm")
    d.text((530, 936), "BEST FOR: DURABLE EVENT WORKFLOWS", font=MONOB(8),
           fill=alpha(TEAL, a), anchor="mm")


def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)
    intro = ease(fr / 14)
    diag = ease((fr - 8) / 18)
    a = diag
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    # ---- Header
    d.text((W / 2, 160), "@buildebugship", font=MONOB(13), fill=alpha(RED, intro), anchor="mm")
    track(d, (W / 2, 192), "EPHEMERAL FAN-OUT  vs  DURABLE EVENT LOG",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")
    tw1 = d.textlength("REDIS ", font=SANSB(42))
    tw2 = d.textlength("vs ", font=SANSB(30))
    tw3 = d.textlength("KAFKA", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2 + tw3) / 2
    d.text((sx, 228), "REDIS ", font=SANSB(42), fill=alpha(AMBER, intro), anchor="lm")
    d.text((sx + tw1, 230), "vs ", font=SANSB(30), fill=alpha(DIM, intro), anchor="lm")
    d.text((sx + tw1 + tw2, 228), "KAFKA", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")
    d.text((W / 2, 264), "when a consumer disconnects, only one system can replay",
           font=SANS(14), fill=alpha(BLUE, intro * 0.95), anchor="mm")

    if diag <= 0.01:
        return base

    # ---- Telemetry exposes semantics instead of misleading benchmark claims.
    if beat3:
        l_lab, l_val, l_col = "REDIS REPLAY", "NONE", RED
        if fr >= 224:
            r_lab, r_val, r_col = "KAFKA REPLAY", "#1042 ✓", GREEN
        else:
            r_lab, r_val, r_col = "KAFKA REPLAY", "RESUMING", AMBER
    elif beat2:
        l_lab, l_val, l_col = "REDIS MISSED", "#1042 LOST", RED
        r_lab, r_val, r_col = "KAFKA LAG", "1 RETAINED", GREEN
    else:
        l_lab, l_val, l_col = "LIVE SUBSCRIBERS", "3/3 ONLINE", AMBER
        r_lab, r_val, r_col = "KAFKA OFFSET", "1041 ACKED", TEAL
    draw_telemetry_hud(d, l_lab, l_val, r_lab, r_val, a, m1_col=l_col, m2_col=r_col)

    if beat3:
        status, status_col = "REDIS HAS NO HISTORY · KAFKA RESUMES FROM OFFSET", GREEN
    elif beat2:
        status, status_col = "CONSUMER OFFLINE · DELIVERY SEMANTICS DIVERGE", RED
    else:
        status, status_col = "LIVE DELIVERY · ALL CONSUMERS ONLINE", MUTED
    track(d, (W / 2, 390), status, MONOB(10),
          alpha(status_col, a * (pulse if beat2 and not beat3 else 1.0)), sp=1, anchor="mm")

    # ---- Shared publisher branches into two deliberately different machines.
    route_col = RED if 90 <= fr < 180 else BLUE
    draw_event_route(d, LEFT_ROUTE, route_col, fr, a, phase=0.0)
    draw_event_route(d, RIGHT_ROUTE, TEAL if not beat2 else GREEN, fr, a, phase=0.42)
    draw_publisher(d, fr, a)
    draw_redis_lane(d, fr, a)
    draw_kafka_lane(d, fr, a)

    if 90 <= fr <= 140:
        alert_a = ease((fr - 90) / 6) * (1 - ease((fr - 130) / 10))
        track(d, (W / 2, 486), "⚠ CONSUMER DISCONNECTED · EVENT #1042 PUBLISHED",
              MONOB(9), alpha(RED, a * alert_a * pulse), sp=1, anchor="mm")

    draw_caption_pill(d, fr, CAPTIONS, a)
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "LIVE FAN-OUT  vs  DURABLE REPLAY",
              MONOB(11), alpha(TEAL, o), sp=3, anchor="mm")
        track(d, (W / 2, 1112), "PRESENCE · NOTIFICATIONS  |  ORDERS · PAYMENTS · CDC",
              MONO(9), alpha(DIM, o), sp=1, anchor="mm")
    return base


def render_and_save_frame(args):
    fr, out_dir = args
    finish(render(fr), fr).save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_redis_pubsub_vs_kafka"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, [(fr, out_dir) for fr in frames]))
    print(f"Rendered Redis Pub/Sub vs Kafka frames: {len(frames)}")
