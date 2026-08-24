# Bespoke Generator Guide

Everything needed to hand-author a flagship reel generator, verify it, and ship it.

## 1. Generator anatomy

File: `engine/generators/<slug>.py`. Fixed skeleton (keep the import block and
`__main__` exactly — `generate.py` drives scripts via `TMP_FRAMES_DIR`):

```python
#!/usr/bin/env python3
"""
Flagship System Design Reel: <Title> (<Apparatus one-liner>)
720x1280 @ 30fps, concept-driven duration (10s default, 30s maximum).
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
    (0,   "<beat 1 hook — the normal state>"),
    (60,  "<early beat 2 — the mechanism of the problem>"),
    (124, "<late beat 2 — quantified pain>"),
    (188, "<beat 3 — the fix activating>"),
    (250, "<beat 3 — quantified win>"),
]

def render(fr):
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)
    intro = ease(fr / 14)
    diag  = ease((fr - 8) / 18)
    a = diag
    # ... header, HUD, stage apparatus, caption pill, outro
    return base

def render_and_save_frame(args):
    fr, out_dir = args
    finish(render(fr), fr).save(os.path.join(out_dir, f"f_{fr:04d}.png"))

if __name__ == "__main__":
    out_dir = os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if (len(sys.argv) > 1 and not sys.argv[1].isdigit()) else os.path.join(os.path.dirname(__file__), "..", "..", "output", "frames_<slug>"))
    os.makedirs(out_dir, exist_ok=True)
    frames = [int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(NF))
    with ProcessPoolExecutor() as executor:
        list(executor.map(render_and_save_frame, [(fr, out_dir) for fr in frames]))
```

## 2. Fixed layout grammar (Y coordinates — collisions are the #1 defect)

| Zone | Y | What |
|---|---|---|
| Header | 160 / 192 / 228 / 264 | handle `@buildebugship` (MONOB 13, RED), comparison tag (track MONOB 11), headline (SANSB 42, white + teal), subhook (SANS 14, BLUE) |
| Telemetry HUD | 304–376 | `draw_telemetry_hud(d, "LATENCY", v1, "THROUGHPUT", v2, a, m1_col=..., m2_col=...)` |
| Status line | ~390 | one-line execution/state summary, color per beat |
| Stage | 415–950 | the bespoke apparatus; the last usable row is a beat-3 takeaway line at Y 944 — nothing below it (the caption pill starts at 980) |
| Caption pill | 980–1028 | `draw_caption_pill(d, fr, CAPTIONS, a)` — never place anything here |
| Outro footer | 1090 / 1112 | two `track` lines after fr 258 (takeaway MONOB 11 TEAL, tool names MONO 10 DIM) |

Header pattern: intro-fade everything with `alpha(col, intro)`; bail out early
(`if diag <= 0.01: return base`) so the first ~8 frames are header-only.

## 3. Beat state machine

```python
beat2, beat3 = fr >= 90, fr >= 180
pulse = 0.55 + 0.45 * math.sin(fr * 0.45)   # alarm flash rate
```

- **Metric choreography**: HUD values and colors flip per beat, e.g. latency
  `0.4ms TEAL → f"{int(lerp(12, 850, ease((fr-90)/85)))}ms" RED → 0.12ms GREEN`.
- **Calibrate counters to the story**: the number on screen at fr 178 must match
  the caption claim. Example: sweep `bar_row = 8.432911 * ease((fr-92)/86)` and
  display `int(bar_row * 1_000_000)` → ends at exactly 8,432,911.
- **Transitions**: elements assemble with `ease((fr - start) / 8)` alpha plus a
  `-12px` y-offset pop; stage re-layouts (e.g. table condensing) with
  `ease((fr - 180) / 20)` lerped geometry.
- Beat 2 opens with a flashing red tag (frames ~90–130) naming the crisis;
  ends with a stamp (~168–196) like `✗ QUERY TIMEOUT — 850ms ELAPSED`.

## 4. Apparatus rules

- One bespoke machine per topic, animated mechanically (sweep, rotation, hop,
  conveyor). Look at existing generators before designing.
- **Seek/travel orbs**: define hops as `(start_fr, end_fr, p0, p1)`; position =
  `lerp` under `ease`; draw trail line while moving, permanent arrow after
  landing (arrowhead via `math.atan2(dy, dx)` with ±2.55 rad barbs).
- Tint checked/passed regions with `alpha(col, 0.14)` overlays; glow = a second,
  wider outline pass. Node pointers = small ellipses at cell boundaries.
- All state must be a pure function of `fr` (no randomness across frames unless
  seeded identically per frame like `np.random.default_rng(42)`).
- For logical architecture, use `engine/diagram.py`: create `ServiceNode`s, read
  named coordinates from `layout().ports`, draw orthogonal connectors first, then
  nodes, and animate packets on the returned path. Use shared text fitting and
  semantic colors. Physical mechanisms keep the bespoke apparatus approach.

## 5. Probe → verify → full render

1. **Glyph safety** for anything beyond ASCII in MONO fonts (`✓ ✗ ⚠ ▸ → · ×` are
   verified safe). Run from the repo root (font paths are root-relative):
   ```bash
   python3 -c "
   from PIL import ImageFont
   f = ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 12)
   print([ch for ch in ['✓','✗','⚠','▸','→','·','×'] if not f.getmask(ch).getbbox()])"
   ```
2. **Probe**: `python3 engine/generators/<slug>.py .tmp_frames/<slug>_test 30 135 240`
   — one frame per beat. Inspect for clipping/overlap; fix geometry and re-probe
   until clean. Rendering extra probes (e.g. `205 258`) is cheap.
3. **Full render**: `python3 engine/generators/<slug>.py .tmp_frames/<slug>`.
4. **Audio**: use the selected duration and proportional beat boundaries (`30%` and `60%`).
5. **Compile** (flags are the house contract from THEME_SPEC.md):
   ```bash
   ffmpeg -y -framerate 30 -i .tmp_frames/<slug>/f_%04d.png -i audio/<slug>.wav \
     -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest \
     -crf 18 -preset fast -movflags +faststart output/video_<slug>.mp4
   ```
6. **Verify**: `ffprobe -v error -show_entries format=duration -show_entries stream=codec_name,width,height,r_frame_rate output/video_<slug>.mp4`
   → expect 720x1280, 30/1, and the selected duration (maximum 30.000000). Then `rm -rf .tmp_frames/<slug>*`.
   Only if a sandboxed Bash run is actually blocked, rerun that command with the
   sandbox disabled — try sandboxed first.

## 6. Register + caption + gallery

- Add a `PRESETS["<slug>"]` entry in `generate.py` (`id`, `title`, `script`,
  `audio`, `output_video`, `caption`) and a routing rule in
  `generate_from_prompt` **before** the generic fallthrough (note:
  `kafka_partitions`, `cold_starts`, `vpn_tunnel`, `streaming_vs_direct`,
  `chatgpt_streaming` presets exist without routing rules — add one whenever a
  prompt should land on them). Validate with
  `python3 -c "import ast; ast.parse(open('generate.py').read())"`.
- Caption txt template: hook line ("<Topic> explained: why X takes A then B"),
  the mechanism, the one-line fix (real SQL/code snippet when applicable), the
  quantified result, a tradeoff, an engagement question,
  "Follow @buildebugship for … explained visually.", 5–9 hashtags.
- Refresh the gallery: `python3 -c "from engine.build_gallery import build_gallery_html; build_gallery_html()"`.

## 7. Pitfalls

- Glyph tofu in MONO fonts → run §5.1 first.
- Y-zone collisions (stage vs caption pill, beat-3 relayout vs counter zone) →
  every element stays in its §2 zone; fade counter zones out over ~10 frames
  when the stage slides into them.
- Numbers on screen contradicting the caption → calibrate (§3).
- Dead code / placeholder polygons left in the generator → keep it clean; it is
  a flagship template others will copy.
