import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reel.catalog import javascript_json
from reel.config import BrandConfig
from reel.models import STAGE_BOUNDS, frame_context
from reel.runs import (atomic_promote, clean_work, new_run_id, resolution_size,
                       safe_child, slugify, validate_duration, validate_manifest,
                       DEFAULT_DURATION, MAX_DURATION, MIN_DURATION)


class RunIdentityTests(unittest.TestCase):
    def test_run_id_is_stable_shape_but_unique_by_token(self):
        now = datetime(2026, 8, 24, 12, 0, 1, tzinfo=timezone.utc)
        first = new_run_id("B-Tree vs LSM Tree", now, "a1b2c3")
        second = new_run_id("B-Tree vs LSM Tree", now, "d4e5f6")
        self.assertEqual(first, "20260824T120001Z-b-tree-vs-lsm-tree-a1b2c3")
        self.assertNotEqual(first, second)

    def test_slug_and_path_safety(self):
        self.assertEqual(slugify("../../Hello, World!"), "hello-world")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): safe_child(Path(tmp), "../escape")

    def test_duration_and_resolution_contract(self):
        self.assertEqual(validate_duration(None), 20.0)
        self.assertEqual((MIN_DURATION, DEFAULT_DURATION, MAX_DURATION), (15.0, 20.0, 30.0))
        self.assertEqual(validate_duration(15), 15.0)
        self.assertEqual(validate_duration(30), 30.0)
        self.assertEqual(resolution_size("2160p"), (2160, 3840))
        for value in (0, -1, 10, 14.99, 30.1, 31):
            with self.assertRaises(ValueError): validate_duration(value)
        with self.assertRaises(ValueError): resolution_size("4k")

    def test_frame_context_has_locked_stage_and_beats(self):
        self.assertEqual(frame_context(5, 100).stage_bounds, STAGE_BOUNDS)
        self.assertEqual(frame_context(5, 100).beat, 1)
        self.assertEqual(frame_context(45, 100).beat, 2)
        self.assertEqual(frame_context(75, 100).beat, 3)


class ValidationTests(unittest.TestCase):
    def manifest(self, run_id):
        return {"schema_version": 1, "run_id": run_id, "topic": "Cache", "created_at": "now",
                "status": "complete", "mode": "bespoke", "duration": 10.0, "fps": 30,
                "resolution": "720p", "video": "video.mp4", "caption": "caption.txt",
                "poster": "poster.jpg", "scene": "scene.py", "brief": "brief.json",
                "audio_profile": "zero voiceover"}

    def manifest_v2(self, run_id):
        manifest = self.manifest(run_id)
        manifest.update({"schema_version": 2, "duration": 20.0,
                         "audio": {"profile": "network", "seed": 42,
                                   "cue_count": 3, "voiceover": False}})
        return manifest

    def test_manifest_schema(self):
        run_id = "20260824T120001Z-cache-a1b2c3"
        self.assertEqual(validate_manifest(self.manifest(run_id))["run_id"], run_id)
        broken = self.manifest(run_id); del broken["video"]
        with self.assertRaises(ValueError): validate_manifest(broken)
        self.assertEqual(validate_manifest(self.manifest_v2(run_id))["audio"]["seed"], 42)
        broken_v2 = self.manifest_v2(run_id); del broken_v2["audio"]
        with self.assertRaises(ValueError): validate_manifest(broken_v2)

    def test_brand_config_validates_configurable_accent(self):
        BrandConfig().validate()
        BrandConfig(accent="#ffffff").validate()
        with self.assertRaises(ValueError): BrandConfig(accent="red").validate()

    def test_catalog_json_escapes_script_terminators(self):
        encoded = javascript_json([{"caption": "</script>\u2028safe"}])
        self.assertNotIn("</script>", encoded)
        self.assertIn("<\\/script>", encoded)
        self.assertIn("\\u2028", encoded)

    def test_atomic_promotion_never_overwrites(self):
        run_id = "20260824T120001Z-cache-a1b2c3"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); output = root / "output"; staging = root / "staging"; staging.mkdir()
            (staging / "manifest.json").write_text(json.dumps(self.manifest(run_id)))
            for name in ("video.mp4", "caption.txt", "poster.jpg", "scene.py", "brief.json"): (staging / name).touch()
            with mock.patch("reel.runs.OUTPUT_DIR", output):
                destination = atomic_promote(staging, run_id)
                self.assertTrue(destination.is_dir())
                other = root / "other"; other.mkdir(); (other / "manifest.json").write_text(json.dumps(self.manifest(run_id)))
                for name in ("video.mp4", "caption.txt", "poster.jpg", "scene.py", "brief.json"): (other / name).touch()
                with self.assertRaises(FileExistsError): atomic_promote(other, run_id)

    def test_cleanup_removes_only_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / ".work"; (work / "one").mkdir(parents=True); (work / "two").mkdir()
            with mock.patch("reel.runs.WORK_DIR", work): self.assertEqual(clean_work(), 2)
            self.assertFalse(work.exists())

    def test_failed_render_keeps_lightweight_diagnostics(self):
        from reel.rendering import create_run, render_run
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / ".work"; output = Path(tmp) / "output"
            with mock.patch("reel.runs.WORK_DIR", work), mock.patch("reel.runs.OUTPUT_DIR", output):
                brief = create_run("Broken Scene", duration=15)
                run = work / brief["run_id"]
                (run / "scene.py").write_text("this is invalid python !!!", encoding="utf-8")
                with self.assertRaises(Exception): render_run(brief["run_id"])
                self.assertTrue((run / "diagnostics" / "failure.json").is_file())
                self.assertFalse((run / "frames").exists())

    def test_legacy_migration_moves_flat_pair_without_reencoding(self):
        from reel.runs import migrate_legacy
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "output"; output.mkdir()
            (output / "video_cache.mp4").write_bytes(b"legacy bytes")
            (output / "video_cache.txt").write_text("legacy caption", encoding="utf-8")
            with mock.patch("reel.runs.OUTPUT_DIR", output): migrated = migrate_legacy()
            self.assertEqual(len(migrated), 1)
            run = output / migrated[0]
            self.assertEqual((run / "video.mp4").read_bytes(), b"legacy bytes")
            self.assertEqual((run / "caption.txt").read_text(), "legacy caption")
            validate_manifest(json.loads((run / "manifest.json").read_text()))

    def test_tracked_gallery_is_catalog_driven_and_has_no_delete_action(self):
        gallery = (ROOT / "gallery.html").read_text(encoding="utf-8")
        self.assertIn('src="output/catalog.js"', gallery)
        for control in ("Search topic", "Newest first", "Copy caption", "Manifest", "Download"):
            self.assertIn(control, gallery)
        self.assertNotIn("deleteVideo", gallery)


class CompatibilityTests(unittest.TestCase):
    EXPECTED = {"ci_cd", "mcp_explained", "sql_injection", "database_failover",
                "kafka_partitions", "redis_pubsub_vs_kafka", "redis_vs_db", "autoscaling",
                "cron_jobs", "vpn_tunnel", "cold_starts", "database_indexing",
                "streaming_vs_direct", "websockets_vs_polling", "sql_vs_nosql",
                "chatgpt_streaming", "cdn_edge", "authn_vs_authz", "react_under_hood",
                "captcha_explained", "garbage_collection", "garbage_collection_simple"}

    def test_all_legacy_presets_have_existing_scripts(self):
        import generate
        self.assertEqual(set(generate.PRESETS), self.EXPECTED)
        from reel.audio import validate_audio_plan
        for preset in generate.PRESETS.values():
            self.assertTrue((ROOT / preset["script"]).is_file())
            validate_audio_plan(preset["audio_plan"])

    def test_legacy_hd_uhd_and_duration_forwarding(self):
        import generate
        with mock.patch.object(generate, "generate_from_prompt") as call, \
             mock.patch.object(sys, "argv", ["generate.py", "--prompt", "new topic", "--hd", "--uhd", "--duration", "25"]):
            generate.main()
        call.assert_called_once_with("new topic", hd=True, uhd=True, duration=25.0)

    def test_quick_and_preset_duration_validation_does_not_clamp(self):
        import generate
        for value in (10, 31):
            with self.assertRaises(ValueError): generate.normalize_duration(value)

    def test_delete_requires_typing_full_run_id(self):
        from reel import cli
        run_id = "20260824T120001Z-cache-a1b2c3"
        with mock.patch("builtins.input", return_value="no"), mock.patch.object(cli, "delete_run") as delete:
            with self.assertRaises(SystemExit) as exit_context: cli.main(["delete", run_id])
        self.assertEqual(exit_context.exception.code, 2)
        delete.assert_not_called()


class AudioContractTests(unittest.TestCase):
    PLAN = {"profile": "network", "tempo_bpm": 100, "events": [
        {"at": .12, "kind": "packet", "intensity": .6},
        {"at": .34, "kind": "alarm", "intensity": .8},
        {"at": .64, "kind": "success", "intensity": .7},
    ]}

    def test_audio_plan_defaults_and_validation(self):
        from reel.audio import validate_audio_plan
        plan = validate_audio_plan({"profile": "mechanical", "events": [
            {"at": .1, "kind": "tick"}, {"at": .4, "kind": "latch"},
            {"at": .7, "kind": "impact"},
        ]})
        self.assertEqual(plan.tempo_bpm, 92)
        self.assertEqual(plan.events[0]["intensity"], .5)
        invalid = [
            None,
            {"profile": "unknown", "events": []},
            {"profile": "network", "tempo_bpm": 10, "events": []},
            {"profile": "network", "events": [{"at": .1, "kind": "packet"}]},
            {"profile": "network", "events": [
                {"at": .1, "kind": "packet"}, {"at": .4, "kind": "wat"}, {"at": .7, "kind": "success"}]},
            {"profile": "network", "events": [
                {"at": .1, "kind": "packet", "intensity": 2},
                {"at": .4, "kind": "alarm"}, {"at": .7, "kind": "success"}]},
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError): validate_audio_plan(value)

    def test_soundtrack_is_stable_topic_and_plan_specific_and_sample_accurate(self):
        from reel.audio import SAMPLE_RATE, build_scene_soundtrack
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / name for name in ("a.wav", "b.wav", "topic.wav", "plan.wav")]
            first = build_scene_soundtrack(paths[0], "Load Balancer", 1.0, self.PLAN)
            build_scene_soundtrack(paths[1], "Load Balancer", 1.0, self.PLAN)
            build_scene_soundtrack(paths[2], "Database", 1.0, self.PLAN)
            changed = {**self.PLAN, "events": [*self.PLAN["events"][:-1],
                       {"at": .72, "kind": "success", "intensity": .7}]}
            build_scene_soundtrack(paths[3], "Load Balancer", 1.0, changed)
            hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
            self.assertEqual(hashes[0], hashes[1])
            self.assertNotEqual(hashes[0], hashes[2])
            self.assertNotEqual(hashes[0], hashes[3])
            self.assertEqual(first["sample_positions"], [round(at * SAMPLE_RATE) for at in (.12, .34, .64)])

    def test_invalid_plan_fails_before_frame_generation(self):
        from reel.rendering import create_run, render_run
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / ".work"; output = Path(tmp) / "output"
            with mock.patch("reel.runs.WORK_DIR", work), mock.patch("reel.runs.OUTPUT_DIR", output):
                brief = create_run("No Audio", duration=15)
                scene = work / brief["run_id"] / "scene.py"
                scene.write_text(scene.read_text().replace("'audio':", "'invalid_audio':"), encoding="utf-8")
                with self.assertRaises(ValueError): render_run(brief["run_id"])
                self.assertFalse((work / brief["run_id"] / "frames").exists())

    def test_scenev2_chrome_and_legacy_primitive_do_not_draw_caption_pills(self):
        from PIL import Image, ImageDraw
        from engine import blueprint_engine as bp
        from reel.rendering import _default_scene, _draw_chrome
        image = Image.new("RGB", (bp.W, bp.H), bp.BG)
        with mock.patch.object(bp, "draw_caption_pill") as caption:
            _draw_chrome(image, _default_scene("Cache", "@buildebugship", "#fb7185"), 200, 600)
            caption.assert_not_called()
        legacy = Image.new("RGB", (bp.W, bp.H), bp.BG)
        before = legacy.tobytes()
        bp.draw_caption_pill(ImageDraw.Draw(legacy), 1, [(0, "caption")], 1)
        self.assertEqual(legacy.tobytes(), before)

    def test_legacy_frames_are_remapped_to_exact_target_count(self):
        from PIL import Image
        from reel.rendering import _remap_legacy_frames
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "source", Path(tmp) / "target"; source.mkdir()
            for frame, color in enumerate(((10, 0, 0), (20, 0, 0), (30, 0, 0))):
                Image.new("RGB", (2, 2), color).save(source / f"f_{frame:04d}.png")
            _remap_legacy_frames(source, target, 15 * 30)
            frames = sorted(target.glob("*.png"))
            self.assertEqual(len(frames), 450)
            self.assertEqual(Image.open(frames[0]).getpixel((0, 0)), (10, 0, 0))
            self.assertEqual(Image.open(frames[-1]).getpixel((0, 0)), (30, 0, 0))

class GitHygieneTests(unittest.TestCase):
    def test_generated_artifacts_are_not_tracked(self):
        tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
        bad = [path for path in tracked if (
            path.endswith((".mp4", ".wav", ".aac", ".m4a", ".mov", ".webm")) or path.startswith(("audio/", ".work/", ".tmp", ".playwright-mcp/"))
            or (path.startswith("output/") and path != "output/.gitkeep") or path.endswith("catalog.js")
        )]
        self.assertEqual(bad, [])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class FFmpegIntegrationTests(unittest.TestCase):
    def test_minimum_and_maximum_duration_compile_have_exact_specs(self):
        from PIL import Image
        from engine.blueprint_engine import BG
        from reel.audio import build_scene_soundtrack
        from reel.rendering import _compile, _verify
        plan = {"profile": "network", "events": [
            {"at": .12, "kind": "packet"}, {"at": .35, "kind": "alarm"},
            {"at": .65, "kind": "success"},
        ]}
        for duration in (15, 30):
            with self.subTest(duration=duration), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); frames = root / "frames"; frames.mkdir()
                source = root / "frame.png"; Image.new("RGB", (720, 1280), BG).save(source)
                for frame in range(duration * 30): os.link(source, frames / f"f_{frame:04d}.png")
                audio, video = root / "audio.wav", root / "video.mp4"
                build_scene_soundtrack(audio, "Duration Boundary", duration, plan)
                _compile(frames, audio, video, duration, "720p")
                probe = _verify(video, duration, "720p")
                streams = {stream["codec_type"]: stream for stream in probe["streams"]}
                self.assertEqual(streams["video"]["codec_name"], "h264")
                self.assertEqual(streams["video"]["r_frame_rate"], "30/1")
                self.assertEqual(streams["audio"]["codec_name"], "aac")
                self.assertAlmostEqual(float(probe["format"]["duration"]), duration, places=2)


if __name__ == "__main__": unittest.main()
