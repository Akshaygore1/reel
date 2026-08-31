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
import wave
from unittest import mock

import numpy as np

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

            with wave.open(str(paths[0]), "rb") as rendered:
                self.assertEqual(rendered.getframerate(), 48_000)
                self.assertEqual(rendered.getnchannels(), 1)
                self.assertEqual(rendered.getsampwidth(), 2)

    def test_all_public_cues_are_audible_and_match_generator_gestures(self):
        from reel.audio import (CUE_GESTURES, PROFILES, SAMPLE_RATE, _add,
                                _cue_signal, _generator_signal)
        profile, seed, intensity = PROFILES["network"], 123456, 0.0
        expected_gestures = {
            "blip": ((0., "accent"),), "packet": ((0., "tick"),),
            "tick": ((0., "tick"),),
            "queue": ((0., "tick"), (.1, "tick"), (.2, "tick"), (.3, "tick")),
            "alarm": ((0., "thud"), (.18, "whoosh")),
            "latch": ((0., "tick"), (.04, "thud")),
            "sweep": ((0., "riser"),),
            "processing": tuple((i * .1, "tick") for i in range(7)),
            "impact": ((0., "thud"),), "success": ((0., "stinger"),),
        }
        self.assertEqual(CUE_GESTURES, expected_gestures)
        for kind, gesture in expected_gestures.items():
            with self.subTest(kind=kind):
                actual = _cue_signal(kind, intensity, profile, seed)
                expected = np.zeros(len(actual))
                for index, (offset, generator) in enumerate(gesture):
                    component_seed = (seed + index * 0x9e3779b9) & 0xffffffff
                    _add(expected, round(offset * SAMPLE_RATE),
                         _generator_signal(generator, .25, component_seed))
                self.assertTrue(np.any(actual))
                np.testing.assert_array_equal(actual, expected)

    def test_generator_attacks_clipping_and_payoff_strength(self):
        from reel.audio import (ATTACK_SECONDS, GENERATOR_LEVELS,
                                SOFT_CLIP_CEILING, _generator_signal, soft_clip)
        frame, rms_window, onset_threshold = 1 / 30, round(.02 * 48_000), .04
        for kind, attack in ATTACK_SECONDS.items():
            with self.subTest(kind=kind):
                signal = _generator_signal(kind, 1., 42)
                bins = [np.sqrt(np.mean(signal[start:start+rms_window] ** 2))
                        for start in range(0, len(signal), rms_window)]
                measured = next(index * .02 for index, rms in enumerate(bins)
                                if rms >= onset_threshold)
                self.assertLessEqual(abs(measured - attack), frame)
        clipped = soft_clip(np.array([-100., -1., 0., 1., 100.]))
        self.assertLessEqual(float(np.max(np.abs(clipped))), SOFT_CLIP_CEILING)
        peaks = {kind: float(np.max(np.abs(_generator_signal(kind, 1., 42))))
                 for kind in GENERATOR_LEVELS}
        self.assertEqual(max(peaks, key=peaks.get), "stinger")

    def test_rendered_pcm_obeys_soft_clip_ceiling(self):
        from reel.audio import SOFT_CLIP_CEILING, build_scene_soundtrack
        crowded = {"profile": "network", "events": [
            {"at": .1, "kind": "success", "intensity": 1.},
            {"at": .1, "kind": "success", "intensity": 1.},
            {"at": .4, "kind": "alarm", "intensity": 1.},
            {"at": .7, "kind": "success", "intensity": 1.},
        ]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ceiling.wav"
            build_scene_soundtrack(path, "Ceiling", 1., crowded)
            with wave.open(str(path), "rb") as rendered:
                pcm = np.frombuffer(rendered.readframes(rendered.getnframes()), dtype="<i2")
            self.assertLessEqual(int(np.max(np.abs(pcm.astype(np.int32)))),
                                 round(SOFT_CLIP_CEILING * 32767))

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

    def test_scenev2_captions_follow_exact_beat_boundaries(self):
        from reel.rendering import caption_for_progress
        captions = ["normal", "crisis", "resolution"]
        self.assertEqual(caption_for_progress(captions, 0), "normal")
        self.assertEqual(caption_for_progress(captions, .29999), "normal")
        self.assertEqual(caption_for_progress(captions, .3), "crisis")
        self.assertEqual(caption_for_progress(captions, .59999), "crisis")
        self.assertEqual(caption_for_progress(captions, .6), "resolution")
        self.assertEqual(caption_for_progress(captions, 1), "resolution")

    def test_scenev2_rejects_missing_empty_or_wrong_sized_caption_lists(self):
        from reel.rendering import validate_scene_captions
        invalid = [None, [], ["one"], ["one", "two"],
                   ["one", "two", "three", "four"],
                   ["one", "", "three"], ["one", "   ", "three"]]
        for captions in invalid:
            with self.subTest(captions=captions), self.assertRaises(ValueError):
                validate_scene_captions(captions)
        self.assertEqual(validate_scene_captions([" one ", "two", "three "]),
                         ("one", "two", "three"))

    def test_scenev2_and_legacy_caption_pills_render_inside_lower_band(self):
        from PIL import Image, ImageChops, ImageDraw
        from engine import blueprint_engine as bp
        from reel.rendering import _default_scene, _draw_chrome
        image = Image.new("RGB", (bp.W, bp.H), bp.BG)
        _draw_chrome(image, _default_scene("Cache"), 180, 600)
        caption_band = ImageChops.difference(
            image.crop((0, 970, bp.W, 1040)),
            Image.new("RGB", (bp.W, 70), bp.BG),
        )
        self.assertIsNotNone(caption_band.getbbox())

        legacy = Image.new("RGB", (bp.W, bp.H), bp.BG)
        layout = bp.draw_caption_pill(
            ImageDraw.Draw(legacy), 30,
            [(0, "first"), (20, "A long database joins caption that must fit safely inside the glass pill even when the explanation includes build-side selection, memory pressure, probe behavior, matching keys, output rows, and the O(N+M) cost of an equi-join")], 1,
        )
        changed = ImageChops.difference(legacy, Image.new("RGB", legacy.size, bp.BG)).getbbox()
        self.assertIsNotNone(changed)
        self.assertGreaterEqual(changed[1], 970)
        self.assertLessEqual(changed[3], 1040)
        self.assertIn("O(N+M) cost", layout["caption"])
        self.assertNotIn("…", " ".join(layout["lines"]))
        self.assertLessEqual(len(layout["lines"]), 2)
        self.assertTrue(all(width <= layout["max_text_width"] for width in layout["line_widths"]))

    def test_blank_and_explicit_headline_connectors_render_without_hidden_spacing(self):
        from PIL import Image, ImageDraw
        from engine import blueprint_engine as bp

        def headline(connector):
            image = Image.new("RGB", (bp.W, bp.H), bp.BG)
            bp.draw_header_bar(ImageDraw.Draw(image), 1, title1="DATABASE",
                               title_vs=connector, title2="JOINS")
            return image.crop((0, 212, bp.W, 252))

        blank, comparison = headline(""), headline("vs")
        blank_pixels = blank.load()
        comparison_pixels = comparison.load()
        blank_dim = sum(blank_pixels[x, y] == bp.DIM for x in range(bp.W) for y in range(blank.height))
        comparison_dim = sum(comparison_pixels[x, y] == bp.DIM for x in range(bp.W) for y in range(comparison.height))
        self.assertEqual(blank_dim, 0)
        self.assertGreater(comparison_dim, 0)

        def color_bounds(image, color):
            points = [(x, y) for y in range(image.height) for x in range(image.width)
                      if image.getpixel((x, y)) == color]
            return min(x for x, _ in points), max(x for x, _ in points)

        blank_white, blank_teal = color_bounds(blank, bp.WHITE), color_bounds(blank, bp.TEAL)
        comparison_white, comparison_teal = color_bounds(comparison, bp.WHITE), color_bounds(comparison, bp.TEAL)
        self.assertLess(blank_teal[0] - blank_white[1], comparison_teal[0] - comparison_white[1])

    def test_scaffold_has_clean_title_caption_contract_and_posting_copy(self):
        from reel.rendering import _caption, create_run
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / ".work"
            with mock.patch("reel.runs.WORK_DIR", work):
                brief = create_run("Database Joins Explained", duration=20)
                run = work / brief["run_id"]
                module_source = (run / "scene.py").read_text(encoding="utf-8")
                self.assertIn("'title_left': 'DATABASE'", module_source)
                self.assertIn("'title_right': 'JOINS'", module_source)
                self.assertIn("'title_connector': ''", module_source)
                self.assertNotIn("'title_right': 'BLUEPRINT'", module_source)
                self.assertTrue(brief["constraints"]["burned_in_captions"])
        self.assertTrue(_caption("Database Joins").startswith("Database Joins explained "))
        self.assertTrue(_caption("Database Joins Explained").startswith("Database Joins Explained as "))
        self.assertNotIn("Explained explained", _caption("Database Joins Explained"))

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
                self.assertEqual(float(probe["format"]["duration"]), duration)


if __name__ == "__main__": unittest.main()
