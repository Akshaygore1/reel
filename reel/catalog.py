"""Build ignored output/catalog.js for the tracked file:// gallery shell."""
from __future__ import annotations

import json
from pathlib import Path

from .runs import OUTPUT_DIR, list_runs


def javascript_json(value) -> str:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            .replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def build_catalog() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for manifest in list_runs():
        run_id = manifest["run_id"]
        run_dir = OUTPUT_DIR / run_id
        caption_path = run_dir / manifest["caption"]
        entries.append({
            **manifest,
            "video_url": f"output/{run_id}/{manifest['video']}",
            "poster_url": f"output/{run_id}/{manifest['poster']}",
            "caption_text": caption_path.read_text(encoding="utf-8") if caption_path.exists() else "",
            "size_bytes": (run_dir / manifest["video"]).stat().st_size if (run_dir / manifest["video"]).exists() else 0,
        })
    path = OUTPUT_DIR / "catalog.js"
    path.write_text(f"window.REEL_CATALOG={javascript_json(entries)};\n", encoding="utf-8")
    return path

