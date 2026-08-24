"""Deterministic, scene-synchronised procedural audio for blueprint reels."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import wave

import numpy as np

SAMPLE_RATE = 44_100
PROFILES = {
    "network": {"tempo_bpm": 108, "root": 146.83, "color": (1.0, 1.25, 1.50)},
    "mechanical": {"tempo_bpm": 92, "root": 110.00, "color": (1.0, 1.50, 2.00)},
    "storage": {"tempo_bpm": 84, "root": 98.00, "color": (1.0, 1.20, 1.50)},
    "security": {"tempo_bpm": 96, "root": 123.47, "color": (1.0, 1.19, 1.50)},
    "compute": {"tempo_bpm": 116, "root": 164.81, "color": (1.0, 1.25, 1.498)},
    "protocol": {"tempo_bpm": 100, "root": 130.81, "color": (1.0, 1.26, 1.50)},
}
CUE_KINDS = frozenset({
    "blip", "packet", "tick", "queue", "alarm", "latch", "sweep",
    "processing", "impact", "success",
})


@dataclass(frozen=True)
class AudioPlan:
    profile: str
    tempo_bpm: float
    events: tuple[dict, ...]

    def canonical(self) -> dict:
        return {
            "profile": self.profile,
            "tempo_bpm": self.tempo_bpm,
            "events": [dict(event) for event in self.events],
        }


def _beat_for(at: float) -> int:
    return 1 if at < .3 else (2 if at < .6 else 3)


def validate_audio_plan(value: object) -> AudioPlan:
    """Validate and normalize a mandatory SceneV2 cue sheet."""
    if not isinstance(value, dict):
        raise ValueError("SCENE['audio'] must be a cue-sheet object")
    profile = value.get("profile")
    if profile not in PROFILES:
        raise ValueError(f"audio profile must be one of: {', '.join(PROFILES)}")
    tempo = value.get("tempo_bpm", PROFILES[profile]["tempo_bpm"])
    if isinstance(tempo, bool) or not isinstance(tempo, (int, float)) or not math.isfinite(float(tempo)):
        raise ValueError("audio tempo_bpm must be a finite number")
    tempo = float(tempo)
    if not 40 <= tempo <= 240:
        raise ValueError("audio tempo_bpm must be between 40 and 240")
    raw_events = value.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        raise ValueError("audio events must be a non-empty list")
    events = []
    for index, event in enumerate(raw_events):
        if not isinstance(event, dict):
            raise ValueError(f"audio event {index} must be an object")
        at, kind, intensity = event.get("at"), event.get("kind"), event.get("intensity", .5)
        if isinstance(at, bool) or not isinstance(at, (int, float)) or not math.isfinite(float(at)) or not 0 <= float(at) < 1:
            raise ValueError(f"audio event {index} at must be normalized in [0, 1)")
        if kind not in CUE_KINDS:
            raise ValueError(f"audio event {index} kind must be one of: {', '.join(sorted(CUE_KINDS))}")
        if isinstance(intensity, bool) or not isinstance(intensity, (int, float)) or not math.isfinite(float(intensity)) or not 0 <= float(intensity) <= 1:
            raise ValueError(f"audio event {index} intensity must be between 0 and 1")
        events.append({"at": float(at), "kind": kind, "intensity": float(intensity)})
    events.sort(key=lambda event: (event["at"], event["kind"], event["intensity"]))
    beats = {_beat_for(event["at"]) for event in events}
    if beats != {1, 2, 3}:
        missing = ", ".join(str(beat) for beat in sorted({1, 2, 3} - beats))
        raise ValueError(f"audio cue sheet must contain at least one event in each narrative beat; missing beat(s): {missing}")
    return AudioPlan(profile, tempo, tuple(events))


def stable_audio_seed(topic: str, plan: AudioPlan | dict) -> int:
    normalized = plan if isinstance(plan, AudioPlan) else validate_audio_plan(plan)
    payload = {"topic": topic, "audio": normalized.canonical()}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _add(samples: np.ndarray, start: int, signal: np.ndarray) -> None:
    if start >= len(samples) or not len(signal):
        return
    source_start = max(0, -start)
    destination_start = max(0, start)
    count = min(len(signal) - source_start, len(samples) - destination_start)
    if count > 0:
        samples[destination_start:destination_start + count] += signal[source_start:source_start + count]


def _tone(duration: float, frequency: np.ndarray | float, amplitude: float, decay: float = 5.0) -> np.ndarray:
    count = max(1, round(duration * SAMPLE_RATE))
    t = np.arange(count, dtype=np.float64) / SAMPLE_RATE
    phase = 2 * np.pi * (frequency * t if np.isscalar(frequency) else np.cumsum(frequency) / SAMPLE_RATE)
    envelope = np.minimum(1.0, t / .008) * np.exp(-decay * t / max(duration, .001))
    return np.sin(phase) * envelope * amplitude


def _cue_signal(kind: str, intensity: float, profile: dict, rng: np.random.Generator) -> np.ndarray:
    root = profile["root"] * rng.uniform(.97, 1.03)
    amplitude = .07 + .21 * intensity
    if kind == "blip":
        return _tone(.09, root * rng.uniform(5.5, 7.5), amplitude, 8)
    if kind == "packet":
        count = round(.16 * SAMPLE_RATE); frequencies = np.linspace(root * 3.2, root * 5.0, count)
        return _tone(.16, frequencies, amplitude, 6)
    if kind == "tick":
        signal = rng.normal(0, 1, round(.035 * SAMPLE_RATE))
        return signal * np.exp(-np.arange(len(signal)) / (SAMPLE_RATE * .005)) * amplitude * .75
    if kind == "queue":
        signal = np.zeros(round(.55 * SAMPLE_RATE))
        for offset in (0, .13, .26, .39):
            _add(signal, round(offset * SAMPLE_RATE), _tone(.12, root * 1.5, amplitude * .65, 7))
        return signal
    if kind == "alarm":
        count = round(.8 * SAMPLE_RATE); frequencies = np.linspace(root * 2.8, root * .8, count)
        signal = _tone(.8, frequencies, amplitude * 1.2, 2.8)
        signal *= .55 + .45 * np.sin(2 * np.pi * 18 * np.arange(count) / SAMPLE_RATE)
        return signal
    if kind == "latch":
        signal = rng.normal(0, 1, round(.2 * SAMPLE_RATE))
        signal *= np.exp(-np.arange(len(signal)) / (SAMPLE_RATE * .012)) * amplitude * .6
        _add(signal, round(.045 * SAMPLE_RATE), _tone(.13, root * .8, amplitude, 7))
        return signal
    if kind == "sweep":
        count = round(.65 * SAMPLE_RATE); frequencies = np.geomspace(root, root * 10, count)
        signal = _tone(.65, frequencies, amplitude * .75, 2)
        signal += rng.normal(0, amplitude * .08, count) * np.sin(np.linspace(0, np.pi, count))
        return signal
    if kind == "processing":
        signal = np.zeros(round(.75 * SAMPLE_RATE))
        for offset in np.arange(0, .7, .1):
            _add(signal, round(offset * SAMPLE_RATE), _tone(.075, root * rng.uniform(4, 7), amplitude * .45, 8))
        return signal
    if kind == "impact":
        count = round(.7 * SAMPLE_RATE); frequencies = np.linspace(root, root * .32, count)
        return _tone(.7, frequencies, amplitude * 1.35, 4)
    if kind == "success":
        signal = np.zeros(round(1.15 * SAMPLE_RATE))
        for delay, ratio in ((0, 2), (.08, 2.5), (.16, 3)):
            _add(signal, round(delay * SAMPLE_RATE), _tone(.95, root * ratio, amplitude * .72, 3.4))
        return signal
    raise AssertionError(kind)


def _ambient(duration: float, plan: AudioPlan, rng: np.random.Generator) -> np.ndarray:
    count = round(duration * SAMPLE_RATE)
    samples = np.zeros(count, dtype=np.float64)
    profile = PROFILES[plan.profile]
    seconds_per_beat = 60 / plan.tempo_bpm
    bar_duration = seconds_per_beat * 4
    progression = (1.0, 1.12246, 1.25992, .94387)
    detune = rng.uniform(.992, 1.008)
    for bar, start_time in enumerate(np.arange(0, duration, bar_duration)):
        length = min(round(bar_duration * SAMPLE_RATE), count - round(start_time * SAMPLE_RATE))
        if length <= 0:
            continue
        t = np.arange(length, dtype=np.float64) / SAMPLE_RATE
        fade = np.sin(np.linspace(0, np.pi, length)) ** .6
        root = profile["root"] * progression[bar % len(progression)] * detune
        chord = sum(np.sin(2 * np.pi * root * ratio * t) for ratio in profile["color"])
        bass = np.sin(2 * np.pi * root * .25 * t)
        _add(samples, round(start_time * SAMPLE_RATE), (chord * .013 + bass * .027) * fade)
    tick_period = seconds_per_beat / 2
    tick_phase = rng.uniform(0, tick_period)
    for index, tick_time in enumerate(np.arange(tick_phase, duration, tick_period)):
        volume = .010 if index % 2 else .018
        tick = rng.normal(0, 1, round(.018 * SAMPLE_RATE))
        tick *= np.exp(-np.arange(len(tick)) / (SAMPLE_RATE * .003)) * volume
        _add(samples, round(tick_time * SAMPLE_RATE), tick)
    return samples


def build_scene_soundtrack(output_wav: str | Path, topic: str, duration: float, audio: AudioPlan | dict) -> dict:
    """Render a deterministic mono PCM cue sheet and return publication metadata."""
    plan = audio if isinstance(audio, AudioPlan) else validate_audio_plan(audio)
    seed = stable_audio_seed(topic, plan)
    rng = np.random.default_rng(seed)
    samples = _ambient(duration, plan, rng)
    sample_positions = []
    profile = PROFILES[plan.profile]
    for event in plan.events:
        sample = round(event["at"] * duration * SAMPLE_RATE)
        sample_positions.append(sample)
        _add(samples, sample, _cue_signal(event["kind"], event["intensity"], profile, rng))
    samples = np.tanh(samples * 1.35)
    peak = max(float(np.max(np.abs(samples))), .001)
    pcm = np.asarray(np.clip(samples * min(1.0, .94 / peak), -1, 1) * 32767, dtype="<i2")
    path = Path(output_wav)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm.tobytes())
    return {
        "profile": plan.profile, "tempo_bpm": plan.tempo_bpm, "seed": seed,
        "cue_count": len(plan.events), "sample_positions": sample_positions,
        "voiceover": False,
    }
