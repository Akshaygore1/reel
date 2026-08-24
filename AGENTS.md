# Blueprint Reel Harness

Create local, zero-voiceover system-design reels in the locked dark warm-slate
blueprint style. Ordinary generation must not modify tracked source files.

## Canonical workflow

1. Check the environment: `python3 -m reel doctor`.
2. Reuse a flagship only when it already matches: `python3 generate.py --preset <key>`.
3. For a new topic, run `python3 -m reel scaffold "<topic>" --json`.
4. Author the bespoke physical/geometric apparatus in `.work/<run-id>/scene.py`.
   SceneV2 receives only a clipped 624×550 stage surface and normalized frame context.
   Choose 15s for simple mechanisms, 20s for standard three-beat explanations, 25s
   for multi-stage comparisons, or 30s for dense protocols. Add a mandatory
   profile-specific normalized audio cue sheet with at least one cue in every beat.
5. Inspect all beats with `python3 -m reel probe <run-id>`, then render with
   `python3 -m reel render <run-id>`.
6. Deliver `output/<run-id>/video.mp4`, `caption.txt`, and the manifest specs.

Use the generic compatibility path only when the user explicitly asks for quick mode:
`python3 generate.py --prompt "<topic>"`.

Never register an ordinary run or write into `engine/generators/`. Only
`python3 -m reel promote <run-id>` may intentionally create reusable tracked source,
and it requires explicit confirmation plus the full validation suite.

The engine owns branding, header, HUD, caption-free breathing room, footer, timing,
cue-sheet audio, compilation, verification, and output promotion. Reel duration is
15–30 seconds with a 20-second fallback. Posting copy stays in `caption.txt` and is
never burned into frames. Visual/audio grammar stays locked; brand fields come from
`reel.config.json`. Runs are immutable and are deleted only through the confirmed CLI command.
