# System Design Reels — Blueprint Video Engine (100% Python)

High-performance video generation engine for 9:16 vertical system-design reels with dark warm-slate blueprint graphics, procedural game SFX, ambient lo-fi synth, zero voiceover, and social captions.

---

## ⚡ Quickstart — Generate Videos with a Single Prompt

### 1. Generate a Concept-Driven Video (up to 30s)
Generate a full 9:16 vertical video, synchronized procedural audio, and caption with a single prompt. Reels default to 10 seconds; use `--duration` when the explanation needs more room:
```bash
python3 generate.py --prompt "Database Sharding vs Partitioning"
python3 generate.py --prompt "Model Context Protocol" --duration 18
```

`--duration` accepts any positive duration and safely caps it at 30 seconds.

### 2. Generate Built-in Core Flagship Reels
List the 4 core presets:
```bash
python3 generate.py --list
```
Build a specific reel preset in ~2.5 seconds:
```bash
python3 generate.py --preset sql_injection
python3 generate.py --preset redis_vs_db
python3 generate.py --preset autoscaling
python3 generate.py --preset cron_jobs
```
Or build all 4 core reels:
```bash
python3 generate.py --preset all
```

### 3. Clean Workspace
```bash
python3 generate.py --clean
```

---

## 📁 Clean Repository Structure

```
reels/
├── THEME_SPEC.md             # Visual design system & animation specification
├── README.md                 # Single-prompt generation guide & documentation
├── generate.py               # Pure Python Master CLI (single-prompt & preset generator)
│
├── engine/                   # Core video & audio synthesis engine
│   ├── blueprint_engine.py   # Base 9:16 rendering primitives & layout tokens
│   ├── pro_audio.py          # Neural TTS voiceover & warm ambient music synthesizer
│   └── generators/           # Modular visual generators
│       ├── sql_injection.py  # 1. SQL Injection (3D Server Racks & Breach Alarm)
│       ├── redis_vs_db.py    # 2. Redis vs DB (Silicon DRAM vs Magnetic Disk)
│       ├── autoscaling.py    # 3. Autoscaling (Pachinko Drops & Crane Scaler)
│       ├── cron_jobs.py      # 4. Cron Jobs (24-Hour Dial & 5 Sliding Gates)
│       └── custom_blueprint.py # Dynamic generator for AI-generated scripts/prompts
│
├── fonts/                    # High-legibility typography (Inter, JetBrains Mono, DejaVu)
├── audio/                    # 4 Core master audio tracks (.wav)
└── output/                   # 4 Core finished MP4s + Instagram captions (.txt)
    ├── video_sql_injection.mp4 / .txt
    ├── video_redis_vs_db.mp4 / .txt
    ├── video_autoscaling.mp4 / .txt
    └── video_cron_jobs.mp4 / .txt
```

---

## 🎨 Theme & Style Specification

The exact visual tokens, canvas layout, audio mixing, and 3-beat storytelling rules are logged in **[`THEME_SPEC.md`](file:///Users/akshay/Desktop/reels/THEME_SPEC.md)**.
