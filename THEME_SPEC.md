# Dark Warm Slate Blueprint — Visual & Audio Theme Specification

## 1. Canvas Dimensions & Video Specification
- **Resolution**: `720 × 1280` (9:16 Vertical Video / Instagram Reels / YouTube Shorts / TikTok)
- **Framerate**: `30 FPS`
- **Total Duration**: concept-driven, required range `15.0–30.0 seconds`; `20.0 seconds` by default
- **Total Frames**: actual duration × 30fps
- **Video Codec**: `H.264 (libx264)`, Pixel Format `yuv420p`, CRF `18`, Preset `fast`
- **Audio Codec**: `AAC @ 192kbps`, 48kHz Mono
- **File Container**: `.mp4` with `+faststart` web optimization

---

## 2. Color Tokens
All RGB color tuples must match these exact design constants:

```python
BG        = (9, 11, 16)      # #090b10 — Deep Warm Slate Canvas
WHITE     = (255, 255, 255)  # #ffffff — Primary Headings, Focus Borders
MUTED     = (148, 163, 184)  # #94a3b8 — Subtitles, Metadata, Section Tags
DIM       = (51, 65, 85)     # #334155 — Rulers, Inactive Grid Lines, Dim Borders
TEAL      = (64, 224, 208)   # #40e0d0 — Fast Throughput, RAM, Encryption, Healthy Nodes
TEAL_D    = (32, 120, 112)   # Dark Teal for Inactive Silicon & Memory Glow
AMBER     = (245, 166, 35)   # #f5a623 — Disk I/O, Queues, Warning States
AMBER_D   = (140, 95, 20)    # Dark Amber for Mechanical Platters
RED       = (251, 113, 133)  # #fb7185 — @buildebugship Branding, Malicious SQL, Overload Alarm
RED_D     = (159, 18, 57)    # Dark Red for Breached Database State
BLUE      = (96, 165, 250)   # #60a5fa — Network Flow, API Gateway Traces
BLUE_D    = (40, 75, 130)    # Dark Blue for Ingest Borders
GREEN     = (52, 211, 153)   # #34d153 — 100% Uptime, Parameterized Queries, Success State
GREEN_D   = (6, 95, 70)      # Dark Green for Scaled Container Tubes
```

---

## 3. Screen Layout Grid (Y: 0 – 1280)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │  Y: 0 - 150 (Top safe zone)
│                     @buildebugship                      │  Y: 168 (Vibrant Red)
│          IN-MEMORY RAM (0.1ms)  vs  DISK I/O (45ms)     │  Y: 192 (Muted Section Tag)
│                      REDIS CACHE                        │  Y: 226 (White & Teal Headline)
│  why in-memory lookups are 375x faster than disk storage│  Y: 262 (Blue Subhook)
│                                                         │
│ ┌──────────────────────┐       ┌──────────────────────┐ │
│ │ LATENCY (REDIS)      │       │ DISK LATENCY (DB)    │ │  Y: 310 - 370 (Telemetry HUD)
│ │ 0.12 ms              │       │ 45.0 ms              │ │
│ └──────────────────────┘       └──────────────────────┘ │
│                                                         │
│ ═══════════════════════════════════════════════════════ │
│                                                         │
│               BESPOKE VISUAL APPARATUS                  │  Y: 400 - 940 (Stage Zone)
│   • RAM Silicon PCB Modules vs Spinning Magnetic Disk   │
│   • Overhead Motorized Crane Rolling Server Containers  │
│   • 3D Isometric Server Racks with Breach Flashers      │
│   • 24-Hour Rotating Dial with 5 Sliding Gates          │
│                                                         │
│ ═══════════════════════════════════════════════════════ │
│                                                         │
│       SYNCHRONIZED GLASS-PILL STORY CAPTION (1–2 lines) │  Y: 972 - 1036
│                                                         │
│                                                         │  Y: 1040 - 1280 (Bottom safe zone)
└─────────────────────────────────────────────────────────┘
```

---

## 4. Scene-Synchronized Sound Design Specification (Zero Voiceover)

- **Zero Voiceover / No TTS**: Pure procedural sound effects and music.
- **Mandatory Cue Sheet**: Every scene selects `network`, `mechanical`, `storage`,
  `security`, `compute`, or `protocol`, with at least one normalized cue in each of
  the 0–30%, 30–60%, and 60–100% narrative beats.
- **Cue Vocabulary**: `blip`, `packet`, `tick`, `queue`, `alarm`, `latch`, `sweep`,
  `processing`, `impact`, and `success`; intensity defaults to `0.5`.
- **Profile Score**: Harmony, rhythm, and timbre follow the selected profile and
  optional 40–240 BPM tempo. Cue SFX variants align exactly to scene event times.
- **Determinism**: Topic plus canonical cue sheet derives the stable seed. Identical
  scene inputs produce identical PCM; different topics or cue sheets change it.
- **Burned-In Story Captions**: Exactly three non-empty captions follow the 0–30%,
  30–60%, and 60–100% beats in a responsive one- or two-line glass pill below the
  apparatus. Separate social posting copy continues to ship as `caption.txt`.

---

## 5. Headline Composition

- `title_left` and `title_right` retain the two-color headline treatment.
- `title_connector` defaults to an empty string and reserves no space when empty.
- Set `title_connector` to `vs` only for a genuine comparison headline.

---

## 6. Hybrid Visual Grammar

Use `engine/diagram.py` for architecture, protocols, dependencies, and logical
flows. Continue using bespoke isometric machinery for physical concepts. This is
opt-in: existing generators stay visually stable until deliberately redesigned.

- Connectors render before nodes and attach only through named ports returned by
  `ServiceNode.layout()`.
- Logical routes are orthogonal; diagonals are reserved for physical apparatuses.
- Every service has a recognizable procedural icon or silhouette.
- State colors are semantic: Blue=request, Amber=waiting, Red=failure,
  Teal=protocol, Green=successful result.
- Connector APIs return their paths for packet animation and audio synchronization.
- Shared wrapping, truncation, padding, and minimum sizes keep all text contained.
- Use an 8px spacing rhythm, 1–3px strokes, 8–18px radii, and restrained glow.
