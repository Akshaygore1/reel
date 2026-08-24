"""Run identity, safe paths, manifests, migration, cleanup, and atomic promotion."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
WORK_DIR = ROOT / ".work"
RUN_ID_RE = re.compile(r"^\d{8}T\d{6}Z-[a-z0-9]+(?:-[a-z0-9]+)*-[a-f0-9]{6}$")
RESOLUTIONS = {
    "720p": (720, 1280),
    "1080p": (1080, 1920),
    "2160p": (2160, 3840),
}
MIN_DURATION = 15.0
DEFAULT_DURATION = 20.0
MAX_DURATION = 30.0


def slugify(value: str, limit: int = 42) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:limit].rstrip("-")
    return slug or "reel"


def new_run_id(topic: str, now: datetime | None = None, token: str | None = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{slugify(topic)}-{token or secrets.token_hex(3)}"


def validate_run_id(run_id: str) -> str:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError(f"invalid run id: {run_id!r}")
    return run_id


def safe_child(parent: Path, name: str) -> Path:
    validate_run_id(name)
    parent_resolved = parent.resolve()
    child = (parent / name).resolve()
    if child.parent != parent_resolved:
        raise ValueError("run path escapes its parent")
    return child


def work_path(run_id: str) -> Path:
    return safe_child(WORK_DIR, run_id)


def output_path(run_id: str) -> Path:
    return safe_child(OUTPUT_DIR, run_id)


def validate_duration(value: float | int | None) -> float:
    duration = DEFAULT_DURATION if value is None else float(value)
    if not MIN_DURATION <= duration <= MAX_DURATION:
        raise ValueError(f"duration must be between {MIN_DURATION:g} and {MAX_DURATION:g} seconds")
    return duration


def _validate_legacy_duration(value: float | int) -> float:
    """Schema-v1 media predates the current authoring duration policy."""
    duration = float(value)
    if not 0 < duration <= MAX_DURATION:
        raise ValueError(f"legacy duration must be greater than 0 and at most {MAX_DURATION:g} seconds")
    return duration


def resolution_size(name: str) -> tuple[int, int]:
    try:
        return RESOLUTIONS[name]
    except KeyError as exc:
        raise ValueError(f"unsupported resolution: {name}") from exc


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(data: dict) -> dict:
    required = {"schema_version", "run_id", "topic", "created_at", "status", "mode",
                "duration", "fps", "resolution", "video", "caption", "poster", "scene",
                "brief", "audio_profile"}
    missing = sorted(required - set(data))
    if missing:
        raise ValueError(f"manifest missing fields: {', '.join(missing)}")
    validate_run_id(data["run_id"])
    if data["schema_version"] == 1:
        _validate_legacy_duration(data["duration"])
    else:
        validate_duration(data["duration"])
    resolution_size(data["resolution"])
    if data["fps"] != 30:
        raise ValueError("FPS is locked to 30")
    if data["status"] != "complete":
        raise ValueError("only complete manifests may be published")
    if data["schema_version"] >= 2:
        audio = data.get("audio")
        audio_required = {"profile", "seed", "cue_count", "voiceover"}
        if not isinstance(audio, dict) or not audio_required <= set(audio):
            raise ValueError("schema-v2 manifest requires structured audio metadata")
        if audio["voiceover"] is not False or audio["cue_count"] < 3:
            raise ValueError("schema-v2 audio metadata must describe cue-driven zero-voiceover audio")
    return data


def atomic_promote(staging: Path, run_id: str) -> Path:
    """Atomically publish a complete staging directory without overwriting a run."""
    destination = output_path(run_id)
    if destination.exists():
        raise FileExistsError(f"run already exists: {run_id}")
    manifest = validate_manifest(read_json(staging / "manifest.json"))
    if manifest["run_id"] != run_id:
        raise ValueError("manifest run id does not match the destination run id")
    for name in (manifest["video"], manifest["caption"], manifest["poster"], manifest["scene"], manifest["brief"]):
        if Path(name).name != name or not (staging / name).is_file():
            raise ValueError(f"staging is missing safe run artifact: {name}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    os.replace(staging, destination)
    return destination


def list_runs() -> list[dict]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    runs = []
    for manifest in OUTPUT_DIR.glob("*/manifest.json"):
        try:
            runs.append(read_json(manifest))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return sorted(runs, key=lambda item: item["created_at"], reverse=True)


def delete_run(run_id: str) -> Path:
    target = output_path(run_id)
    if not target.is_dir():
        raise FileNotFoundError(f"run not found: {run_id}")
    shutil.rmtree(target)
    return target


def clean_work() -> int:
    if not WORK_DIR.exists():
        return 0
    count = sum(1 for path in WORK_DIR.iterdir() if path.is_dir())
    shutil.rmtree(WORK_DIR)
    return count


def migrate_legacy() -> list[str]:
    """Move flat video_*.mp4/.txt pairs into run directories without re-encoding."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    migrated: list[str] = []
    for video in sorted(OUTPUT_DIR.glob("video_*.mp4")):
        topic = video.stem.removeprefix("video_").replace("_", " ")
        run_id = new_run_id(topic)
        target = output_path(run_id)
        target.mkdir()
        video.replace(target / "video.mp4")
        caption_source = video.with_suffix(".txt")
        caption = caption_source.read_text(encoding="utf-8") if caption_source.exists() else topic
        if caption_source.exists():
            caption_source.unlink()
        (target / "caption.txt").write_text(caption, encoding="utf-8")
        (target / "scene.py").write_text("# Legacy media migration; original scene unavailable.\n", encoding="utf-8")
        write_json(target / "brief.json", {"topic": topic, "mode": "legacy-migration"})
        duration, resolution = 10.0, "720p"
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
                 "-select_streams", "v:0", "-of", "json", str(target / "video.mp4")],
                check=True, capture_output=True, text=True,
            )
            media = json.loads(result.stdout)
            duration = min(MAX_DURATION, float(media["format"]["duration"]))
            dimensions = (media["streams"][0]["width"], media["streams"][0]["height"])
            resolution = next((name for name, size in RESOLUTIONS.items() if size == dimensions), "720p")
        except (OSError, KeyError, IndexError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError):
            pass
        try:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{duration * .7:.3f}",
                            "-i", str(target / "video.mp4"), "-frames:v", "1", str(target / "poster.jpg")],
                           check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError):
            # A valid tiny JPEG fallback keeps the run kit self-contained.
            from PIL import Image
            Image.new("RGB", (360, 640), (9, 11, 16)).save(target / "poster.jpg")
        created = datetime.fromtimestamp((target / "video.mp4").stat().st_mtime, timezone.utc).isoformat()
        manifest = {
            "schema_version": 1, "run_id": run_id, "topic": topic, "created_at": created,
            "status": "complete", "mode": "legacy-migration", "duration": duration, "fps": 30,
            "resolution": resolution, "video": "video.mp4", "caption": "caption.txt",
            "poster": "poster.jpg", "scene": "scene.py", "brief": "brief.json",
            "audio_profile": "Procedural Game SFX + Lo-Fi Ambient Synth; Zero Voiceover",
        }
        write_json(target / "manifest.json", manifest)
        migrated.append(run_id)
    return migrated
