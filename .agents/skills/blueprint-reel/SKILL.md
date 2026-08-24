---
name: blueprint-reel
description: Produce dark warm-slate blueprint system-design reels with the local Python SceneV2 run harness, procedural game SFX, ambient synth, and zero voiceover.
---

# Blueprint Reel Creator

Everything is local: Pillow frames, NumPy audio, FFmpeg compilation. Read
`THEME_SPEC.md`, `engine/blueprint_engine.py`, `engine/diagram.py`, and the relevant
existing generator before authoring a scene.

## Route and build

- Existing exact preset: `python3 generate.py --preset <key>`.
- Explicit quick/generic request: `python3 generate.py --prompt "<topic>"`.
- New topic by default: `python3 -m reel scaffold "<topic>" --json`, edit only the
  resulting `.work/<run-id>/scene.py`, probe, then render.

SceneV2 is deliberately constrained: the engine owns canvas, header, telemetry,
synchronized lower story-caption pill, footer, branding, 30/60 beat boundaries, audio synchronization,
multiprocessing, FFmpeg, FFprobe, and atomic publication. Scene code receives a
clipped stage surface plus `FrameContext` with normalized progress, beat, beat
progress, stage bounds, and locked theme tokens.

Never add an ordinary scene to `engine/generators/` or edit a registry. Preserve
multiple treatments of the same topic as separate run IDs. The generic quick path
must never be presented as a bespoke flagship treatment.

## Visual and sound requirements

- Three beats: normal 0–30%, crisis 30–60%, resolution 60–100%.
- Use one mechanically animated, topic-specific apparatus; no generic box diagrams.
- Logical architecture may use `engine/diagram.py`; physical concepts use bespoke
  machinery. All animation is a pure function of frame context.
- Locked blueprint palette and layout; configurable brand fields are in
  `reel.config.json`.
- Every `SCENE` defines a deterministic cue sheet using a profile (`network`,
  `mechanical`, `storage`, `security`, `compute`, or `protocol`) and normalized
  events. Use only `blip`, `packet`, `tick`, `queue`, `alarm`, `latch`, `sweep`,
  `processing`, `impact`, or `success`, with at least one cue in every beat.
- Every `SCENE` defines exactly three non-empty story captions for the 0–30%,
  30–60%, and 60–100% beats. These are burned into the lower glass pill; posting
  copy remains separate in `caption.txt`.
- Headlines use `title_left` and `title_right`. `title_connector` defaults to blank;
  set it to `vs` only for a genuine comparison.
- Default 720×1280 at 30fps for 20 seconds. Choose 15s for a simple mechanism, 20s
  for a standard three-beat explanation, 25s for a multi-stage comparison, and 30s
  for a dense protocol. Values outside 15–30 seconds are invalid.

## Verify and deliver

Run `python3 -m reel probe <run-id>` and visually inspect all three PNGs. Then run
`python3 -m reel render <run-id>` and `python3 -m reel inspect <run-id>`. Deliver
clickable links to the packaged video and caption, the verified manifest specs, and
the full caption with attribution. Refreshes affect only ignored `output/catalog.js`.

Only use `python3 -m reel promote <run-id>` when the user explicitly wants a run
converted into reusable tracked source; confirmation and the full test suite are
mandatory.
