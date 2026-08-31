"""Deterministic, scene-synchronised procedural audio for blueprint reels."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import wave

import numpy as np

SAMPLE_RATE = 48_000
REFERENCE_ROOT = 146.83
SOFT_CLIP_CEILING = .89
PROFILES = {
    "network": {"tempo_bpm": 108, "root": 146.83, "color": (1., 1.25, 1.5)},
    "mechanical": {"tempo_bpm": 92, "root": 110., "color": (1., 1.5, 2.)},
    "storage": {"tempo_bpm": 84, "root": 98., "color": (1., 1.2, 1.5)},
    "security": {"tempo_bpm": 96, "root": 123.47, "color": (1., 1.19, 1.5)},
    "compute": {"tempo_bpm": 116, "root": 164.81, "color": (1., 1.25, 1.498)},
    "protocol": {"tempo_bpm": 100, "root": 130.81, "color": (1., 1.26, 1.5)},
}
CUE_KINDS = frozenset({"blip", "packet", "tick", "queue", "alarm", "latch",
                       "sweep", "processing", "impact", "success"})
GENERATOR_LEVELS = {"tick": 1.517, "thud": .503, "whoosh": .71,
                    "accent": 1.44, "riser": 1.123, "stinger": .8}
ATTACK_SECONDS = {"tick": 0., "thud": 0., "whoosh": 0., "accent": 0.,
                  "riser": .04, "stinger": 0.}
GENERATOR_DURATIONS = {"tick": .04, "thud": .18, "whoosh": .28,
                       "accent": .14, "riser": .15, "stinger": .22}
CUE_GESTURES = {
    "blip": ((0., "accent"),), "packet": ((0., "tick"),), "tick": ((0., "tick"),),
    "queue": ((0., "tick"), (.1, "tick"), (.2, "tick"), (.3, "tick")),
    "alarm": ((0., "thud"), (.18, "whoosh")),
    "latch": ((0., "tick"), (.04, "thud")), "sweep": ((0., "riser"),),
    "processing": tuple((i * .1, "tick") for i in range(7)),
    "impact": ((0., "thud"),), "success": ((0., "stinger"),),
}


@dataclass(frozen=True)
class AudioPlan:
    profile: str
    tempo_bpm: float
    events: tuple[dict, ...]

    def canonical(self) -> dict:
        return {"profile": self.profile, "tempo_bpm": self.tempo_bpm,
                "events": [dict(event) for event in self.events]}


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
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).digest()
    return int.from_bytes(digest[:8], "big")


class _XorShift32:
    def __init__(self, seed: int): self.state = seed & 0xffffffff

    def sample(self) -> float:
        value = self.state
        value ^= (value << 13) & 0xffffffff; value ^= value >> 17
        value ^= (value << 5) & 0xffffffff; self.state = value & 0xffffffff
        return (self.state / 0xffffffff) * 2 - 1


def _event_seed(plan_seed: int, sample_position: int, event_index: int) -> int:
    payload = (plan_seed.to_bytes(8, "big") + sample_position.to_bytes(8, "big", signed=True)
               + event_index.to_bytes(8, "big"))
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def _add(samples: np.ndarray, start: int, signal: np.ndarray) -> None:
    if start >= len(samples) or not len(signal): return
    source_start, destination_start = max(0, -start), max(0, start)
    count = min(len(signal) - source_start, len(samples) - destination_start)
    if count > 0:
        samples[destination_start:destination_start + count] += signal[source_start:source_start + count]


def _generator_signal(kind: str, gain: float, seed: int, pitch_scale: float = 1.) -> np.ndarray:
    """Render one calibrated reference generator in isolation."""
    count = round(GENERATOR_DURATIONS[kind] * SAMPLE_RATE)
    t = np.arange(count, dtype=np.float64) / SAMPLE_RATE
    sine = lambda hz: np.sin(2 * np.pi * hz * pitch_scale * t)
    if kind == "tick":
        rng, lp, edge = _XorShift32(seed), 0., np.empty(count)
        for i in range(count):
            raw = rng.sample(); lp += (raw - lp) * .35; edge[i] = (raw - lp) * .55
        signal = (sine(2200) * .5 + sine(3300) * .18 + edge) * np.exp(-t / .008) * .5
    elif kind == "thud":
        hz = (78 - 34 * (t / GENERATOR_DURATIONS["thud"])) * pitch_scale
        signal = (np.sin(2*np.pi*hz*t) * .9 + np.sin(2*np.pi*hz*2*t) * .12) * np.exp(-t/.055)
    elif kind == "whoosh":
        rng, lp, lp2, noise, p = (_XorShift32(seed + 7), 0., 0., np.empty(count),
                                  t / GENERATOR_DURATIONS["whoosh"])
        for i in range(count):
            k = .02 + .22 * math.sin(min(1., p[i] * 1.6) * math.pi)
            raw = rng.sample(); lp += (raw-lp)*k; lp2 += (lp-lp2)*k; noise[i] = lp2 * 3.2
        signal = (noise + sine(120 - 60*p) * .22) * (np.minimum(1, p/.08) * np.power(1-p, 1.7))
    elif kind == "accent":
        signal = (sine(880)*.5 + sine(1320)*.3) * np.exp(-t/.035) * .6
    elif kind == "riser":
        rng, lp, noise, p = (_XorShift32(seed + 13), 0., np.empty(count),
                             t / GENERATOR_DURATIONS["riser"])
        for i in range(count):
            k = .04 + .3*p[i]; lp += (rng.sample()-lp)*k; noise[i] = lp*1.6
        signal = (noise + sine(300+900*p)*.3) * (np.power(p,1.2)*(1-np.power(p,6)))
    elif kind == "stinger":
        rng, lp, noise = _XorShift32(seed + 29), 0., np.empty(count)
        for i in range(count):
            lp += (rng.sample()-lp)*.4; noise[i] = lp
        chord = sine(587.33)*.5 + sine(880)*.34 + sine(1174.66)*.16
        signal = chord*np.exp(-t/.07)*.85 + noise*np.exp(-t/.006)*.9
    else:
        raise ValueError(f"unknown generator kind: {kind}")
    return signal * gain * GENERATOR_LEVELS[kind]


def _cue_signal(kind: str, intensity: float, profile: dict, seed: int) -> np.ndarray:
    gain, scale, gesture = .25 + .75*intensity, profile["root"]/REFERENCE_ROOT, CUE_GESTURES[kind]
    length = max(round(offset*SAMPLE_RATE) + round(GENERATOR_DURATIONS[generator]*SAMPLE_RATE)
                 for offset, generator in gesture)
    signal = np.zeros(length)
    for i, (offset, generator) in enumerate(gesture):
        component_seed = (seed + i * 0x9e3779b9) & 0xffffffff
        _add(signal, round(offset*SAMPLE_RATE), _generator_signal(generator, gain, component_seed, scale))
    return signal


def _ambient(duration: float, plan: AudioPlan, rng: np.random.Generator) -> np.ndarray:
    """Retain the profile-driven lo-fi bed independently from cue RNG state."""
    count = round(duration*SAMPLE_RATE); samples = np.zeros(count); profile = PROFILES[plan.profile]
    beat = 60/plan.tempo_bpm; bar_duration = beat*4; progression = (1., 1.12246, 1.25992, .94387)
    detune = rng.uniform(.992, 1.008)
    for bar, start in enumerate(np.arange(0, duration, bar_duration)):
        length = min(round(bar_duration*SAMPLE_RATE), count-round(start*SAMPLE_RATE))
        if length <= 0: continue
        t = np.arange(length)/SAMPLE_RATE; fade = np.sin(np.linspace(0,np.pi,length))**.6
        root = profile["root"]*progression[bar%len(progression)]*detune
        chord = sum(np.sin(2*np.pi*root*ratio*t) for ratio in profile["color"])
        _add(samples, round(start*SAMPLE_RATE), (chord*.013 + np.sin(2*np.pi*root*.25*t)*.027)*fade)
    period = beat/2
    for i, tick_time in enumerate(np.arange(rng.uniform(0,period), duration, period)):
        tick = rng.normal(0,1,round(.018*SAMPLE_RATE))
        tick *= np.exp(-np.arange(len(tick))/(SAMPLE_RATE*.003)) * (.010 if i%2 else .018)
        _add(samples, round(tick_time*SAMPLE_RATE), tick)
    return samples


def soft_clip(samples: np.ndarray, ceiling: float = SOFT_CLIP_CEILING) -> np.ndarray:
    return np.tanh(samples/ceiling)*ceiling


def build_scene_soundtrack(output_wav: str | Path, topic: str, duration: float, audio: AudioPlan | dict) -> dict:
    """Render deterministic 48 kHz mono 16-bit PCM and publication metadata."""
    plan = audio if isinstance(audio, AudioPlan) else validate_audio_plan(audio)
    seed = stable_audio_seed(topic, plan); samples = _ambient(duration, plan, np.random.default_rng(seed))
    positions = []
    for index, event in enumerate(plan.events):
        sample = round(event["at"]*duration*SAMPLE_RATE); positions.append(sample)
        _add(samples, sample, _cue_signal(event["kind"], event["intensity"], PROFILES[plan.profile],
                                         _event_seed(seed, sample, index)))
    pcm = np.asarray(np.rint(np.clip(soft_clip(samples), -1, 1)*32767), dtype="<i2")
    path = Path(output_wav); path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(SAMPLE_RATE); output.writeframes(pcm.tobytes())
    return {"profile": plan.profile, "tempo_bpm": plan.tempo_bpm, "seed": seed,
            "cue_count": len(plan.events), "sample_positions": positions, "voiceover": False}
