#!/usr/bin/env python3
"""
Flagship System Design Reel: CI/CD Pipeline (Continuous Integration & Continuous Delivery)
Visual Apparatus:
- Developer Git commit stream with branch metadata.
- 4-Stage CI Automation Matrix: 1. Lint/AST -> 2. Build/Docker -> 3. Automated Test Gate -> 4. Signed Artifact Hub.
- Continuous Delivery (CD) Zero-Downtime Engine:
  - Top Ingress / Canary Traffic Balancer
  - Dual Blue (v1 Stable) & Green (v2 Canary) Pod Clusters
  - Live orthogonal packet traffic routing and zero-downtime cutover.
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
    draw_blueprint_grid, draw_cad_crosshairs,
)

CAPTIONS = [
    (0,   "every git push triggers an automated CI/CD pipeline."),
    (60,  "code is linted, compiled, and validated across 428 unit tests."),
    (124, "a bad commit breaks a test: the CI gate halts deployment instantly."),
    (188, "with the fix pushed, CD triggers an automated canary rollout."),
    (250, "traffic shifts to green pods with zero downtime and 100% health."),
]


def draw_header(d, intro):
    draw_blueprint_grid(d)
    draw_cad_crosshairs(d, 48, 140)
    draw_cad_crosshairs(d, W - 48, 140)

    # Red handle branding pill
    handle = "@buildebugship"
    pill_w = d.textlength(handle, font=MONOB(12)) + 36
    px0, py0 = W / 2 - pill_w / 2, 148
    px1, py1 = W / 2 + pill_w / 2, 172
    d.rounded_rectangle([px0, py0, px1, py1], radius=12, fill=(18, 14, 20),
                        outline=alpha(RED, 0.8 * intro), width=1)
    d.ellipse([px0 + 10, py0 + 8, px0 + 16, py0 + 14], fill=RED)
    d.text((px0 + 24, py0 + 11), handle, font=MONOB(12), fill=alpha(WHITE, intro), anchor="lm")

    # Comparison Tag
    track(d, (W / 2, 192), "MANUAL DEPLOYS (HIGH RISK)  vs  AUTOMATED CI/CD (0 DOWNTIME)",
          MONOB(10), alpha(MUTED, intro), sp=1, anchor="mm")

    # Headline: CI/CD PIPELINE
    t1, t2 = "CI/CD ", "PIPELINE"
    w1 = d.textlength(t1, font=SANSB(40))
    w2 = d.textlength(t2, font=SANSB(40))
    sx = W / 2 - (w1 + w2) / 2
    d.text((sx, 228), t1, font=SANSB(40), fill=alpha(WHITE, intro), anchor="lm")
    d.text((sx + w1, 228), t2, font=SANSB(40), fill=alpha(TEAL, intro), anchor="lm")

    # Subhook
    d.text((W / 2, 268), "automated test gating, container builds & canary delivery",
           font=SANS(13), fill=alpha(BLUE, intro * 0.95), anchor="mm")

    # Divider line
    d.line([(48, 290), (W - 48, 290)], fill=alpha(DIM, 0.6 * intro), width=1)


def draw_commit_bar(d, fr, a):
    """Draws the Git Ingest pill at the top of the stage (Y: 415 to 465)"""
    beat2 = (90 <= fr < 180)
    beat3 = (fr >= 180)
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    col = GREEN if beat3 else (RED if beat2 else BLUE)
    ca = a * (pulse if beat2 else 1.0)

    # Outer container
    d.rounded_rectangle([48, 415, W - 48, 465], radius=8, fill=(12, 16, 24),
                        outline=alpha(col, ca * 0.8), width=2)

    # Git branch badge
    d.rounded_rectangle([58, 423, 138, 457], radius=5, fill=(16, 22, 32),
                        outline=alpha(col, ca * 0.5), width=1)
    d.ellipse([68, 437, 76, 445], fill=alpha(col, ca))
    d.line([(76, 441), (92, 441)], fill=alpha(col, ca), width=2)
    d.ellipse([92, 437, 100, 445], fill=alpha(col, ca))
    d.text((106, 440), "main", font=MONOB(10), fill=alpha(WHITE, a), anchor="lm")

    if beat3:
        commit_hash = "c8f2a1e -> 2b7e19d"
        msg = "git push · fix(auth): sanitize token check"
        status_txt = "MERGED [OK]"
        status_col = GREEN
    elif beat2:
        commit_hash = "f9a031c"
        msg = "git push · feat: broken auth query (buggy)"
        status_txt = "BLOCKED [X]"
        status_col = RED
    else:
        commit_hash = "c8f2a1e"
        msg = "git push · feat: user payment service v2.4"
        status_txt = "TRIGGERED"
        status_col = TEAL

    d.text((148, 431), msg, font=MONOB(10), fill=alpha(WHITE, a), anchor="lm")
    d.text((148, 449), f"commit [{commit_hash}]", font=MONO(9), fill=alpha(MUTED, a), anchor="lm")

    # Status Pill
    d.rounded_rectangle([W - 152, 425, W - 58, 455], radius=4, fill=(10, 14, 20),
                        outline=alpha(status_col, ca * 0.7), width=1)
    d.text((W - 105, 440), status_txt, font=MONOB(9),
           fill=alpha(status_col, ca), anchor="mm")


def draw_ci_stages(d, fr, a):
    """Draws the 4 CI Pipeline Chambers: Lint -> Build -> Test -> Artifact (Y: 480 to 670)"""
    beat2 = (90 <= fr < 180)
    beat3 = (fr >= 180)
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    # CI Group Outer Enclosure
    d.rounded_rectangle([48, 480, W - 48, 672], radius=10, fill=(10, 13, 19),
                        outline=alpha(DIM, a * 0.8), width=1)
    d.rectangle([48, 480, W - 48, 502], fill=(15, 20, 28))
    track(d, (58, 491), "CONTINUOUS INTEGRATION (CI) AUTOMATION SUITE",
          MONOB(9), alpha(WHITE, a), sp=1, anchor="lm")
    track(d, (W - 58, 491), "GITHUB ACTIONS RUNNER",
          MONO(8), alpha(MUTED, a), sp=1, anchor="rm")

    # 4 Pipeline Stage Nodes
    stages = [
        {"name": "1. LINT / AST", "desc": "Syntax & Types", "x0": 58, "x1": 194},
        {"name": "2. BUILD", "desc": "Docker Image", "x0": 208, "x1": 344},
        {"name": "3. TEST GATE", "desc": "428 Unit Tests", "x0": 358, "x1": 494},
        {"name": "4. ARTIFACT", "desc": "Container Hub", "x0": 508, "x1": 644},
    ]

    sy0, sy1 = 512, 616

    # Connector Conduits between stages
    for i in range(len(stages) - 1):
        cx0 = stages[i]["x1"]
        cx1 = stages[i + 1]["x0"]
        cmy = (sy0 + sy1) / 2
        d.line([(cx0, cmy), (cx1, cmy)], fill=alpha(DIM, a * 0.6), width=3)
        d.polygon([(cx1 - 3, cmy), (cx1 - 8, cmy - 3), (cx1 - 8, cmy + 3)], fill=alpha(DIM, a * 0.8))

    # Stage statuses based on beat & frame progress
    for idx, st in enumerate(stages):
        x0, x1 = st["x0"], st["x1"]

        if beat3:
            active = True
            failed = False
            stage_stat = ["PASS 0.3s ✓", "DOCKER OK ✓", "428/428 ✓", "IMAGE v2.4.2 ✓"][idx]
            sub_col = GREEN
        elif beat2:
            if idx == 0:
                active, failed, stage_stat, sub_col = True, False, "PASS 0.4s ✓", GREEN
            elif idx == 1:
                active, failed, stage_stat, sub_col = True, False, "DOCKER OK ✓", GREEN
            elif idx == 2:
                active, failed, stage_stat, sub_col = True, True, "FAIL ✗ (NullPtr)", RED
            else:
                active, failed, stage_stat, sub_col = False, False, "BLOCKED ✗", DIM
        else:
            prog_idx = int((fr / 90.0) * 4.0)
            if idx < prog_idx:
                active, failed, stage_stat, sub_col = True, False, ["PASS 0.4s ✓", "COMPILED ✓", "428 PASS ✓", "STORED ✓"][idx], TEAL
            elif idx == prog_idx:
                active, failed, stage_stat, sub_col = True, False, "RUNNING...", AMBER
            else:
                active, failed, stage_stat, sub_col = False, False, "QUEUED", DIM

        box_col = RED if failed else (GREEN if sub_col == GREEN else (TEAL if active and not failed else DIM))
        card_fill = (24, 10, 14) if failed else ((12, 18, 25) if active else (10, 12, 17))

        # Stage Card Box
        d.rounded_rectangle([x0, sy0, x1, sy1], radius=7, fill=card_fill,
                            outline=alpha(box_col, a * (pulse if failed else 0.85)), width=2 if (failed or active) else 1)

        # Stage Header
        d.text(((x0 + x1) / 2, sy0 + 15), st["name"], font=MONOB(9), fill=alpha(WHITE, a), anchor="mm")
        d.text(((x0 + x1) / 2, sy0 + 30), st["desc"], font=SANS(8), fill=alpha(MUTED, a), anchor="mm")

        # Stage Mini Visual Widget
        wy0, wy1 = sy0 + 42, sy0 + 68
        d.rectangle([x0 + 8, wy0, x1 - 8, wy1], fill=(7, 9, 13), outline=alpha(DIM, a * 0.5), width=1)

        if idx == 0:
            d.line([(x0 + 14, wy0 + 7), (x1 - 20, wy0 + 7)], fill=alpha(TEAL, a * 0.7), width=2)
            d.line([(x0 + 14, wy0 + 13), (x1 - 34, wy0 + 13)], fill=alpha(WHITE, a * 0.6), width=2)
            d.line([(x0 + 14, wy0 + 19), (x1 - 16, wy0 + 19)], fill=alpha(MUTED, a * 0.5), width=2)
        elif idx == 1:
            d.rectangle([x0 + 18, wy0 + 5, x1 - 18, wy0 + 11], fill=alpha(BLUE, a * 0.8))
            d.rectangle([x0 + 18, wy0 + 14, x1 - 18, wy0 + 20], fill=alpha(TEAL, a * 0.8))
        elif idx == 2:
            if failed:
                d.line([(x0 + 16, wy0 + 5), (x1 - 16, wy1 - 5)], fill=alpha(RED, a * pulse), width=2)
                d.line([(x1 - 16, wy0 + 5), (x0 + 16, wy1 - 5)], fill=alpha(RED, a * pulse), width=2)
            else:
                for tx in range(4):
                    d.ellipse([x0 + 18 + tx * 26, wy0 + 9, x0 + 26 + tx * 26, wy0 + 17],
                              fill=alpha(GREEN if sub_col == GREEN else TEAL, a))
        else:
            d.rectangle([x0 + 24, wy0 + 5, x1 - 24, wy1 - 6], fill=(16, 22, 30),
                        outline=alpha(GREEN if sub_col == GREEN else TEAL, a), width=1)
            d.text(((x0 + x1) / 2, (wy0 + wy1) / 2), "tar.gz", font=MONO(7),
                   fill=alpha(WHITE, a), anchor="mm")

        # Stage Status Pill at bottom of node
        d.rounded_rectangle([x0 + 6, sy1 - 20, x1 - 6, sy1 - 4], radius=3, fill=(6, 8, 12),
                            outline=alpha(sub_col, a * 0.6), width=1)
        d.text(((x0 + x1) / 2, sy1 - 12), stage_stat, font=MONOB(8),
               fill=alpha(sub_col, a * (pulse if failed else 1.0)), anchor="mm")

    # Moving CI Data Packet along the pipeline
    if not beat2:
        t_pipe = (fr % 90) / 90.0 if not beat3 else ((fr - 180) % 120) / 120.0
        pkt_x = lerp(stages[0]["x0"] + 20, stages[3]["x1"] - 20, ease(t_pipe))
        pkt_y = (sy0 + sy1) / 2
        d.ellipse([pkt_x - 5, pkt_y - 5, pkt_x + 5, pkt_y + 5], fill=alpha(GREEN if beat3 else TEAL, a))
        d.ellipse([pkt_x - 8, pkt_y - 8, pkt_x + 8, pkt_y + 8],
                  outline=alpha(GREEN if beat3 else TEAL, a * 0.5), width=1)
    else:
        pkt_x = stages[2]["x0"] + 20
        pkt_y = (sy0 + sy1) / 2
        d.ellipse([pkt_x - 6, pkt_y - 6, pkt_x + 6, pkt_y + 6], fill=alpha(RED, a * pulse))

    # Bottom status bar inside CI box (Y: 626 to 662)
    if beat3:
        d.rounded_rectangle([58, 626, W - 58, 662], radius=6, fill=(10, 24, 18),
                            outline=alpha(GREEN, a * 0.8), width=1)
        d.text((W / 2, 638), "✓ ALL 428 TESTS PASSED · CVE SCAN: 0 VULNERABILITIES",
               font=MONOB(10), fill=alpha(GREEN, a), anchor="mm")
        d.text((W / 2, 651), "IMMUTABLE ARTIFACT SIGNED & PUSHED TO REGISTRY",
               font=MONO(9), fill=alpha(TEAL, a), anchor="mm")
    elif beat2:
        d.rounded_rectangle([58, 626, W - 58, 662], radius=6, fill=(30, 10, 15),
                            outline=alpha(RED, a * (0.8 + 0.2 * pulse)), width=2)
        d.text((W / 2, 638), "! TEST FAILURE: integration_auth_spec.ts (Line 42)",
               font=MONOB(10), fill=alpha(WHITE, a), anchor="mm")
        d.text((W / 2, 651), "CI GATING HALTED DEPLOYMENT · ZERO PRODUCTION IMPACT",
               font=MONO(9), fill=alpha(RED, a * (0.8 + 0.2 * pulse)), anchor="mm")
    else:
        d.rounded_rectangle([58, 626, W - 58, 662], radius=6, fill=(11, 16, 24),
                            outline=alpha(BLUE, a * 0.5), width=1)
        d.text((W / 2, 644), "AUTOMATED MATRIX: LINT → BUILD → UNIT TEST → ARTIFACT VAULT",
               font=MONOB(9), fill=alpha(MUTED, a), anchor="mm")


def draw_cd_deployment(d, fr, a):
    """Draws the CD Zero-Downtime Canary & Blue-Green Cluster (Y: 686 to 948)"""
    beat2 = (90 <= fr < 180)
    beat3 = (fr >= 180)
    pulse = 0.55 + 0.45 * math.sin(fr * 0.45)

    # CD Group Outer Enclosure
    d.rounded_rectangle([48, 686, W - 48, 948], radius=10, fill=(10, 13, 19),
                        outline=alpha(DIM, a * 0.8), width=1)
    d.rectangle([48, 686, W - 48, 708], fill=(15, 20, 28))
    track(d, (58, 697), "CONTINUOUS DELIVERY (CD) · ZERO-DOWNTIME CANARY CLUSTER",
          MONOB(9), alpha(WHITE, a), sp=1, anchor="lm")
    track(d, (W - 58, 697), "KUBERNETES / ARGO CD",
          MONO(8), alpha(MUTED, a), sp=1, anchor="rm")

    # TOP: Ingress / Canary Traffic Router (Centered horizontally at X: 140 to 580, Y: 718 to 768)
    rx0, ry0, rx1, ry1 = 140, 718, 580, 768
    d.rounded_rectangle([rx0, ry0, rx1, ry1], radius=8, fill=(12, 17, 26),
                        outline=alpha(BLUE, a * 0.8), width=2)
    d.text((rx0 + 16, (ry0 + ry1) / 2), "INGRESS ROUTER", font=MONOB(10), fill=alpha(WHITE, a), anchor="lm")

    # Traffic Split calculation
    if beat3:
        canary_pct = int(lerp(0, 100, ease((fr - 180) / 75)))
        blue_pct = 100 - canary_pct
    else:
        canary_pct = 0
        blue_pct = 100

    # Traffic pills inside Router
    # Blue pill
    d.rounded_rectangle([rx0 + 140, ry0 + 8, rx0 + 260, ry1 - 8], radius=4, fill=(8, 12, 18),
                        outline=alpha(BLUE if blue_pct > 0 else DIM, a * 0.7), width=1)
    d.text((rx0 + 148, (ry0 + ry1) / 2), f"BLUE: {blue_pct}%", font=MONOB(9),
           fill=alpha(BLUE if blue_pct > 0 else MUTED, a), anchor="lm")

    # Green pill
    d.rounded_rectangle([rx0 + 276, ry0 + 8, rx0 + 420, ry1 - 8], radius=4, fill=(8, 12, 18),
                        outline=alpha(GREEN if canary_pct > 0 else DIM, a * 0.7), width=1)
    d.text((rx0 + 284, (ry0 + ry1) / 2), f"GREEN: {canary_pct}%", font=MONOB(9),
           fill=alpha(GREEN if canary_pct > 0 else MUTED, a), anchor="lm")

    # Orthogonal Conduits from Router Down to Clusters:
    blue_active = (blue_pct > 0)
    d.line([(240, 768), (240, 784), (195, 784), (195, 796)],
           fill=alpha(BLUE if blue_active else DIM, a * 0.8), width=2)

    green_active = (canary_pct > 0)
    green_conduit_col = GREEN if green_active else (RED if beat2 else DIM)
    d.line([(480, 768), (480, 784), (525, 784), (525, 796)],
           fill=alpha(green_conduit_col, a * 0.8), width=2)

    # Bottom Left: Blue Environment Cluster (X: 58 to 338, Y: 796 to 876)
    bx0, by0, bx1, by1 = 58, 796, 338, 876
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=8, fill=(11, 15, 23),
                        outline=alpha(BLUE if blue_active else DIM, a * (0.8 if blue_active else 0.4)), width=2)
    d.rectangle([bx0 + 4, by0 + 4, bx1 - 4, by0 + 22], fill=(15, 20, 32))
    d.text(((bx0 + bx1) / 2, by0 + 13), "BLUE ENV (v2.4.0 STABLE)",
           font=MONOB(9), fill=alpha(BLUE if blue_active else MUTED, a), anchor="mm")

    # 2 Blue Pods inside Blue Cluster
    for pidx in range(2):
        px0 = bx0 + 10 + pidx * 135
        px1 = px0 + 125
        py0, py1 = by0 + 28, by1 - 8
        d.rounded_rectangle([px0, py0, px1, py1], radius=5, fill=(8, 11, 18),
                            outline=alpha(BLUE if blue_active else DIM, a * 0.6), width=1)
        d.ellipse([px0 + 10, py0 + 12, px0 + 18, py0 + 20], fill=alpha(BLUE if blue_active else DIM, a))
        d.text((px0 + 24, py0 + 16), f"pod-b{pidx+1}", font=MONOB(9), fill=alpha(WHITE, a), anchor="lm")
        b_sub = f"{blue_pct}% LOAD" if blue_pct > 0 else "DRAINED / IDLE"
        d.text((px0 + 10, py0 + 32), b_sub, font=MONO(8),
               fill=alpha(BLUE if blue_active else MUTED, a), anchor="lm")

    # Bottom Right: Green Environment Cluster (X: 370 to 650, Y: 796 to 876)
    gx0, gy0, gx1, gy1 = 370, 796, 650, 876
    green_box_col = GREEN if green_active else (RED if beat2 else DIM)
    d.rounded_rectangle([gx0, gy0, gx1, gy1], radius=8, fill=(10, 20, 16) if green_active else (10, 12, 17),
                        outline=alpha(green_box_col, a * (pulse if beat2 else (0.9 if green_active else 0.4))), width=2)
    d.rectangle([gx0 + 4, gy0 + 4, gx1 - 4, gy0 + 22], fill=(13, 26, 20) if green_active else (14, 18, 24))
    d.text(((gx0 + gx1) / 2, gy0 + 13), "GREEN ENV (v2.4.2 CANARY)",
           font=MONOB(9), fill=alpha(green_box_col, a), anchor="mm")

    # 2 Green Pods inside Green Cluster
    for pidx in range(2):
        px0 = gx0 + 10 + pidx * 135
        px1 = px0 + 125
        py0, py1 = gy0 + 28, gy1 - 8
        d.rounded_rectangle([px0, py0, px1, py1], radius=5, fill=(7, 14, 11) if green_active else (8, 10, 15),
                            outline=alpha(green_box_col, a * 0.6), width=1)
        if green_active:
            d.ellipse([px0 + 10, py0 + 12, px0 + 18, py0 + 20], fill=alpha(GREEN, a))
            d.text((px0 + 24, py0 + 16), f"pod-g{pidx+1}", font=MONOB(9), fill=alpha(WHITE, a), anchor="lm")
            g_sub = f"CANARY {canary_pct}%" if canary_pct < 100 else "100% PROMOTED ✓"
            d.text((px0 + 10, py0 + 32), g_sub, font=MONO(8), fill=alpha(GREEN, a), anchor="lm")
        elif beat2:
            d.text(((px0 + px1) / 2, (py0 + py1) / 2), "ABORTED BY CI", font=MONOB(8), fill=alpha(RED, a * pulse), anchor="mm")
        else:
            d.text(((px0 + px1) / 2, (py0 + py1) / 2), "STANDBY", font=MONO(8), fill=alpha(DIM, a), anchor="mm")

    # Live packet pulses flowing through CD router
    if blue_active:
        t_b = (fr * 3) % 40 / 40.0
        bx = lerp(240, 195, t_b)
        by = lerp(768, 796, t_b)
        d.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=alpha(BLUE, a))

    if green_active:
        t_g = (fr * 4) % 30 / 30.0
        gx = lerp(480, 525, t_g)
        gy = lerp(768, 796, t_g)
        d.ellipse([gx - 4, gy - 4, gx + 4, gy + 4], fill=alpha(GREEN, a))

    # Bottom Stage Key Metrics Bar (Y: 888 to 942)
    if beat3:
        d.rounded_rectangle([58, 888, W - 58, 942], radius=7, fill=(9, 24, 16),
                            outline=alpha(GREEN, a * 0.9), width=2)
        d.text((W / 2, 905), "✓ CANARY VERIFIED · 100% TRAFFIC PROMOTED TO GREEN",
               font=MONOB(10), fill=alpha(GREEN, a), anchor="mm")
        d.text((W / 2, 924), "0 DOWNTIME · 0 DROPPED REQUESTS · AUTOMATED ROLLBACK READY",
               font=MONO(9), fill=alpha(WHITE, a), anchor="mm")
    elif beat2:
        d.rounded_rectangle([58, 888, W - 58, 942], radius=7, fill=(28, 10, 14),
                            outline=alpha(RED, a * pulse), width=2)
        d.text((W / 2, 905), "! CRITICAL BUG CONTAINED IN CI TEST STAGE",
               font=MONOB(10), fill=alpha(RED, a * pulse), anchor="mm")
        d.text((W / 2, 924), "PRODUCTION NEVER RECEIVED BROKEN BUILD · 100% UPTIME PRESERVED",
               font=MONO(9), fill=alpha(WHITE, a), anchor="mm")
    else:
        d.rounded_rectangle([58, 888, W - 58, 942], radius=7, fill=(11, 16, 24),
                            outline=alpha(BLUE, a * 0.6), width=1)
        d.text((W / 2, 905), "AUTOMATED DELIVERY: CANARY TRAFFIC SHIFTING (10% → 100%)",
               font=MONOB(10), fill=alpha(TEAL, a), anchor="mm")
        d.text((W / 2, 924), "HEALTH PROBES MONITORED AT 100MS INTERVALS",
               font=MONO(9), fill=alpha(MUTED, a), anchor="mm")


def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)

    intro = ease(fr / 14)
    diag = ease((fr - 8) / 18)
    a = diag

    # 1. Header
    draw_header(d, intro)
    if diag <= 0.01:
        return base

    beat2 = (90 <= fr < 180)
    beat3 = (fr >= 180)

    # 2. Telemetry HUD Cards (Y: 304 to 376)
    if beat3:
        m1_val, m1_col = "48 / DAY", GREEN
        m2_val, m2_col = "0 DOWNTIME", GREEN
        status_line = "✓ FIX VALIDATED · CANARY CUTOVER COMPLETE · PROD 100% HEALTHY"
        stat_col = GREEN
    elif beat2:
        m1_val, m1_col = "BLOCKED [X]", RED
        m2_val, m2_col = "FAIL (GATE)", RED
        status_line = "! TEST REGRESSION DETECTED · CI GATE HALTED DEPLOYMENT"
        stat_col = RED
    else:
        m1_val, m1_col = "AUTOMATED", TEAL
        m2_val, m2_col = "428/428 PASS", TEAL
        status_line = "GIT PUSH TRIGGERED · MULTI-STAGE AUTOMATION PIPELINE ACTIVE"
        stat_col = BLUE

    draw_telemetry_hud(d, "DEPLOY FREQ", m1_val, "PIPELINE HEALTH", m2_val, a, m1_col=m1_col, m2_col=m2_col)

    # Status summary line (Y: 392)
    track(d, (W / 2, 392), status_line, MONOB(9), alpha(stat_col, a), sp=1, anchor="mm")

    # 3. Stage Apparatus (Y: 415 to 948)
    draw_commit_bar(d, fr, a)
    draw_ci_stages(d, fr, a)
    draw_cd_deployment(d, fr, a)

    # 4. Caption Pill (Y: 980 to 1028)
    draw_caption_pill(d, fr, CAPTIONS, a)

    # 5. Outro Footer (After frame 258)
    if fr > 258:
        o = ease((fr - 258) / 20)
        track(d, (W / 2, 1090), "CONTINUOUS INTEGRATION · AUTOMATED CANARY · ZERO DOWNTIME",
              MONOB(10), alpha(TEAL, o), sp=1, anchor="mm")
        track(d, (W / 2, 1112), "GIT · DOCKER · GITHUB ACTIONS · KUBERNETES · ARGO CD",
              MONO(9), alpha(DIM, o), sp=2, anchor="mm")

    return base


def render_and_save_frame(args):
    fr, out_dir = args
    finish(render(fr), fr).save(os.path.join(out_dir, f"f_{fr:04d}.png"))


if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_ci_cd"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, [(fr, out_dir) for fr in frames]))
    print(f"Rendered CI/CD frames: {len(frames)}")
