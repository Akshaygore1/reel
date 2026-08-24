"""SceneV2 rendering plus the legacy-preset adapter."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

from PIL import Image, ImageDraw

from engine import blueprint_engine as bp
from .audio import build_scene_soundtrack, stable_audio_seed, validate_audio_plan
from .config import load_brand
from .models import STAGE_BOUNDS, StageSurface, frame_context
from .runs import (DEFAULT_DURATION, MAX_DURATION, MIN_DURATION, ROOT, atomic_promote, new_run_id, resolution_size,
                   validate_duration, validate_run_id, work_path, write_json)

FPS = 30
AUDIO_PROFILE = "Remastered Game SFX + Lo-Fi Ambient Synth; Zero Voiceover"


SCENE_TEMPLATE = '''"""Run-local SceneV2: {topic}. Edit only draw_stage and SCENE content."""
import math
from reel.models import StageSurface, FrameContext
from engine import blueprint_engine as bp

SCENE = {scene_json}

def draw_stage(surface: StageSurface, context: FrameContext) -> None:
    """Bespoke three-beat apparatus, using stage-local coordinates (624x550)."""
    d = surface.draw
    t, beat = context.progress, context.beat
    col = bp.BLUE if beat == 1 else (bp.RED if beat == 2 else bp.GREEN)
    pulse = .65 + .35 * math.sin(context.frame * .35)
    # A physical routing rotor: packets orbit, overload jams it, shards resolve it.
    cx, cy, radius = 312, 250, 150
    d.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], outline=bp.alpha(col, pulse), width=4)
    for i in range(12):
        angle = i * math.tau / 12 + t * math.tau * (1 if beat != 2 else .08)
        x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        r = 9 if beat < 3 else 12
        d.ellipse([x-r, y-r, x+r, y+r], fill=bp.alpha(col, .9), outline=bp.WHITE)
    spokes = 1 if beat < 3 else 4
    for i in range(spokes):
        a = i * math.tau / spokes
        d.line([(cx, cy), (cx + radius * math.cos(a), cy + radius * math.sin(a))], fill=bp.alpha(col, .7), width=3)
    d.ellipse([cx-44, cy-44, cx+44, cy+44], fill=(14,18,26,255), outline=col, width=3)
    d.text((cx, cy), "JAM" if beat == 2 else ("1 NODE" if beat == 1 else "4 SHARDS"),
           font=bp.MONOB(13), fill=bp.WHITE, anchor="mm")
    status = "PACKETS FLOW" if beat == 1 else ("10x LOAD · ROTOR STALL" if beat == 2 else "HASH ROUTES · LOAD SPLITS")
    d.text((cx, 476), status, font=bp.MONOB(13), fill=col, anchor="mm")
'''


def _default_scene(topic: str) -> dict:
    title_words = topic.upper().split()
    return {
        "topic": topic,
        "comparison": "BASELINE  vs  RESILIENT DESIGN",
        "title_left": " ".join(title_words[:2])[:18] or "SYSTEM",
        "title_right": "BLUEPRINT",
        "subhook": f"how {topic.lower()} behaves under production load"[:78],
        "hud": ["LATENCY", "0.4ms", "THROUGHPUT", "12k req/s"],
        "captions": [
            "normal traffic moves through one deterministic path.",
            "a 10x spike saturates the mechanism and queues explode.",
            "the architecture partitions work and restores healthy flow.",
        ],
        "audio": {
            "profile": "network",
            "tempo_bpm": 100,
            "events": [
                {"at": .12, "kind": "packet", "intensity": .6},
                {"at": .34, "kind": "alarm", "intensity": .8},
                {"at": .64, "kind": "success", "intensity": .7},
            ],
        },
        "footer": "MEASURE · BREAK · REDESIGN · VERIFY",
    }


def _audio_metadata(topic: str, audio: dict) -> dict:
    plan = validate_audio_plan(audio)
    return {
        "profile": plan.profile, "tempo_bpm": plan.tempo_bpm,
        "seed": stable_audio_seed(topic, plan), "cue_count": len(plan.events),
        "voiceover": False,
    }


def create_run(topic: str, duration: float = DEFAULT_DURATION, resolution: str = "720p",
               mode: str = "bespoke", preset: str | None = None,
               audio_plan: dict | None = None) -> dict:
    duration = validate_duration(duration)
    resolution_size(resolution)
    run_id = new_run_id(topic)
    run_work = work_path(run_id)
    run_work.mkdir(parents=True, exist_ok=False)
    scene = _default_scene(topic)
    if audio_plan is not None:
        scene["audio"] = audio_plan
    brief = {
        "schema_version": 2, "run_id": run_id, "topic": topic, "mode": mode,
        "preset": preset, "duration": duration, "resolution": resolution, "fps": FPS,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "narrative": {"beat_1": "normal state", "beat_2": "crisis", "beat_3": "architecture resolution"},
        "constraints": {"stage_bounds": list(STAGE_BOUNDS), "zero_voiceover": True,
                        "min_duration": MIN_DURATION, "max_duration": MAX_DURATION,
                        "burned_in_captions": False},
        "audio": _audio_metadata(topic, scene["audio"]),
    }
    write_json(run_work / "brief.json", brief)
    source = SCENE_TEMPLATE.format(topic=topic.replace('"', "'"), scene_json=repr(scene))
    (run_work / "scene.py").write_text(source, encoding="utf-8")
    return brief


def _load_scene(scene_path: Path):
    name = f"reel_run_{scene_path.parent.name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(name, scene_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scene: {scene_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not isinstance(getattr(module, "SCENE", None), dict) or not callable(getattr(module, "draw_stage", None)):
        raise ValueError("scene.py must define SCENE and draw_stage(surface, context)")
    return module


def _draw_chrome(base: Image.Image, scene: dict, frame: int, frame_count: int) -> None:
    d = ImageDraw.Draw(base)
    ctx = frame_context(frame, frame_count)
    intro = bp.ease(frame / max(1, int(FPS * .45)))
    brand = load_brand()
    accent_hex = brand.accent.lstrip("#")
    brand_accent = tuple(int(accent_hex[index:index + 2], 16) for index in (0, 2, 4))
    bp.draw_header_bar(
        d, intro, handle=brand.handle,
        comp_left=scene.get("comparison", "BASELINE vs RESILIENT").split("vs")[0].strip(),
        comp_right=scene.get("comparison", "BASELINE vs RESILIENT").split("vs")[-1].strip(),
        title1=scene.get("title_left", "SYSTEM"), title_vs="vs",
        title2=scene.get("title_right", "BLUEPRINT"), subhook=scene.get("subhook", ""),
        brand_accent=brand_accent,
    )
    hud = scene.get("hud", ["LATENCY", "0.4ms", "THROUGHPUT", "12k req/s"])
    if ctx.beat == 2:
        values, colors = [hud[0], "850ms", hud[2], "QUEUEING"], [bp.RED, bp.RED]
    elif ctx.beat == 3:
        values, colors = [hud[0], "0.12ms", hud[2], "150k req/s"], [bp.GREEN, bp.GREEN]
    else:
        values, colors = hud, [bp.TEAL, bp.BLUE]
    bp.draw_telemetry_hud(d, *values, intro, m1_col=colors[0], m2_col=colors[1])
    if ctx.progress >= .86:
        out = bp.ease((ctx.progress - .86) / .1)
        bp.track(d, (bp.W / 2, 1090), scene.get("footer", "SYSTEM DESIGN BLUEPRINT"), bp.MONOB(11), bp.alpha(bp.TEAL, out), sp=2, anchor="mm")
        bp.track(d, (bp.W / 2, 1112), "PROCEDURAL SFX · ZERO VOICEOVER", bp.MONO(10), bp.alpha(bp.DIM, out), sp=2, anchor="mm")


def render_scene_frame(scene_path: str, frame: int, frame_count: int, destination: str) -> str:
    module = _load_scene(Path(scene_path))
    base = Image.new("RGB", (bp.W, bp.H), bp.BG)
    _draw_chrome(base, module.SCENE, frame, frame_count)
    surface = StageSurface()
    module.draw_stage(surface, frame_context(frame, frame_count))
    base.paste(surface.image, STAGE_BOUNDS[:2], surface.image)
    bp.finish(base, frame).save(destination)
    return destination


def _frame_task(args):
    return render_scene_frame(*args)


def probe_run(run_id: str) -> list[Path]:
    run_work = work_path(run_id)
    brief = json.loads((run_work / "brief.json").read_text(encoding="utf-8"))
    validate_duration(brief["duration"])
    module = _load_scene(run_work / "scene.py")
    validate_audio_plan(module.SCENE.get("audio"))
    frame_count = max(3, round(brief["duration"] * FPS))
    probe_dir = run_work / "diagnostics" / "probes"
    probe_dir.mkdir(parents=True, exist_ok=True)
    frames = [int(frame_count * .15), int(frame_count * .45), min(frame_count - 1, int(frame_count * .78))]
    paths = []
    for beat, frame in enumerate(frames, 1):
        path = probe_dir / f"beat-{beat}.png"
        render_scene_frame(str(run_work / "scene.py"), frame, frame_count, str(path))
        paths.append(path)
    return paths


def _compile(frames: Path, audio: Path, video: Path, duration: float, resolution: str) -> None:
    width, height = resolution_size(resolution)
    filters = [] if resolution == "720p" else [f"scale={width}:{height}:flags=lanczos"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
           "-i", str(frames / "f_%04d.png"), "-i", str(audio)]
    if filters:
        cmd += ["-vf", ",".join(filters)]
    cmd += ["-t", f"{duration:.6f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-crf", "18",
            "-preset", "fast", "-movflags", "+faststart", str(video)]
    subprocess.run(cmd, cwd=ROOT, check=True)


def inspect_video(video: Path) -> dict:
    cmd = ["ffprobe", "-v", "error", "-show_entries",
           "format=duration:stream=codec_name,codec_type,width,height,r_frame_rate",
           "-of", "json", str(video)]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def _verify(video: Path, duration: float, resolution: str) -> dict:
    probe = inspect_video(video)
    width, height = resolution_size(resolution)
    streams = probe.get("streams", [])
    visual = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    actual = float(probe["format"]["duration"])
    if not visual or (visual.get("width"), visual.get("height")) != (width, height):
        raise RuntimeError("compiled video dimensions do not match the run brief")
    if visual.get("r_frame_rate") != "30/1" or not audio:
        raise RuntimeError("compiled video must contain 30fps video and an audio stream")
    if actual > MAX_DURATION + .001 or abs(actual - duration) > .001:
        raise RuntimeError(f"compiled duration {actual:.3f}s does not match {duration:.3f}s")
    return probe


def _caption(topic: str) -> str:
    brand = load_brand()
    return (f"{topic} explained as a three-beat system design blueprint.\n\n"
            "Watch the normal path, the production bottleneck, and the architecture change that restores healthy flow.\n\n"
            f"{brand.cta}\n\n#systemdesign #backend #architecture #devops #distributedSystems\n"
            f"\n{brand.caption_attribution}")


def _publish(run_id: str, brief: dict, staging: Path, scene_source: Path,
             video: Path, caption: str, poster_source: Path, mode: str, probe: dict,
             audio_metadata: dict) -> Path:
    staging.mkdir(parents=True, exist_ok=False)
    shutil.move(str(video), staging / "video.mp4")
    (staging / "caption.txt").write_text(caption, encoding="utf-8")
    shutil.copy2(scene_source, staging / "scene.py")
    shutil.copy2(work_path(run_id) / "brief.json", staging / "brief.json")
    if poster_source.exists():
        Image.open(poster_source).convert("RGB").save(staging / "poster.jpg", quality=88)
    else:
        Image.new("RGB", resolution_size(brief["resolution"]), bp.BG).save(staging / "poster.jpg")
    manifest = {
        "schema_version": 2, "run_id": run_id, "topic": brief["topic"],
        "created_at": brief["created_at"], "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete", "mode": mode, "preset": brief.get("preset"),
        "duration": brief["duration"], "fps": FPS, "resolution": brief["resolution"],
        "video": "video.mp4", "caption": "caption.txt", "poster": "poster.jpg",
        "scene": "scene.py", "brief": "brief.json", "audio_profile": AUDIO_PROFILE,
        "audio": audio_metadata,
        "ffprobe": probe,
    }
    write_json(staging / "manifest.json", manifest)
    return atomic_promote(staging, run_id)


def render_run(run_id: str, keep_work: bool = False) -> Path:
    validate_run_id(run_id)
    run_work = work_path(run_id)
    brief = json.loads((run_work / "brief.json").read_text(encoding="utf-8"))
    brief["duration"] = validate_duration(brief["duration"])
    frame_count = max(1, round(brief["duration"] * FPS))
    frames, audio = run_work / "frames", run_work / "audio.wav"
    staging, video = run_work / "publish", run_work / "video.mp4"
    try:
        module = _load_scene(run_work / "scene.py")
        audio_plan = validate_audio_plan(module.SCENE.get("audio"))
        brief["schema_version"] = 2
        brief["audio"] = _audio_metadata(brief["topic"], audio_plan.canonical())
        write_json(run_work / "brief.json", brief)
        frames.mkdir(exist_ok=False)
        tasks = [(str(run_work / "scene.py"), frame, frame_count, str(frames / f"f_{frame:04d}.png")) for frame in range(frame_count)]
        workers = min(os.cpu_count() or 1, 8)
        with ProcessPoolExecutor(max_workers=workers) as pool:
            list(pool.map(_frame_task, tasks, chunksize=max(1, frame_count // (workers * 4))))
        audio_metadata = build_scene_soundtrack(audio, brief["topic"], brief["duration"], audio_plan)
        audio_metadata.pop("sample_positions")
        _compile(frames, audio, video, brief["duration"], brief["resolution"])
        probe = _verify(video, brief["duration"], brief["resolution"])
        poster_frame = frames / f"f_{min(frame_count - 1, int(frame_count * .75)):04d}.png"
        destination = _publish(run_id, brief, staging, run_work / "scene.py", video,
                               _caption(brief["topic"]), poster_frame, brief["mode"], probe,
                               audio_metadata)
        if not keep_work:
            shutil.rmtree(run_work, ignore_errors=True)
        return destination
    except Exception as exc:
        (run_work / "diagnostics").mkdir(exist_ok=True)
        write_json(run_work / "diagnostics" / "failure.json", {
            "error": str(exc), "traceback": traceback.format_exc(),
            "failed_at": datetime.now(timezone.utc).isoformat(),
        })
        if not keep_work:
            shutil.rmtree(frames, ignore_errors=True)
            audio.unlink(missing_ok=True)
            shutil.rmtree(staging, ignore_errors=True)
            video.unlink(missing_ok=True)
        raise


def render_legacy_preset(key: str, preset: dict, duration: float | None = None,
                         resolution: str = "720p", keep_work: bool = False) -> Path:
    selected_duration = validate_duration(duration if duration is not None else preset.get("duration"))
    audio_plan = validate_audio_plan(preset.get("audio_plan"))
    brief = create_run(preset["title"], selected_duration, resolution,
                       mode="legacy-preset", preset=key, audio_plan=audio_plan.canonical())
    run_id, run_work = brief["run_id"], work_path(brief["run_id"])
    frames, source_frames, audio = run_work / "frames", run_work / "legacy-source-frames", run_work / "audio.wav"
    video, staging = run_work / "video.mp4", run_work / "publish"
    try:
        source_frames.mkdir()
        env = os.environ.copy()
        env["TMP_FRAMES_DIR"] = str(source_frames)
        script = ROOT / preset["script"]
        subprocess.run([sys.executable, str(script), str(source_frames)], cwd=ROOT, env=env, check=True)
        _remap_legacy_frames(source_frames, frames, round(brief["duration"] * FPS))
        audio_metadata = build_scene_soundtrack(audio, brief["topic"], brief["duration"], audio_plan)
        audio_metadata.pop("sample_positions")
        _compile(frames, audio, video, brief["duration"], resolution)
        probe = _verify(video, brief["duration"], resolution)
        candidates = sorted(frames.glob("*.png"))
        poster = candidates[min(len(candidates) - 1, int(len(candidates) * .75))]
        destination = _publish(run_id, brief, staging, script, video, preset["caption"], poster,
                               "legacy-preset", probe, audio_metadata)
        if not keep_work:
            shutil.rmtree(run_work, ignore_errors=True)
        return destination
    except Exception as exc:
        (run_work / "diagnostics").mkdir(exist_ok=True)
        write_json(run_work / "diagnostics" / "failure.json", {"error": str(exc), "traceback": traceback.format_exc()})
        if not keep_work:
            shutil.rmtree(frames, ignore_errors=True)
            shutil.rmtree(source_frames, ignore_errors=True)
            audio.unlink(missing_ok=True)
            shutil.rmtree(staging, ignore_errors=True)
            video.unlink(missing_ok=True)
        raise


def _remap_legacy_frames(source: Path, destination: Path, frame_count: int) -> None:
    """Uniformly time-remap a fixed legacy animation to an exact target frame count."""
    candidates = sorted(source.glob("*.png"))
    if not candidates:
        raise ValueError("legacy preset generated no PNG frames")
    destination.mkdir(exist_ok=False)
    denominator = max(1, frame_count - 1)
    for frame in range(frame_count):
        source_index = round(frame * (len(candidates) - 1) / denominator)
        target = destination / f"f_{frame:04d}.png"
        try:
            os.link(candidates[source_index], target)
        except OSError:
            shutil.copy2(candidates[source_index], target)
