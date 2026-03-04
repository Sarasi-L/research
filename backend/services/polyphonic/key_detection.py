# backend/services/polyphonic/key_detection.py

import numpy as np
import pretty_midi

# Krumhansl major/minor profiles
KRUMHANSL_MAJOR = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
     2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)

KRUMHANSL_MINOR = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
     2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)

KEY_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]

def detect_key(midi_path: str):
    """
    Detect key signature using Krumhansl–Schmuckler algorithm.
    Works with multi-track polyphonic MIDI.
    """
    print(f"\n[KEY] ===== Detecting key signature: {midi_path} =====")

    midi = pretty_midi.PrettyMIDI(midi_path)

    # Create pitch-class histogram
    pc_hist = np.zeros(12)

    for inst in midi.instruments:
        for note in inst.notes:
            pitch_class = note.pitch % 12
            pc_hist[pitch_class] += note.end - note.start  # weighted

    if pc_hist.sum() == 0:
        print("[KEY] No notes found! Default = C major")
        return "C", "major"

    pc_hist /= pc_hist.sum()

    # Correlate with all 12 rotations
    correlations_major = []
    correlations_minor = []

    for i in range(12):
        correlations_major.append(np.corrcoef(pc_hist, np.roll(KRUMHANSL_MAJOR, i))[0, 1])
        correlations_minor.append(np.corrcoef(pc_hist, np.roll(KRUMHANSL_MINOR, i))[0, 1])

    best_major = np.argmax(correlations_major)
    best_minor = np.argmax(correlations_minor)

    if correlations_major[best_major] >= correlations_minor[best_minor]:
        print(f"[KEY] Key detected: {KEY_NAMES[best_major]} major")
        return KEY_NAMES[best_major], "major"
    else:
        print(f"[KEY] Key detected: {KEY_NAMES[best_minor]} minor")
        return KEY_NAMES[best_minor], "minor"