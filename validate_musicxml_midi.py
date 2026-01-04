# backend/evaluation/validate_audio_vs_midi.py

import librosa
import numpy as np
import pretty_midi
import matplotlib.pyplot as plt
import math

from backend.services.monophonic.preprocess_monophonic_audio import preprocess_audio
from backend.services.monophonic.pitch_extraction import extract_pitch

# ======================================================
# 🔧 PATHS (EDIT ONLY THESE)
# ======================================================
AUDIO_PATH = "nokia_tune_ver_1993.mp3"
MIDI_PATH  = "nokia.mid"


# ======================================================
# 🎵 UTILS
# ======================================================
def midi_to_hz(midi):
    return 440.0 * (2 ** ((midi - 69) / 12))


def cents_error(f1, f2):
    return abs(1200 * math.log2(f1 / f2))


# ======================================================
# 🎼 LOAD AUDIO & CREPE PITCH
# ======================================================
print("[INFO] Loading audio & extracting CREPE pitch...")

y, sr = preprocess_audio(AUDIO_PATH)
time, freq, conf = extract_pitch(y, sr)

time = np.array(time)
freq = np.array(freq)
conf = np.array(conf)

# Keep only confident frames
freq[conf < 0.6] = np.nan

print(f"[INFO] Audio pitch frames: {len(freq)}")


# ======================================================
# 🎹 LOAD MIDI NOTES
# ======================================================
print("[INFO] Extracting notes from MIDI...")

pm = pretty_midi.PrettyMIDI(MIDI_PATH)

midi_notes = []
for inst in pm.instruments:
    for n in inst.notes:
        midi_notes.append({
            "start": n.start,
            "end": n.end,
            "midi": n.pitch
        })

print(f"[INFO] MIDI notes: {len(midi_notes)}")


# ======================================================
# 🎯 NOTE-LEVEL PITCH VALIDATION
# ======================================================
def validate_note_pitch(times, freqs, notes):
    errors = []
    correct = 0
    evaluated = 0

    for note in notes:
        frames = [
            f for t, f in zip(times, freqs)
            if note["start"] <= t <= note["end"]
            and not np.isnan(f)
        ]

        if len(frames) < 5:
            continue

        median_freq = np.median(frames)
        midi_freq = midi_to_hz(note["midi"])

        err = cents_error(median_freq, midi_freq)
        errors.append(err)

        if err <= 50:   # ≤ 50 cents = correct pitch
            correct += 1

        evaluated += 1

    if evaluated == 0:
        return None

    return {
        "evaluated_notes": evaluated,
        "pitch_accuracy": round(100 * correct / evaluated, 2),
        "mean_cents_error": round(float(np.mean(errors)), 2),
        "median_cents_error": round(float(np.median(errors)), 2)
    }


print("[INFO] Computing pitch accuracy...")
results = validate_note_pitch(time, freq, midi_notes)

print("\n----- PITCH VALIDATION -----")
for k, v in results.items():
    print(f"{k:22s}: {v}")


# ======================================================
# 📊 VISUAL ALIGNMENT PLOT (CORRECT)
# ======================================================
print("[INFO] Plotting pitch alignment...")

plt.figure(figsize=(14, 4))

# Audio pitch
plt.plot(
    time,
    librosa.hz_to_midi(freq),
    label="Audio Pitch (CREPE)",
    linewidth=1
)

# MIDI notes
for n in midi_notes:
    plt.hlines(
        n["midi"],
        n["start"],
        n["end"],
        colors="orange",
        linewidth=3
    )

plt.xlabel("Time (seconds)")
plt.ylabel("MIDI Pitch")
plt.title("Audio vs Generated MIDI (Note-Level Alignment)")
plt.legend()
plt.tight_layout()
plt.show()
