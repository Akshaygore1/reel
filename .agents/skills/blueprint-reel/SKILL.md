---
name: blueprint-reel
description: Produce @buildebugship dark warm-slate blueprint system-design reel videos (720x1280, 30fps, up to 30s, procedural game SFX, zero voiceover) with this repo's 100% Python engine. Use whenever the user asks to create, make, or generate a video, reel, short, or animation about any system design, backend, database, caching, networking, distributed-systems, security, or cloud topic — including casual phrasing like "video on X", "do a reel about X", or just a topic name.
---

# Blueprint Reel Creator

Turn any technical topic into a flagship-grade 9:16 reel. Everything is local:
PIL frame rendering → numpy procedural audio → FFmpeg compile. No external APIs.

All repo file paths mentioned in this skill (`THEME_SPEC.md`, `engine/…`,
`generate.py`, `output/…`) are relative to the **workspace root**, not the skill
directory. Only `references/` lives inside the skill.

## Read before building

- `THEME_SPEC.md` — canvas spec, exact color tokens, Y-zone layout grid, sound design. Never invent colors; import them from `engine/blueprint_engine.py`.
- `engine/blueprint_engine.py` — shared helpers: `draw_telemetry_hud`, `draw_caption_pill`, `track`, `alpha`, `ease`, `lerp`, font lambdas.
- `engine/diagram.py` — polished nodes, named ports, orthogonal connectors,
  packets, protocol buses, groups, prompts, and result panels for logical flows.
- `engine/generators/database_indexing.py` — the most complete recent exemplar (3-beat state machine, calibrated counters, seek-orb hops).
- `engine/generators/redis_vs_db.py` — a simpler exemplar.

## Route the request

1. **Topic already has a preset** (check the `PRESETS` dict in `generate.py` — e.g. `autoscaling`, `redis_vs_db`, `sql_injection`, `cron_jobs`, `database_indexing`): run `python3 generate.py --preset <key>` (add `--hd` for 1080x1920). Deliver.
2. **User explicitly wants the quick generic path** (`--prompt`): run `python3 generate.py --prompt "<topic>"`. Deliver.
3. **Default for any new topic**: build a **bespoke flagship reel** — hand-author the generator, verify per beat, compile, register. Follow `references/bespoke-generator-guide.md` end to end. Never ship the generic two-boxes blueprint when a real reel was asked for.

## Non-negotiables

- **3-beat narrative**: normal state at 0–30%, crisis at 30–60%, resolution at 60–100%. Default to 10s; use more time when the concept needs it, up to the 30s cap. Audio events follow the same proportional boundaries.
- **Hybrid visual grammar**: architecture and flowcharts use `engine/diagram.py`;
  physical concepts use bespoke apparatuses (spinning platters, cranes, hash
  rings, B-trees, token buckets…). Draw connectors below nodes, attach through
  named ports, reserve diagonals for physical perspective, and never ship plain
  rectangles talking to each other.
- **Zero voiceover.** Audio comes only from `engine.sfx_audio.build_game_soundtrack(path, duration=duration, beat1_end=duration*.30, beat2_end=duration*.60)`.
- **Brand**: `@buildebugship` red `#fb7185` header, caption pill via `draw_caption_pill`, outro footer lines after frame 258.
- **Output contract**: concept-driven frame sequence → `output/video_<slug>.mp4` (720x1280, 30fps, maximum 30.000s) + `output/video_<slug>.txt` viral caption.

## Verify before delivering

- Probe one frame per beat: `python3 engine/generators/<slug>.py .tmp_frames/<slug>_test 30 135 240`, then inspect each frame for clipping/overlap (Read the PNGs; vision analysis is best-effort — don't block on rate limits).
- After compiling, `ffprobe` must report 720x1280, `30/1`, and the requested duration (never above `30.000000`).
- Register the reel as a `PRESETS` entry + routing rule in `generate.py` so future prompts reuse it, and refresh the gallery via `engine.build_gallery.build_gallery_html()`.

## Deliver

Clickable `file://` links to the mp4 and txt, a spec line with the actual duration (maximum 30s), and the full caption text with `@buildebugship`.
