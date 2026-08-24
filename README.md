# Blueprint Reel Harness

A local, cross-platform Python harness for 9:16 system-design reels. Pillow renders
the caption-free blueprint visuals, NumPy synthesizes scene-synchronized zero-voiceover
game SFX and ambient music,
and FFmpeg compiles verified H.264/AAC videos.

## Setup

```bash
python3 -m venv .venv
# Activate it: source .venv/bin/activate (macOS/Linux)
#          or: .venv\Scripts\activate (Windows)
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
python -m reel doctor
```

FFmpeg and FFprobe must be installed on `PATH`.

## New bespoke run

```bash
python3 -m reel scaffold "Consistent Hashing" --json
# edit .work/<run-id>/scene.py
python3 -m reel probe <run-id>
python3 -m reel render <run-id>
```

Every new reel must be 15–30 seconds. Choose 15 seconds for a simple mechanism,
20 for a standard three-beat explanation (the fallback), 25 for a multi-stage
comparison, and 30 for a dense protocol. Each `SCENE` must also declare an `audio`
cue sheet with at least one normalized cue in every narrative beat:

```python
SCENE["audio"] = {
    "profile": "network",  # network|mechanical|storage|security|compute|protocol
    "tempo_bpm": 100,      # optional; the profile default is used when omitted
    "events": [
        {"at": 0.12, "kind": "packet", "intensity": 0.6},
        {"at": 0.34, "kind": "alarm", "intensity": 0.8},
        {"at": 0.64, "kind": "success", "intensity": 0.7},
    ],
}
```

Cue kinds are `blip`, `packet`, `tick`, `queue`, `alarm`, `latch`, `sweep`,
`processing`, `impact`, and `success`; intensity defaults to `0.5`. Invalid or
incomplete plans fail before frames render. Frames contain no posting-caption text,
while every output kit still includes a populated `caption.txt`.

Successful runs are immutable kits under `output/<run-id>/` containing `video.mp4`,
`caption.txt`, `manifest.json`, `poster.jpg`, `brief.json`, and `scene.py`. Heavy
frames and WAVs live under ignored `.work/` and are removed after successful renders.

## Commands

```text
python3 -m reel doctor
python3 -m reel presets
python3 -m reel scaffold "<topic>" [--duration N] [--resolution 720p|1080p|2160p] --json
python3 -m reel probe <run-id>
python3 -m reel render <run-id> [--keep-work]
python3 -m reel runs [--json]
python3 -m reel inspect <run-id> [--json]
python3 -m reel delete <run-id> [--yes]
python3 -m reel clean
python3 -m reel migrate-legacy
python3 -m reel promote <run-id> [--yes]
```

`generate.py` remains a compatibility wrapper for legacy presets and flags. Open
`gallery.html` directly; it reads ignored `output/catalog.js` and never rewrites
tracked HTML.
