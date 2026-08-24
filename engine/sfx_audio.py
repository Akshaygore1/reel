#!/usr/bin/env python3
"""
Procedural Game SFX & Ambient Sound Engine for System Design Reels.
100% Python, Zero Voiceover, Zero external dependencies.
Engineered for Infinite Seamless Looping and Crystal-Clear Sound Quality.

Soundtrack Architecture:
1. Lo-Fi Ambient Tech Synth Bed (Fmaj7 -> G -> Am7 -> Em7) with Sub-Bass @ -18dB.
2. Crisp 8-bit UI micro-blips & rhythmic hi-hat clock ticks.
3. Descending alert saw-buzzer at Beat 2 (3.0s).
4. Shimmering "Ting-Tong" dual bell victory chime at Beat 3 (6.0s).
5. Seamless crossfade boundary guaranteeing zero pop/click when looping indefinitely.
"""
import os, math, struct, wave

SAMPLE_RATE = 44100

def add_blip(samples, start_time, freq=1100.0, volume=0.22, duration=0.045):
    """Adds a crisp, punchy 8-bit UI / packet blip with fast attack and natural decay"""
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(duration * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples): break
        t = i / SAMPLE_RATE
        decay = math.exp(-i / (SAMPLE_RATE * 0.010))
        v1 = math.sin(2.0 * math.pi * freq * t) * 0.75
        v2 = math.sin(2.0 * math.pi * (freq * 1.5) * t) * 0.25
        samples[idx] += (v1 + v2) * volume * decay

def add_clock_tick(samples, start_time, volume=0.08):
    """Subtle high-tech 8th-note rhythm tick for forward driving momentum"""
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(0.02 * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples): break
        decay = math.exp(-i / (SAMPLE_RATE * 0.003))
        noise = (math.sin(i * 12.34) * 0.5 + math.sin(i * 45.67) * 0.5)
        samples[idx] += noise * volume * decay

def add_ting_tong(samples, start_time, volume=0.52):
    """
    High-Definition 'Ting-Tong' two-tone victory/success chime.
    Tone 1 (Ting): 659.25 Hz (E5) + bell harmonics
    Tone 2 (Tong): 987.77 Hz (B5) + bell harmonics
    """
    tones = [
        {"freq": 659.25, "delay": 0.00, "dur": 0.80},
        {"freq": 987.77, "delay": 0.20, "dur": 1.20}
    ]
    for tone in tones:
        s_start = int((start_time + tone["delay"]) * SAMPLE_RATE)
        n_samples = int(tone["dur"] * SAMPLE_RATE)
        f0 = tone["freq"]
        for i in range(n_samples):
            idx = s_start + i
            if idx >= len(samples): break
            t = i / SAMPLE_RATE
            decay = math.exp(-i / (SAMPLE_RATE * 0.25))
            v1 = math.sin(2.0 * math.pi * f0 * t) * 0.65
            v2 = math.sin(2.0 * math.pi * (f0 * 2.0) * t) * 0.22
            v3 = math.sin(2.0 * math.pi * (f0 * 3.01) * t) * 0.09
            v4 = math.sin(2.0 * math.pi * (f0 * 4.16) * t) * 0.04
            samples[idx] += (v1 + v2 + v3 + v4) * volume * decay

def add_game_over_buzzer(samples, start_time, volume=0.40, duration=0.85):
    """
    Punchy 'Game Over' / Alert descending alarm buzzer.
    Sawtooth/square edge dropping from 270Hz down to 85Hz with 22Hz alarm tremolo.
    """
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(duration * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples): break
        t = i / SAMPLE_RATE
        decay = math.exp(-i / (SAMPLE_RATE * 0.40))
        freq = 270.0 * math.exp(-t * 1.4)
        am = 0.55 + 0.45 * math.sin(2.0 * math.pi * 22.0 * t)
        phase = 2.0 * math.pi * freq * t
        s1 = math.sin(phase)
        s2 = 0.5 * math.sin(2.0 * phase)
        s3 = 0.3 * math.sin(3.0 * phase)
        s4 = 0.2 * math.sin(5.0 * phase)
        samples[idx] += (s1 + s2 + s3 + s4) * volume * am * decay

def generate_ambient_synth_bed(samples, duration=10.0):
    """Generates warm, filtered lo-fi chords & sub-bassline sitting cleanly at -18dB"""
    total_samples = len(samples)
    # Chords: Fmaj7 -> G -> Am7 -> Em7 (4 bars @ 2.5s each = exactly 10.0s)
    chords = [
        [174.61, 220.00, 261.63, 329.63], # Fmaj7
        [196.00, 246.94, 293.66, 392.00], # G
        [220.00, 261.63, 329.63, 392.00], # Am7
        [164.81, 196.00, 246.94, 329.63], # Em7
    ]
    chord_len = int(SAMPLE_RATE * 2.5)
    num_chords = int(math.ceil(duration / 2.5))

    for i in range(num_chords):
        chord = chords[i % len(chords)]
        c_start = i * chord_len
        for note in chord:
            for s in range(chord_len):
                idx = c_start + s
                if idx >= total_samples: break
                t = s / SAMPLE_RATE
                env = math.sin((s / chord_len) * math.pi)
                val = math.sin(2.0 * math.pi * note * t) * 0.038 * env
                samples[idx] += val

    # Sub-Bass: F1 (43.6Hz) -> G1 (49.0Hz) -> A1 (55.0Hz) -> E1 (41.2Hz)
    bass_notes = [43.65, 49.00, 55.00, 41.20]
    for i in range(num_chords):
        b_freq = bass_notes[i % len(bass_notes)]
        b_start = i * chord_len
        for s in range(chord_len):
            idx = b_start + s
            if idx >= total_samples: break
            t = s / SAMPLE_RATE
            env = math.sin((s / chord_len) * math.pi)
            val = math.sin(2.0 * math.pi * b_freq * t) * 0.070 * env
            samples[idx] += val

def generate_gc_ambient_bed(samples, duration=10.0):
    """Memory-GC score: tense minor pulses that resolve into a bright open fifth."""
    total_samples = len(samples)
    chords = [
        [146.83, 220.00, 293.66, 349.23],  # Dm7 — allocation hum
        [130.81, 196.00, 261.63, 311.13],  # Cm color — heap pressure
        [146.83, 220.00, 293.66, 369.99],  # D major — collector arrives
        [196.00, 293.66, 392.00, 493.88],  # G open fifth — memory cleared
    ]
    bass_notes = [36.71, 32.70, 36.71, 49.00]
    chord_len = int(SAMPLE_RATE * 2.5)
    for bar, chord in enumerate(chords):
        start = bar * chord_len
        for note in chord:
            for s in range(chord_len):
                idx = start + s
                if idx >= total_samples:
                    break
                t = s / SAMPLE_RATE
                env = math.sin((s / chord_len) * math.pi)
                # A slow tremolo suggests memory pages breathing under pressure.
                trem = 0.72 + 0.28 * math.sin(2 * math.pi * 2.0 * t)
                samples[idx] += math.sin(2 * math.pi * note * t) * 0.030 * env * trem
        for s in range(chord_len):
            idx = start + s
            if idx >= total_samples:
                break
            t = s / SAMPLE_RATE
            env = math.sin((s / chord_len) * math.pi)
            samples[idx] += math.sin(2 * math.pi * bass_notes[bar] * t) * 0.065 * env

def add_sweep_whoosh(samples, start_time, volume=0.18, duration=0.55):
    """Deterministic filtered-noise sweep for reclaimed objects."""
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(duration * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples):
            break
        t = i / SAMPLE_RATE
        p = i / max(1, n_samples - 1)
        env = math.sin(math.pi * p) ** 1.5
        carrier = (math.sin(i * 0.73) + 0.55 * math.sin(i * 1.91) + 0.25 * math.sin(i * 4.37))
        tone = math.sin(2 * math.pi * (180 + 900 * p) * t)
        samples[idx] += (carrier * 0.22 + tone * 0.45) * volume * env

def add_cleanup_thump(samples, start_time, volume=0.32, duration=0.28):
    """Short compactor/bin impact used when garbage leaves the heap."""
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(duration * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples):
            break
        t = i / SAMPLE_RATE
        decay = math.exp(-i / (SAMPLE_RATE * 0.075))
        freq = 92.0 - 42.0 * min(1.0, t / duration)
        samples[idx] += (math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * freq * 2 * t)) * volume * decay

def add_impact_boom(samples, start_time, volume=0.55, duration=0.90):
    """
    Sub-bass impact boom / punch chord for explosive transitions (e.g. BOOM full text dump).
    Puckering sub-sine 80Hz -> 32Hz with fast punch attack and warm resonance.
    """
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(duration * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples): break
        t = i / SAMPLE_RATE
        decay = math.exp(-i / (SAMPLE_RATE * 0.28))
        freq = 90.0 * math.exp(-t * 2.2) + 32.0
        phase = 2.0 * math.pi * freq * t
        s1 = math.sin(phase)
        s2 = 0.4 * math.sin(phase * 0.5)
        # Add subtle noise burst at attack
        noise = (math.sin(i * 37.1) * 0.2) * math.exp(-i / (SAMPLE_RATE * 0.015))
        samples[idx] += (s1 + s2 + noise) * volume * decay


def add_packet_toot(samples, start_time, freq=520.0, volume=0.24, duration=0.11):
    """Rounded, gamified network-packet toot with a tiny pitch lift on launch."""
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(duration * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples): break
        t = i / SAMPLE_RATE
        p = i / max(1, n_samples - 1)
        env = min(1.0, p / 0.08) * math.exp(-4.8 * p)
        f = freq * (0.92 + 0.12 * min(1.0, p / 0.35))
        body = math.sin(2 * math.pi * f * t) + 0.28 * math.sin(2 * math.pi * f * 2 * t)
        samples[idx] += body * volume * env


def add_mcp_packet_blip(samples, start_time, freq=720.0, volume=0.12, duration=0.075):
    """Soft glassy MCP packet cue without the nasal pitch lift of packet_toot."""
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(duration * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples): break
        t = i / SAMPLE_RATE
        p = i / max(1, n_samples - 1)
        attack = min(1.0, p / 0.16)
        env = attack * math.exp(-7.5 * p)
        glass = (math.sin(2 * math.pi * freq * t) * 0.72 +
                 math.sin(2 * math.pi * freq * 2.01 * t) * 0.10 +
                 math.sin(2 * math.pi * freq * 0.50 * t) * 0.18)
        samples[idx] += glass * volume * env


def add_connector_click(samples, start_time, pitch=1.0, volume=0.28):
    """Mechanical socket insertion: contact, metal latch, then seated thump."""
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(0.18 * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples): break
        t = i / SAMPLE_RATE
        contact = math.sin(i * 13.7) * math.exp(-t / 0.008)
        latch_t = max(0.0, t - 0.045)
        latch = math.sin(2 * math.pi * 1450 * pitch * latch_t) * math.exp(-latch_t / 0.018) if t >= 0.045 else 0.0
        seat_t = max(0.0, t - 0.075)
        seat = math.sin(2 * math.pi * 105 * pitch * seat_t) * math.exp(-seat_t / 0.055) if t >= 0.075 else 0.0
        samples[idx] += (contact * 0.18 + latch * 0.48 + seat * 0.72) * volume


def add_rejected_adapter(samples, start_time, pitch=1.0, volume=0.22):
    """A mismatched plug scraping the socket and bouncing back."""
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(0.42 * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples): break
        t = i / SAMPLE_RATE
        p = i / max(1, n_samples - 1)
        scrape = (math.sin(i * 1.73) + 0.45 * math.sin(i * 4.91)) * math.sin(math.pi * min(1.0, p * 2.2))
        spring = math.sin(2 * math.pi * (210 * pitch - 95 * p) * t) * math.exp(-5.5 * p)
        samples[idx] += (scrape * 0.055 + spring * 0.28) * volume


def add_discovery_scan(samples, start_time, duration=2.15, volume=0.16):
    """Rising capability scan synchronized with list_tools travel."""
    s_start = int(start_time * SAMPLE_RATE)
    n_samples = int(duration * SAMPLE_RATE)
    for i in range(n_samples):
        idx = s_start + i
        if idx >= len(samples): break
        t = i / SAMPLE_RATE
        p = i / max(1, n_samples - 1)
        freq = 190 + 760 * (p ** 1.35)
        gate = 0.32 + 0.68 * (1 if int(t * 12) % 2 == 0 else 0.22)
        env = math.sin(math.pi * p) ** 0.75
        samples[idx] += (math.sin(2 * math.pi * freq * t) + 0.22 * math.sin(2 * math.pi * freq * 2.01 * t)) * volume * gate * env


def add_server_processing(samples, start_time, duration=0.75, volume=0.12):
    """Restrained processing shimmer while the weather server executes."""
    for step in range(int(duration / 0.15)):
        add_mcp_packet_blip(samples, start_time + step * 0.15,
                            freq=540 + (step % 3) * 70,
                            volume=volume * 0.58, duration=0.065)


def add_result_resolve(samples, start_time, volume=0.25):
    """Resolved protocol chord caused by the structured result landing."""
    for note, delay in ((261.63, 0.00), (329.63, 0.035), (392.00, 0.070), (523.25, 0.105)):
        s_start = int((start_time + delay) * SAMPLE_RATE)
        for i in range(int(0.78 * SAMPLE_RATE)):
            idx = s_start + i
            if idx >= len(samples): break
            t = i / SAMPLE_RATE
            env = (1 - math.exp(-t / 0.018)) * math.exp(-t / 0.34)
            samples[idx] += (math.sin(2 * math.pi * note * t) + 0.12 * math.sin(2 * math.pi * note * 2 * t)) * volume * env


def generate_mcp_soundscape(samples, duration):
    """Clean MCP apparatus SFX with intentional silence between events."""
    scale = duration / 18.0
    for n, when in enumerate((1.35, 1.72, 2.09, 2.46, 3.05, 3.42)):
        add_mcp_packet_blip(samples, when * scale, freq=680 + n * 26, volume=0.105)
    for n, when in enumerate((6.05, 7.65, 9.25)):
        add_rejected_adapter(samples, when * scale, pitch=0.92 + n * 0.10)
    for n, when in enumerate((10.82, 11.02, 11.22)):
        add_connector_click(samples, when * scale, pitch=0.92 + n * 0.08)
    add_discovery_scan(samples, 11.05 * scale, duration=2.10 * scale)
    for n, when in enumerate((11.25, 11.72, 12.20, 12.68, 13.10)):
        add_mcp_packet_blip(samples, when * scale, freq=720 + n * 30, volume=0.11)
    for n, when in enumerate((13.28, 13.66, 14.04, 14.42, 14.80)):
        add_mcp_packet_blip(samples, when * scale, freq=820 - n * 25, volume=0.12)
    add_server_processing(samples, 14.86 * scale, duration=0.70 * scale)
    for n, when in enumerate((15.18, 15.50, 15.82, 16.14, 16.46)):
        add_mcp_packet_blip(samples, when * scale, freq=650 + n * 34, volume=0.11)
    add_result_resolve(samples, 16.58 * scale, volume=0.20)

def apply_loop_crossfade(samples, crossfade_sec=0.08):
    """Smoothly blends the end of the audio buffer into the start for 100% pop-free looping"""
    cf_samples = int(crossfade_sec * SAMPLE_RATE)
    for i in range(cf_samples):
        t = i / cf_samples
        head_idx = i
        tail_idx = len(samples) - cf_samples + i
        if tail_idx >= len(samples): break
        # Equal power crossfade
        w_tail = math.cos(t * math.pi * 0.5)
        w_head = math.sin(t * math.pi * 0.5)
        blended = samples[tail_idx] * w_tail + samples[head_idx] * w_head
        samples[tail_idx] = blended * w_tail
        samples[head_idx] = blended * w_head

def build_game_soundtrack(output_wav, duration=10.0, beat1_end=3.0, beat2_end=6.0, boom_time=8.0, theme="default"):
    """
    Builds the master game soundtrack with zero voiceover:
    - Ambient synth chords & sub-bass throughout.
    - Periodic crisp UI micro-blips during normal traffic (Beat 1 & Beat 3).
    - Harsh game-over / alert buzzer at crisis (Beat 2 start).
    - Glorious 'Ting-Tong' level-up chime at resolution (Beat 3 start).
    - Explosive sub-bass impact boom at boom_time.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_wav)), exist_ok=True)
    total_samples = int(SAMPLE_RATE * duration)
    samples = [0.0] * total_samples

    # 1. Topic-aware synth bed; default preserves the established brand score.
    if theme == "mcp_protocol":
        generate_mcp_soundscape(samples, duration=duration)
    elif theme == "memory_gc":
        generate_gc_ambient_bed(samples, duration=duration)
    else:
        generate_ambient_synth_bed(samples, duration=duration)

    # 2. Rhythmic Clock Ticks every 0.25s (120 BPM 8th-notes)
    num_ticks = 0 if theme == "mcp_protocol" else int(duration / 0.25)
    for i in range(num_ticks):
        t = i * 0.25
        if t < duration - 0.1:
            add_clock_tick(samples, t, volume=0.06 if (i % 2 == 0) else 0.03)

    # 3. UI Micro-blips / Token typing blips
    timing_scale = duration / 10.0
    blip_times = ([] if theme == "mcp_protocol" else
                  [0.25, 0.70, 1.15, 1.60, 2.05, 2.50, 6.15, 6.75, 7.35, 8.85]
                  if theme == "memory_gc" else
                  [0.20, 0.55, 0.90, 1.30, 1.70, 2.10, 2.50, 6.20, 6.60, 7.00, 7.40, 8.60, 9.10])
    for bt in (t * timing_scale for t in blip_times):
        if bt < duration:
            freq = (620.0 + (bt * 55.0) % 180.0) if theme == "memory_gc" else (1050.0 + (bt * 40.0) % 220.0)
            add_blip(samples, bt, freq=freq, volume=0.18)

    # 4. Game Over / Alarm Buzzer at Crisis (Beat 2 @ 3.0s)
    if theme != "mcp_protocol" and beat1_end < duration:
        add_game_over_buzzer(samples, start_time=beat1_end, volume=0.40, duration=0.85)

    # 5. Ting-Tong Success Chime at Resolution (Beat 3 @ 6.0s)
    if theme != "mcp_protocol" and beat2_end < duration:
        add_ting_tong(samples, start_time=beat2_end, volume=0.52)

    if theme == "memory_gc":
        add_sweep_whoosh(samples, 6.35 * timing_scale, volume=0.20)
        add_sweep_whoosh(samples, 7.05 * timing_scale, volume=0.17)
        add_cleanup_thump(samples, 7.65 * timing_scale, volume=0.34)
        add_cleanup_thump(samples, 8.20 * timing_scale, volume=0.28)

    # 6. Sub-bass Impact Boom (at 8.0s)
    if theme != "mcp_protocol" and boom_time and boom_time < duration:
        add_impact_boom(samples, start_time=boom_time, volume=0.58)

    # 7. Apply Seamless Loop Crossfade
    apply_loop_crossfade(samples, crossfade_sec=0.08)

    # 8. Soft-limiting & Normalization
    peak = max(max(abs(s) for s in samples), 0.001)
    gain = 0.92 / peak if peak > 0.92 else 1.0

    # Export to 16-bit PCM WAV
    with wave.open(output_wav, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        int_samples = [int(max(-1.0, min(1.0, s * gain)) * 32767) for s in samples]
        wf.writeframes(struct.pack(f'{len(int_samples)}h', *int_samples))

    return duration

if __name__ == "__main__":
    out = "audio/game_sfx_test.wav"
    build_game_soundtrack(out, duration=10.0)
    print(f"Generated {out}")
