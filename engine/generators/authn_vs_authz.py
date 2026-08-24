#!/usr/bin/env python3
"""
Flagship System Design Reel: AuthN vs AuthZ — Blueprint Pinball Machine
Visual Apparatus: A tilted arcade pinball playfield. Top half is the AuthN
chamber with glowing pop-bumpers (JWT, TOKEN, PASSKEY). Bottom half is the
AuthZ enforcement zone with role-gate drop-targets and dual flippers.
Beat 1: Ball launches up shooter lane, bounces AuthN bumpers → identity verified.
Beat 2: Ball rolls into ADMIN gate → flippers slam shut → 403 FORBIDDEN sparks.
Beat 3: RBAC routes Viewer ball through READ lane → 200 OK, score maxes out.
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
    (0,   "a signed JWT enters your API — who is this user?"),
    (60,  "AuthN checks identity: signature valid, user #42 confirmed."),
    (124, "user #42 tries DELETE /db — 403 FORBIDDEN. identity ≠ permission."),
    (188, "RBAC policy routes each role to its allowed scope."),
    (250, "identity verified (AuthN) · permissions enforced (AuthZ)."),
]

# ── Playfield geometry ──────────────────────────────────────────────
PF_X0, PF_X1 = 68, 652       # playfield left/right rails
PF_Y0, PF_Y1 = 420, 938      # playfield top/bottom
PF_CX = (PF_X0 + PF_X1) / 2  # center X
SHOOTER_X = PF_X1 - 28        # shooter lane center X

# ── AuthN bumpers (top chamber) ────────────────────────────────────
BUMPERS = [
    {"cx": 220, "cy": 530, "r": 28, "label": "JWT",     "sub": "SIG ✓"},
    {"cx": 360, "cy": 510, "r": 30, "label": "TOKEN",   "sub": "USR #42"},
    {"cx": 500, "cy": 530, "r": 28, "label": "PASSKEY", "sub": "FIDO2"},
]

# ── AuthZ gate lanes ───────────────────────────────────────────────
GATES = [
    {"name": "READ",  "role": "VIEWER", "x0": 98,  "x1": 230, "col": TEAL},
    {"name": "ADMIN", "role": "ADMIN",  "x0": 260, "x1": 420, "col": RED},
    {"name": "WRITE", "role": "EDITOR", "x0": 450, "x1": 582, "col": BLUE},
]

# ── Ball trajectory keyframes ──────────────────────────────────────
# Each segment: (start_fr, end_fr, x0, y0, x1, y1, arc_height)
# arc_height > 0 means the ball arcs upward (parabolic), 0 = linear

# Beat 1: Launch up shooter lane → curve into bumper chamber → bounce through 3 bumpers → settle
BEAT1_PATH = [
    # Launch up shooter lane
    (14,  32,  SHOOTER_X, PF_Y1 - 20, SHOOTER_X, PF_Y0 + 60,  0),
    # Curve left into bumper zone
    (32,  42,  SHOOTER_X, PF_Y0 + 60, 500, 530,  -30),
    # Hit PASSKEY bumper → bounce to TOKEN
    (42,  52,  500, 530,  360, 510,  -25),
    # Hit TOKEN bumper → bounce to JWT
    (52,  62,  360, 510,  220, 530,  -20),
    # Bounce down from JWT toward AuthZ zone entrance
    (62,  82,  220, 530,  340, 640,  -15),
    # Coast into center above gates
    (82,  89,  340, 640,  340, 660,  0),
]

# Beat 2: Ball rolls into ADMIN gate → slammed back by flipper → rejected → drains
BEAT2_PATH = [
    # Roll into ADMIN gate
    (90,  108, 340, 660,  340, 745,  0),
    # SLAM — flipper kicks it back up-left with a hard arc
    (108, 126, 340, 745,  220, 620,  -50),
    # Tumble back down with 403 rejection
    (126, 148, 220, 620,  280, 820,  -20),
    # Fall into drain
    (148, 174, 280, 820,  340, 920,  0),
]

# Beat 3: New ball launches, passes AuthN quickly, routes through READ lane → 200 OK
BEAT3_PATH = [
    # Quick launch
    (180, 195, SHOOTER_X, PF_Y1 - 20, SHOOTER_X, PF_Y0 + 60, 0),
    # Fast curve into bumper chamber
    (195, 205, SHOOTER_X, PF_Y0 + 60, 360, 510, -30),
    # Quick bounce through bumpers (identity already known)
    (205, 215, 360, 510,  220, 530,  -20),
    # Down to gate entrance
    (215, 228, 220, 530,  164, 660,  -10),
    # Through READ lane (correct role)
    (228, 248, 164, 660,  164, 760,  0),
    # Celebrate — arc out of lane
    (248, 268, 164, 760,  340, 850,  -35),
    # Settle at response drain
    (268, 285, 340, 850,  340, 920,  0),
]


def ball_pos(fr, path):
    """Compute ball (x, y) from keyframed path with parabolic arcs."""
    for sf, ef, x0, y0, x1, y1, arc_h in path:
        if sf <= fr <= ef:
            t = ease((fr - sf) / max(1, ef - sf))
            bx = lerp(x0, x1, t)
            by = lerp(y0, y1, t)
            # Parabolic arc: peak at t=0.5
            by += arc_h * 4 * t * (1 - t)
            return bx, by
    # After last segment, hold final position
    if path and fr > path[-1][1]:
        return path[-1][4], path[-1][5]
    if path and fr < path[0][0]:
        return path[0][2], path[0][3]
    return -100, -100


def bumper_hit_frame(fr, path, bcx, bcy, radius=35):
    """Check if ball hits a bumper at a specific frame."""
    bx, by = ball_pos(fr, path)
    dist = math.hypot(bx - bcx, by - bcy)
    return dist < radius


def draw_playfield(d, fr, a):
    """Draw the tilted pinball playfield cabinet with rails and lane guides."""
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    cab_col = GREEN if beat3 else (RED if beat2 else BLUE)

    # ── Outer cabinet frame ──
    d.rounded_rectangle([PF_X0, PF_Y0, PF_X1, PF_Y1], radius=14, fill=(8, 10, 15),
                        outline=alpha(cab_col, a * (pulse if beat2 else 0.7)), width=2)

    # ── Inner playfield border ──
    d.rounded_rectangle([PF_X0 + 6, PF_Y0 + 6, PF_X1 - 6, PF_Y1 - 6], radius=10,
                        fill=(6, 8, 12), outline=alpha(DIM, a * 0.5), width=1)

    # ── Top arch rail ──
    d.arc([PF_X0 + 10, PF_Y0 + 6, PF_X1 - 50, PF_Y0 + 90], start=180, end=360,
          fill=alpha(cab_col, a * 0.6), width=2)

    # ── Shooter lane rail (right side) ──
    sx = PF_X1 - 44
    d.line([(sx, PF_Y0 + 50), (sx, PF_Y1 - 6)], fill=alpha(DIM, a * 0.7), width=2)

    # ── Plunger spring ──
    spring_base = PF_Y1 - 55
    compress = 0
    if fr < 14:
        compress = 12 * ease(fr / 14)  # Compressing
    elif fr < 32:
        compress = 12 * (1 - ease((fr - 14) / 8))  # Releasing
    elif 180 <= fr < 195:
        compress = 12 * ease((fr - 180) / 8) * (1 - ease((fr - 186) / 9))

    for s in range(6):
        sy = spring_base + s * 7 + compress
        d.line([(sx + 6, sy), (sx + 22, sy + 3)], fill=alpha(AMBER, a * 0.85), width=2)
        d.line([(sx + 22, sy + 3), (sx + 6, sy + 7)], fill=alpha(AMBER, a * 0.85), width=2)

    # ── Plunger knob ──
    d.rounded_rectangle([sx + 8, PF_Y1 - 14, sx + 20, PF_Y1 - 6], radius=2,
                        fill=alpha(WHITE, a * 0.75))

    # ── Zone divider line between AuthN and AuthZ ──
    div_y = 645
    d.line([(PF_X0 + 20, div_y), (PF_X1 - 50, div_y)], fill=alpha(DIM, a * 0.5), width=1)

    # ── Zone labels ──
    # AuthN zone label
    d.rounded_rectangle([PF_CX - 100, PF_Y0 + 12, PF_CX + 100, PF_Y0 + 32],
                        radius=4, fill=(14, 18, 28),
                        outline=alpha(TEAL if not beat2 else (GREEN if beat3 else RED), a * 0.65), width=1)
    track(d, (PF_CX, PF_Y0 + 22), "AUTHN ZONE · WHO ARE YOU?",
          MONOB(9), alpha(WHITE, a), sp=1, anchor="mm")

    # AuthZ zone label
    d.rounded_rectangle([PF_CX - 110, div_y + 4, PF_CX + 110, div_y + 24],
                        radius=4, fill=(14, 18, 28),
                        outline=alpha(GREEN if beat3 else (RED if beat2 else AMBER), a * 0.65), width=1)
    track(d, (PF_CX, div_y + 14), "AUTHZ ZONE · WHAT CAN YOU DO?",
          MONOB(9), alpha(WHITE, a), sp=1, anchor="mm")

    # ── Left/Right inlane guides (triangular slingshot bumpers) ──
    sl_col = GREEN if beat3 else (RED if beat2 else AMBER)
    # Left slingshot
    d.polygon([(PF_X0 + 14, 750), (PF_X0 + 50, 780), (PF_X0 + 14, 810)],
              fill=(12, 15, 22), outline=alpha(sl_col, a * 0.65))
    d.ellipse([PF_X0 + 24, 776, PF_X0 + 34, 786], fill=alpha(sl_col, a * 0.7))
    # Right slingshot
    d.polygon([(PF_X1 - 58, 750), (PF_X1 - 58 + 36, 780), (PF_X1 - 58, 810)],
              fill=(12, 15, 22), outline=alpha(sl_col, a * 0.65))
    d.ellipse([PF_X1 - 54, 776, PF_X1 - 44, 786], fill=alpha(sl_col, a * 0.7))


def draw_bumpers(d, fr, a):
    """Draw pop-bumpers with impact rings on ball contact."""
    beat2, beat3 = fr >= 90, fr >= 180
    path = BEAT3_PATH if beat3 else (BEAT2_PATH if beat2 else BEAT1_PATH)

    for bmp in BUMPERS:
        bcx, bcy, br = bmp["cx"], bmp["cy"], bmp["r"]

        # Check for recent hit (within last 6 frames)
        hit = False
        for check_fr in range(max(0, fr - 5), fr + 1):
            if bumper_hit_frame(check_fr, path, bcx, bcy, br + 8):
                hit = True
                break

        base_col = TEAL if not beat2 else (GREEN if beat3 else RED)
        glow = 1.0 if hit else 0.45

        # Outer ring with glow
        d.ellipse([bcx - br, bcy - br, bcx + br, bcy + br],
                  fill=(12, 16, 26), outline=alpha(base_col, a * glow), width=2)

        # Inner hot core
        inner_r = br - 10
        d.ellipse([bcx - inner_r, bcy - inner_r, bcx + inner_r, bcy + inner_r],
                  fill=alpha(base_col, a * (0.75 if hit else 0.2)))

        # Cross-hatch scoring marks inside bumper
        if hit:
            for k in range(4):
                angle = k * math.pi / 4 + (fr * 0.15)
                x1 = bcx + (inner_r - 3) * math.cos(angle)
                y1 = bcy + (inner_r - 3) * math.sin(angle)
                x2 = bcx - (inner_r - 3) * math.cos(angle)
                y2 = bcy - (inner_r - 3) * math.sin(angle)
                d.line([(x1, y1), (x2, y2)], fill=alpha(WHITE, a * 0.35), width=1)

        # Impact expanding ring
        if hit:
            ring_r = br + 6 + (fr % 6) * 2.5
            ring_a = max(0, 1.0 - (fr % 6) / 6)
            d.ellipse([bcx - ring_r, bcy - ring_r, bcx + ring_r, bcy + ring_r],
                      outline=alpha(base_col, a * ring_a * 0.6), width=1)

        # Labels
        d.text((bcx, bcy - 3), bmp["label"], font=MONOB(9), fill=alpha(WHITE, a), anchor="mm")
        d.text((bcx, bcy + 9), bmp["sub"], font=MONO(7), fill=alpha(MUTED, a * 0.85), anchor="mm")


def draw_gates(d, fr, a):
    """Draw AuthZ role-gate drop targets."""
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    for i, gate in enumerate(GATES):
        gx0, gx1 = gate["x0"], gate["x1"]
        gy0, gy1 = 670, 755
        is_admin = (i == 1)
        is_read = (i == 0)

        if beat3:
            if is_read:
                g_col = GREEN
                status = "✓ 200 OK"
                s_col = GREEN
            elif is_admin:
                g_col = RED
                status = "LOCKED"
                s_col = RED
            else:
                g_col = BLUE
                status = "STANDBY"
                s_col = BLUE
        elif beat2:
            if is_admin:
                g_col = RED
                status = "✗ 403"
                s_col = RED
            else:
                g_col = DIM
                status = "—"
                s_col = DIM
        else:
            g_col = gate["col"]
            status = "READY"
            s_col = MUTED

        outline_a = a * (pulse if (beat2 and is_admin) else 0.75)
        d.rounded_rectangle([gx0, gy0, gx1, gy1], radius=6, fill=(10, 13, 20),
                            outline=alpha(g_col, outline_a), width=2)

        # Gate icon bar at top of lane
        d.line([(gx0 + 8, gy0 + 2), (gx1 - 8, gy0 + 2)], fill=alpha(g_col, a * 0.8), width=2)

        # Lane name
        d.text(((gx0 + gx1) / 2, gy0 + 20), gate["name"], font=MONOB(12),
               fill=alpha(WHITE, a), anchor="mm")

        # Role requirement
        d.text(((gx0 + gx1) / 2, gy0 + 38), f"ROLE: {gate['role']}", font=MONO(8),
               fill=alpha(MUTED, a * 0.85), anchor="mm")

        # Status badge
        badge_y = gy1 - 20
        d.rounded_rectangle([gx0 + 8, badge_y - 8, gx1 - 8, badge_y + 8],
                            radius=4, fill=(8, 10, 16),
                            outline=alpha(g_col, a * 0.6), width=1)
        d.text(((gx0 + gx1) / 2, badge_y), status, font=MONOB(9),
               fill=alpha(s_col, a * (pulse if (beat2 and is_admin) else 1.0)), anchor="mm")

        # Beat 3: green flow arrow through READ lane
        if beat3 and is_read and fr >= 228:
            arrow_prog = ease((fr - 228) / 20)
            ay = lerp(gy0 + 10, gy1 - 10, arrow_prog)
            d.line([((gx0 + gx1) / 2, gy0 + 55), ((gx0 + gx1) / 2, ay)],
                   fill=alpha(GREEN, a * 0.7), width=3)
            # Arrowhead
            d.polygon([((gx0 + gx1) / 2, ay + 4),
                       ((gx0 + gx1) / 2 - 5, ay - 4),
                       ((gx0 + gx1) / 2 + 5, ay - 4)],
                      fill=alpha(GREEN, a * 0.8))


def draw_flippers(d, fr, a):
    """Draw dual security flippers with animated swing."""
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    # Flipper pivot points
    l_pivot = (190, 830)
    r_pivot = (490, 830)
    flip_len = 75

    # Flipper angles (degrees from horizontal)
    if beat2:
        # Slam up to block
        swing = ease((fr - 90) / 10)
        l_angle = lerp(-25, 10, swing)
        r_angle = lerp(205, 170, swing)
    elif beat3:
        # Gentle guiding motion
        osc = math.sin((fr - 180) * 0.12) * 12
        l_angle = -20 + osc
        r_angle = 200 - osc
    else:
        # Idle rocking
        osc = math.sin(fr * 0.15) * 15
        l_angle = -25 + osc
        r_angle = 205 - osc

    f_col = GREEN if beat3 else (RED if beat2 else TEAL)

    for pivot, angle in [(l_pivot, l_angle), (r_pivot, r_angle)]:
        rad = math.radians(angle)
        tip_x = pivot[0] + math.cos(rad) * flip_len
        tip_y = pivot[1] + math.sin(rad) * flip_len

        # Flipper bar (tapered — thick at pivot, thin at tip)
        # Draw as polygon for taper effect
        perp = math.radians(angle + 90)
        pw, tw = 5, 2  # pivot width, tip width
        pts = [
            (pivot[0] + pw * math.cos(perp), pivot[1] + pw * math.sin(perp)),
            (tip_x + tw * math.cos(perp), tip_y + tw * math.sin(perp)),
            (tip_x - tw * math.cos(perp), tip_y - tw * math.sin(perp)),
            (pivot[0] - pw * math.cos(perp), pivot[1] - pw * math.sin(perp)),
        ]
        d.polygon(pts, fill=alpha(f_col, a * (pulse if beat2 else 0.85)),
                  outline=alpha(WHITE, a * 0.5))

        # Pivot dot
        d.ellipse([pivot[0] - 5, pivot[1] - 5, pivot[0] + 5, pivot[1] + 5],
                  fill=alpha(WHITE, a * 0.9))
        # Tip dot
        d.ellipse([tip_x - 3, tip_y - 3, tip_x + 3, tip_y + 3],
                  fill=alpha(AMBER, a * 0.8))

    # Label between flippers
    if beat3:
        track(d, (340, 825), "✓ POLICY ROUTE", MONOB(10), alpha(GREEN, a), sp=1, anchor="mm")
    elif beat2:
        track(d, (340, 825), "⚠ RBAC BLOCK", MONOB(10), alpha(RED, a * pulse), sp=1, anchor="mm")
    else:
        track(d, (340, 825), "AUTHZ FLIPPERS", MONO(9), alpha(MUTED, a), sp=1, anchor="mm")

    # Drain slot
    d.line([(280, 878), (400, 878)], fill=alpha(DIM, a * 0.55), width=2)
    d.text((340, 895), "RESPONSE DRAIN", font=MONO(8), fill=alpha(MUTED, a * 0.6), anchor="mm")


def draw_ball(d, fr, a):
    """Draw the pinball with trail, label, and impact effects."""
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    if fr < 14:
        # Ball sitting on plunger, not yet launched
        bx, by = SHOOTER_X, PF_Y1 - 20 - 4 * ease(fr / 14)
        d.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=alpha(TEAL, a))
        d.ellipse([bx - 9, by - 9, bx + 9, by + 9], outline=alpha(TEAL, a * 0.4), width=1)
        return

    path = BEAT3_PATH if beat3 else (BEAT2_PATH if beat2 else BEAT1_PATH)
    bx, by = ball_pos(fr, path)

    if bx < -50:
        return

    ball_col = GREEN if beat3 else (RED if beat2 else TEAL)

    # Motion trail (last 4 positions)
    for trail_i in range(4):
        tfr = fr - (trail_i + 1) * 2
        if tfr < (path[0][0] if path else 0):
            break
        tx, ty = ball_pos(tfr, path)
        if tx > -50:
            ta = a * (0.25 - trail_i * 0.05)
            tr = 4 - trail_i * 0.5
            d.ellipse([tx - tr, ty - tr, tx + tr, ty + tr], fill=alpha(ball_col, ta))

    # Main ball
    d.ellipse([bx - 7, by - 7, bx + 7, by + 7], fill=alpha(ball_col, a))
    # Highlight spot (shiny steel ball)
    d.ellipse([bx - 3, by - 4, bx + 1, by - 1], fill=alpha(WHITE, a * 0.55))
    # Outer glow ring
    d.ellipse([bx - 11, by - 11, bx + 11, by + 11],
              outline=alpha(ball_col, a * 0.4), width=1)

    # Beat 2 rejection label
    if beat2 and 108 <= fr <= 174:
        d.text((bx + 16, by), "403", font=MONOB(10),
               fill=alpha(RED, a * pulse), anchor="lm")

    # Beat 2 impact sparks at flipper contact point (fr ~108)
    if beat2 and 106 <= fr <= 118:
        spark_t = (fr - 106) / 12
        for spk in range(6):
            sa = spk * math.pi / 3 + fr * 0.3
            sr = 8 + spark_t * 18
            sx = 340 + sr * math.cos(sa)
            sy = 745 + sr * math.sin(sa)
            spark_a = a * (1 - spark_t) * 0.8
            d.line([(340, 745), (sx, sy)], fill=alpha(RED, spark_a), width=2)
            d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=alpha(AMBER, spark_a))

    # Beat 3 success label near READ gate
    if beat3 and 228 <= fr <= 268:
        if by > 700:
            d.text((bx + 16, by), "200 OK", font=MONOB(9),
                   fill=alpha(GREEN, a), anchor="lm")

    # Beat 1 identity confirmed near bottom
    if not beat2 and not beat3 and fr >= 62:
        if by > 600:
            d.text((bx + 16, by - 4), "JWT ✓", font=MONO(8),
                   fill=alpha(WHITE, a * 0.85), anchor="lm")


def draw_score_display(d, fr, a):
    """Draw arcade-style score counter above the playfield."""
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    # Score ramps up on bumper hits
    if beat3:
        score = 4200
        s_col = GREEN
    elif beat2:
        score_base = 1500
        score = score_base + int(lerp(0, 1200, ease((fr - 90) / 60)))
        s_col = RED
    else:
        if fr < 42:
            score = 0
        elif fr < 52:
            score = 500
        elif fr < 62:
            score = 1000
        else:
            score = 1500
        s_col = TEAL

    # Score display box
    sd_x0, sd_y0 = PF_X0 + 10, PF_Y0 - 32
    sd_x1, sd_y1 = PF_X0 + 135, PF_Y0 - 4
    d.rounded_rectangle([sd_x0, sd_y0, sd_x1, sd_y1], radius=5, fill=(10, 13, 19),
                        outline=alpha(s_col, a * 0.6), width=1)
    d.text((sd_x0 + 8, sd_y0 + 6), "SCORE", font=MONO(7), fill=alpha(MUTED, a * 0.8), anchor="lt")
    d.text((sd_x1 - 8, sd_y1 - 6), f"{score:,}", font=MONOB(14),
           fill=alpha(s_col, a), anchor="rb")

    # Ball count indicator
    bc_x0 = PF_X1 - 135
    bc_x1 = PF_X1 - 10
    d.rounded_rectangle([bc_x0, sd_y0, bc_x1, sd_y1], radius=5, fill=(10, 13, 19),
                        outline=alpha(s_col, a * 0.6), width=1)
    d.text((bc_x0 + 8, sd_y0 + 6), "STATUS", font=MONO(7), fill=alpha(MUTED, a * 0.8), anchor="lt")
    if beat3:
        status_txt = "RBAC OK"
        st_col = GREEN
    elif beat2:
        status_txt = "BLOCKED"
        st_col = RED
    else:
        status_txt = "AUTHN..."
        st_col = TEAL
    d.text((bc_x1 - 8, sd_y1 - 6), status_txt, font=MONOB(11),
           fill=alpha(st_col, a * (pulse if beat2 else 1.0)), anchor="rb")


def draw_query_pill(d, fr, a):
    """Draw the API request context pill above the playfield."""
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    col = GREEN if beat3 else (RED if beat2 else BLUE)
    ca = a * (pulse if beat2 else 1.0)

    d.rounded_rectangle([52, 410, 668, 382], radius=0, fill=BG)  # Clear zone
    # No separate pill — the score display + playfield serve as the stage


def draw_takeaway_bar(d, fr, a):
    """Bottom takeaway one-liner inside the stage zone."""
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)
    y = 944

    if beat3:
        track(d, (W / 2, y), "✓ AUTHN = IDENTITY  ·  AUTHZ = PERMISSIONS  ·  RBAC ENFORCED",
              MONOB(10), alpha(GREEN, a), sp=1, anchor="mm")
    elif beat2:
        track(d, (W / 2, y), "⚠ IDENTITY ≠ PERMISSION · AUTHN PASSED BUT AUTHZ DENIED",
              MONOB(10), alpha(RED, a * pulse), sp=1, anchor="mm")
    else:
        track(d, (W / 2, y), "DUAL SECURITY LAYERS · IDENTITY FIRST, PERMISSIONS SECOND",
              MONOB(10), alpha(MUTED, a), sp=1, anchor="mm")


# ── Beat 2 crisis stamps ──────────────────────────────────────────
def draw_crisis_stamps(d, fr, a):
    """Beat 2 alarm tag and rejection stamp."""
    beat2 = fr >= 90 and fr < 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    # Opening alarm tag
    if 90 <= fr <= 130:
        ga = ease((fr - 90) / 5) * (1 - ease((fr - 120) / 10))
        track(d, (W / 2, 480), "⚠ VIEWER ROLE ATTEMPTS ADMIN ACTION",
              MONOB(11), alpha(RED, a * ga * pulse), sp=2, anchor="mm")

    # Rejection stamp
    if 148 <= fr <= 178:
        so = ease((fr - 148) / 6) * (1 - ease((fr - 170) / 8))
        track(d, (W / 2, 480), "✗ 403 FORBIDDEN — INSUFFICIENT PERMISSIONS",
              MONOB(14), alpha(RED, a * so * pulse), sp=2, anchor="mm")


def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag
    beat2, beat3 = fr >= 90, fr >= 180
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    # ──── 1. Header (Y: 148 – 290) ────
    # Blueprint dot grid
    for gx in range(36, W - 36, 48):
        for gy in range(80, H - 80, 48):
            d.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(22, 28, 40))

    # CAD crosshairs
    for cx_pos, cy_pos in [(48, 140), (W - 48, 140)]:
        d.line([(cx_pos - 8, cy_pos), (cx_pos + 8, cy_pos)], fill=alpha(DIM, 0.7), width=1)
        d.line([(cx_pos, cy_pos - 8), (cx_pos, cy_pos + 8)], fill=alpha(DIM, 0.7), width=1)

    # Red handle branding pill
    pill_w = d.textlength("@buildebugship", font=MONOB(12)) + 36
    px0, py0 = W / 2 - pill_w / 2, 148
    px1, py1 = W / 2 + pill_w / 2, 172
    d.rounded_rectangle([px0, py0, px1, py1], radius=12, fill=(18, 14, 20),
                        outline=alpha(RED, 0.8 * intro), width=1)
    d.ellipse([px0 + 10, py0 + 8, px0 + 16, py0 + 14], fill=RED)
    d.text((px0 + 24, py0 + 11), "@buildebugship", font=MONOB(12),
           fill=alpha(WHITE, intro), anchor="lm")

    # Comparison tag
    track(d, (W / 2, 192), "AUTHN (WHO YOU ARE)   vs   AUTHZ (WHAT YOU CAN DO)",
          MONOB(11), alpha(MUTED, intro), sp=2, anchor="mm")

    # Large bold headline
    tw1 = d.textlength("AUTHN ", font=SANSB(42))
    tw2 = d.textlength("vs ", font=SANSB(32))
    tw3 = d.textlength("AUTHZ", font=SANSB(42))
    sx = W / 2 - (tw1 + tw2 + tw3) / 2
    d.text((sx, 228), "AUTHN ", font=SANSB(42), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + tw1, 230), "vs ", font=SANSB(32), fill=alpha(DIM, intro), anchor="lm")
    d.text((sx + tw1 + tw2, 228), "AUTHZ", font=SANSB(42), fill=alpha(TEAL, intro), anchor="lm")

    # Subhook
    d.text((W / 2, 268), "identity vs permission explained via pinball mechanics",
           font=SANS(13), fill=alpha(BLUE, intro * 0.95), anchor="mm")

    # Divider
    d.line([(48, 290), (W - 48, 290)], fill=alpha(DIM, 0.6), width=1)

    if diag <= 0.01:
        return base

    # ──── 2. Telemetry HUD (Y: 304 – 376) ────
    if beat3:
        m1v, m1c = "200 VERIFIED", GREEN
        m2v, m2c = "200 RBAC OK", GREEN
    elif beat2:
        m1v, m1c = "200 JWT OK", TEAL
        m2v, m2c = "403 DENIED", RED
    else:
        m1v, m1c = "CHECKING...", TEAL
        m2v, m2c = "PENDING", AMBER

    draw_telemetry_hud(d, "AUTHENTICATION", m1v, "AUTHORIZATION", m2v, a,
                       m1_col=m1c, m2_col=m2c)

    # ──── 3. Status line (Y: ~390) ────
    if beat3:
        st, stc = "RBAC POLICY: user.role='viewer' → scope.read GRANTED", GREEN
    elif beat2:
        st, stc = "RBAC POLICY: user.role='viewer' → scope.admin DENIED", RED
    else:
        st, stc = "AUTH PIPELINE: Bearer eyJhbG... → signature verification", MUTED
    track(d, (W / 2, 393), st, MONOB(10), alpha(stc, a * (pulse if beat2 else 1.0)),
          sp=1, anchor="mm")

    # ──── 4. Stage (Y: 388 – 950) ────
    draw_score_display(d, fr, a)
    draw_playfield(d, fr, a)
    draw_bumpers(d, fr, a)
    draw_gates(d, fr, a)
    draw_flippers(d, fr, a)
    draw_ball(d, fr, a)
    draw_crisis_stamps(d, fr, a)
    draw_takeaway_bar(d, fr, a)

    # ──── 5. Caption pill (Y: 980 – 1028) ────
    draw_caption_pill(d, fr, CAPTIONS, a)

    # ──── 6. Outro footer (fr 258+) ────
    if fr >= 258:
        o = ease((fr - 258) / 18)
        track(d, (W / 2, 1090), "AUTHN = IDENTITY (WHO) · AUTHZ = PERMISSIONS (WHAT) · RBAC",
              MONOB(11), alpha(TEAL, o), sp=2, anchor="mm")
        track(d, (W / 2, 1112), "JWT · OAUTH2 · OIDC · CASBIN · KEYCLOAK · OPA · OKTA",
              MONO(10), alpha(DIM, o), sp=2, anchor="mm")

    return base


def render_and_save_frame(args):
    fr, out_dir = args
    finish(render(fr), fr).save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_authn_vs_authz"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, [(fr, out_dir) for fr in frames]))
    print(f"Rendered AuthN vs AuthZ Pinball frames: {len(frames)}")
