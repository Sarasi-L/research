# backend/services/monophonic/key_detection.py

import numpy as np

# Pitch class profiles (Krumhansl & Kessler)
MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
     2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)

MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
     2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]


def hz_to_pitch_class(freq):
    """
    Convert frequency (Hz) to pitch class index (0–11)
    """
    midi = 69 + 12 * np.log2(freq / 440.0)
    return int(round(midi)) % 12


def detect_key(notes):
    """
    Detect musical key from quantized monophonic notes

    Args:
        notes: list of {pitch, duration_beats}

    Returns:
        dict with key, mode, confidence
    """

    if not notes:
        return None

    pitch_class_hist = np.zeros(12)

    for note in notes:
        freq = note["pitch"]
        dur = note.get("duration_beats", 1.0)

        if freq <= 0:
            continue

        pc = hz_to_pitch_class(freq)
        pitch_class_hist[pc] += dur

    # Normalize
    pitch_class_hist /= np.sum(pitch_class_hist)

    best_score = -np.inf
    best_key = None
    best_mode = None

    for i in range(12):
        major_score = np.corrcoef(
            np.roll(MAJOR_PROFILE, i),
            pitch_class_hist
        )[0, 1]

        minor_score = np.corrcoef(
            np.roll(MINOR_PROFILE, i),
            pitch_class_hist
        )[0, 1]

        if major_score > best_score:
            best_score = major_score
            best_key = NOTE_NAMES[i]
            best_mode = "major"

        if minor_score > best_score:
            best_score = minor_score
            best_key = NOTE_NAMES[i]
            best_mode = "minor"

    return {
        "key": best_key,
        "mode": best_mode,
        "confidence": round(float(best_score), 3)
    }
