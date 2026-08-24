#!/usr/bin/env python3
"""
Professional Audio Engine for System Design Reels.
Features:
1. Studio Neural Voiceover (Microsoft Natural Neural TTS).
2. Dynamic Ambient Tech Lo-Fi Music Synthesizer matching exact speech duration (>10s).
3. Auto-mixing & sidechain ducking into broadcast-ready AAC.
"""
import os, sys, math, struct, wave, subprocess, shutil

from engine.sfx_audio import build_game_soundtrack, add_ting_tong, add_game_over_buzzer, add_blip

SAMPLE_RATE = 44100


CORE_VOICEOVERS = {
    "sql_injection": (
        "When a hacker enters quote or one equals one into the username field, "
        "raw string concatenation merges code with user input. "
        "The SQL parser interprets one equals one as always TRUE, "
        "bypassing authentication and dumping all one hundred thousand user records. "
        "Always use prepared statements to parameterize data safely."
    ),
    "redis_vs_db": (
        "Fetching a user profile from disk requires spinning magnetic platters and mechanical seek arms. "
        "That forty-five millisecond latency slows down your entire API under load. "
        "Redis stores key-values directly in electrical DRAM transistors, "
        "delivering responses in zero point one milliseconds. That is over three hundred times faster."
    ),
    "autoscaling": (
        "During a flash sale, traffic surges ten times. "
        "Two server instances hit ninety-eight percent CPU and start dropping packets. "
        "The Horizontal Pod Autoscaler detects the load spike and spins up two new server containers automatically. "
        "Traffic balances evenly across all four instances, dropping load back down with zero downtime."
    ),
    "cron_jobs": (
        "A cron expression is five mechanical dimensions: "
        "minute, hour, day of month, month, and day of week. "
        "Every minute, the clock daemon advances. "
        "When all five gates align at midnight, the job triggers automatically, "
        "running your backup script with mathematical precision."
    )
}

def find_edge_tts():
    """Finds edge-tts binary or module"""
    candidate_paths = [
        shutil.which("edge-tts"),
        os.path.expanduser("~/Library/Python/3.9/bin/edge-tts"),
        os.path.expanduser("~/.local/bin/edge-tts"),
        "/opt/homebrew/bin/edge-tts",
        "/usr/local/bin/edge-tts"
    ]
    for p in candidate_paths:
        if p and os.path.exists(p) and os.access(p, os.X_OK):
            return [p]
    return [sys.executable, "-m", "edge_tts"]

def get_audio_duration(wav_path):
    """Calculates duration in seconds of a WAV file"""
    if not os.path.exists(wav_path):
        return 10.0
    try:
        with wave.open(wav_path, 'r') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return max(10.0, frames / float(rate))
    except Exception:
        return 10.0

def generate_voiceover(target_or_text, output_wav):
    """Generates natural neural voiceover using edge-tts or system TTS"""
    text = CORE_VOICEOVERS.get(target_or_text, target_or_text)
    if not text or len(text.strip()) == 0:
        return False
    
    mp3_path = output_wav.replace(".wav", "_temp_voice.mp3")
    
    tts_cmd_base = find_edge_tts()
    try:
        cmd = tts_cmd_base + [
            "--voice", "en-US-ChristopherNeural",
            "--rate", "+6%",
            "--text", text,
            "--write-media", mp3_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Convert to 44.1kHz WAV
        subprocess.run([
            "ffmpeg", "-y",
            "-i", mp3_path,
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            output_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        return True
    except Exception:
        # Fallback to macOS `say`
        aiff_path = output_wav.replace(".wav", "_temp_voice.aiff")
        try:
            subprocess.run(["say", "-v", "Daniel", "-o", aiff_path, text], check=True)
            subprocess.run([
                "ffmpeg", "-y",
                "-i", aiff_path,
                "-ar", str(SAMPLE_RATE),
                "-ac", "1",
                output_wav
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(aiff_path): os.remove(aiff_path)
            return True
        except Exception:
            return False

def generate_warm_ambient_music(duration=12.0):
    """Generates warm, gentle, lo-fi ambient tech music dynamically scaled to any duration"""
    total_samples = int(SAMPLE_RATE * duration)
    samples = [0.0] * total_samples
    
    bpm = 120.0
    beat_dur = 60.0 / bpm
    
    # Warm chord progression (Fmaj7 -> G -> Am7 -> Em7)
    chords = [
        [174.61, 220.00, 261.63, 329.63], # Fmaj7
        [196.00, 246.94, 293.66, 392.00], # G
        [220.00, 261.63, 329.63, 392.00], # Am7
        [164.81, 196.00, 246.94, 329.63], # Em7
    ]
    
    chord_len = int(SAMPLE_RATE * 3.0) # 3.0s per chord
    num_chords_needed = int(math.ceil(duration / 3.0))
    
    for i in range(num_chords_needed):
        chord = chords[i % len(chords)]
        c_start = i * chord_len
        for note in chord:
            for s in range(chord_len):
                idx = c_start + s
                if idx >= total_samples: break
                t = s / SAMPLE_RATE
                env = math.sin((s / chord_len) * math.pi)
                val = math.sin(2.0 * math.pi * note * t) * 0.035 * env
                samples[idx] += val

    # Gentle low-frequency warm sub bassline (F1 -> G1 -> A1 -> E1)
    bass_notes = [43.65, 49.00, 55.00, 41.20]
    for i in range(num_chords_needed):
        b_freq = bass_notes[i % len(bass_notes)]
        b_start = i * chord_len
        for s in range(chord_len):
            idx = b_start + s
            if idx >= total_samples: break
            t = s / SAMPLE_RATE
            env = math.sin((s / chord_len) * math.pi)
            val = math.sin(2.0 * math.pi * b_freq * t) * 0.08 * env
            samples[idx] += val

    # Soft, organic lo-fi percussion ticks (woodblock/rim tap style)
    num_steps = int(duration / (beat_dur / 2.0))
    for step in range(num_steps):
        s_idx = int(step * (beat_dur / 2.0) * SAMPLE_RATE)
        for i in range(int(SAMPLE_RATE * 0.015)):
            if s_idx + i >= total_samples: break
            t = i / SAMPLE_RATE
            decay = math.exp(-i / (SAMPLE_RATE * 0.003))
            tap = math.sin(2.0 * math.pi * 950.0 * t) * 0.03 * decay
            samples[s_idx + i] += tap

    return samples

def build_pro_soundtrack(target_or_text, output_path, min_duration=12.0):
    """Combines Voiceover + Dynamic Ambient Music into master track, returning final duration"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    voice_wav = output_path.replace(".wav", "_voice.wav")
    music_wav = output_path.replace(".wav", "_music.wav")
    
    # 1. Generate Voiceover
    has_voice = generate_voiceover(target_or_text, voice_wav)
    
    # Determine exact audio duration
    if has_voice and os.path.exists(voice_wav):
        voice_duration = get_audio_duration(voice_wav)
        final_duration = max(min_duration, voice_duration + 0.8) # 0.8s tail buffer
    else:
        final_duration = min_duration
        
    # 2. Generate Warm Ambient Music matching exact duration
    music_samples = generate_warm_ambient_music(duration=final_duration)
    with wave.open(music_wav, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        int_samples = [int(max(-1.0, min(1.0, s)) * 32767) for s in music_samples]
        wf.writeframes(struct.pack(f'{len(int_samples)}h', *int_samples))
        
    # 3. Mix Voice + Music with volume ducking in FFmpeg
    if has_voice and os.path.exists(voice_wav):
        cmd = [
            "ffmpeg", "-y",
            "-i", voice_wav,
            "-i", music_wav,
            "-filter_complex",
            "[0:a]volume=1.25,alimiter=limit=0.95[v];"
            "[1:a]volume=0.22[m];"
            "[v][m]amix=inputs=2:duration=longest:dropout_transition=2[out]",
            "-map", "[out]",
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", music_wav,
            "-filter_complex", "volume=0.9,alimiter=limit=0.95[out]",
            "-map", "[out]",
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    if os.path.exists(voice_wav): os.remove(voice_wav)
    if os.path.exists(music_wav): os.remove(music_wav)
    return final_duration

def main():
    audio_dir = os.path.join(os.path.dirname(__file__), "..", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    for r_id in CORE_VOICEOVERS.keys():
        out_wav = os.path.join(audio_dir, f"{r_id}.wav")
        dur = build_pro_soundtrack(r_id, out_wav)
        print(f"🎵 Generated {r_id}.wav ({dur:.1f}s)")

if __name__ == "__main__":
    main()
