"""Stable command-line interface for the portable reel harness."""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import subprocess
import sys

from .catalog import build_catalog
from .config import load_brand
from .rendering import create_run, inspect_video, probe_run, render_run
from .runs import (OUTPUT_DIR, ROOT, WORK_DIR, clean_work, delete_run, list_runs,
                   migrate_legacy, read_json, validate_run_id, work_path,
                   DEFAULT_DURATION)


def _presets() -> dict:
    from generate import PRESETS
    return PRESETS


def doctor() -> tuple[bool, list[dict]]:
    checks = []
    def add(name, ok, detail): checks.append({"check": name, "ok": bool(ok), "detail": str(detail)})
    add("python", sys.version_info >= (3, 9), platform.python_version())
    for module in ("PIL", "numpy"):
        found = importlib.util.find_spec(module) is not None
        add(module, found, "installed" if found else "missing")
    for binary in ("ffmpeg", "ffprobe"):
        found = shutil.which(binary); add(binary, bool(found), found or "not on PATH")
    try:
        brand = load_brand(); add("brand config", True, f"{brand.handle} / {brand.accent}")
    except Exception as exc: add("brand config", False, exc)
    fonts = [ROOT / "fonts" / name for name in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf")]
    add("fonts", all(path.is_file() for path in fonts), f"{sum(path.is_file() for path in fonts)}/4 required fonts")
    for directory in (OUTPUT_DIR, WORK_DIR):
        try:
            directory.mkdir(parents=True, exist_ok=True)
            probe = directory / ".write-probe"; probe.write_text("ok", encoding="utf-8"); probe.unlink()
            ignored = subprocess.run(["git", "check-ignore", "-q", str(directory / "probe")], cwd=ROOT).returncode == 0
            add(f"{directory.name} writable + ignored", ignored, directory)
        except OSError as exc: add(f"{directory.name} writable + ignored", False, exc)
    return all(check["ok"] for check in checks), checks


def _find_run(run_id: str):
    validate_run_id(run_id)
    for base in (OUTPUT_DIR, WORK_DIR):
        path = base / run_id
        source = path / ("manifest.json" if base == OUTPUT_DIR else "brief.json")
        if source.exists(): return path, read_json(source)
    raise FileNotFoundError(f"run not found: {run_id}")


def _promote_scene(run_id: str, yes: bool):
    source_dir, metadata = _find_run(run_id)
    if source_dir.parent != OUTPUT_DIR: raise ValueError("only a successfully rendered output run can be promoted")
    if not yes:
        answer = input(f"Promote {run_id} into tracked reusable source? Type the full run id: ").strip()
        if answer != run_id: raise RuntimeError("promotion cancelled")
    scene = source_dir / "scene.py"
    spec = importlib.util.spec_from_file_location("promote_candidate", scene)
    if spec is None or spec.loader is None: raise ValueError("invalid scene module")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if not callable(getattr(module, "draw_stage", None)): raise ValueError("scene does not implement SceneV2")
    test_command = ([sys.executable, "-m", "pytest", "-q"] if importlib.util.find_spec("pytest")
                    else [sys.executable, "-m", "unittest", "discover", "-s", "tests"])
    subprocess.run(test_command, cwd=ROOT, check=True)
    promoted = ROOT / "reel" / "promoted"; promoted.mkdir(exist_ok=True)
    (promoted / "__init__.py").touch(exist_ok=True)
    from .runs import slugify
    slug = slugify(metadata.get("preset") or metadata["topic"]).replace("-", "_")
    target = promoted / f"{slug}.py"
    if target.exists(): raise FileExistsError(f"promoted scene already exists: {target.name}")
    shutil.copy2(scene, target)
    registry = promoted / "registry.json"
    data = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {}
    data[slug] = {"title": metadata["topic"], "scene": f"reel/promoted/{target.name}", "source_run": run_id}
    registry.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    subprocess.run(test_command, cwd=ROOT, check=True)
    return target


def build_parser():
    parser = argparse.ArgumentParser(prog="reel", description="Portable Blueprint Reel harness")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor"); commands.add_parser("presets")
    scaffold = commands.add_parser("scaffold"); scaffold.add_argument("topic"); scaffold.add_argument("--duration", type=float, default=DEFAULT_DURATION); scaffold.add_argument("--resolution", choices=("720p", "1080p", "2160p"), default="720p"); scaffold.add_argument("--json", action="store_true")
    probe = commands.add_parser("probe"); probe.add_argument("run_id")
    render = commands.add_parser("render"); render.add_argument("run_id"); render.add_argument("--keep-work", action="store_true")
    runs = commands.add_parser("runs"); runs.add_argument("--json", action="store_true")
    inspect = commands.add_parser("inspect"); inspect.add_argument("run_id"); inspect.add_argument("--json", action="store_true")
    delete = commands.add_parser("delete"); delete.add_argument("run_id"); delete.add_argument("--yes", action="store_true")
    commands.add_parser("clean"); commands.add_parser("migrate-legacy")
    promote = commands.add_parser("promote"); promote.add_argument("run_id"); promote.add_argument("--yes", action="store_true")
    serve = commands.add_parser("serve"); serve.add_argument("--port", type=int, default=8000)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            ok, checks = doctor()
            for check in checks: print(f"{'OK' if check['ok'] else 'FAIL':4} {check['check']}: {check['detail']}")
            raise SystemExit(0 if ok else 1)
        if args.command == "presets":
            for key, value in _presets().items(): print(f"{key:26} {value['title']}")
        elif args.command == "scaffold":
            brief = create_run(args.topic, args.duration, args.resolution)
            print(json.dumps(brief, indent=2) if args.json else f"Scaffolded {brief['run_id']} at {work_path(brief['run_id'])}")
        elif args.command == "probe":
            for path in probe_run(args.run_id): print(path)
        elif args.command == "render":
            path = render_run(args.run_id, args.keep_work); build_catalog(); print(path)
        elif args.command == "runs":
            runs = list_runs()
            if args.json: print(json.dumps(runs, indent=2))
            else:
                for run in runs: print(f"{run['run_id']}  {run['duration']:g}s  {run['resolution']}  {run['topic']}")
        elif args.command == "inspect":
            path, data = _find_run(args.run_id)
            if (path / "video.mp4").exists(): data = {**data, "live_ffprobe": inspect_video(path / "video.mp4")}
            print(json.dumps(data, indent=2))
        elif args.command == "delete":
            if not args.yes:
                answer = input(f"Delete run {args.run_id}? Type the full run id: ").strip()
                if answer != args.run_id: raise RuntimeError("deletion cancelled")
            deleted = delete_run(args.run_id); build_catalog(); print(f"Deleted {deleted}")
        elif args.command == "clean":
            count = clean_work(); print(f"Removed {count} work director{'y' if count == 1 else 'ies'}")
        elif args.command == "migrate-legacy":
            migrated = migrate_legacy(); build_catalog(); print(f"Migrated {len(migrated)} legacy videos")
            for run_id in migrated: print(run_id)
        elif args.command == "promote": print(_promote_scene(args.run_id, args.yes))
        elif args.command == "serve":
            build_catalog()
            from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
            class Handler(SimpleHTTPRequestHandler):
                def __init__(self, *a, **kw): super().__init__(*a, directory=str(ROOT), **kw)
            print(f"Read-only gallery: http://localhost:{args.port}/gallery.html")
            ThreadingHTTPServer(("", args.port), Handler).serve_forever()
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr); raise SystemExit(2)
