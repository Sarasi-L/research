import numpy as np

# ==============================
# CONSTANTS
# ==============================

NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]

# Major & minor scale pitch classes (for validation)
KEY_SCALES = {
    "C major":  [0, 2, 4, 5, 7, 9, 11],
    "C# major": [1, 3, 5, 6, 8, 10, 0],
    "D major":  [2, 4, 6, 7, 9, 11, 1],
    "D# major": [3, 5, 7, 8, 10, 0, 2],
    "E major":  [4, 6, 8, 9, 11, 1, 3],
    "F major":  [5, 7, 9, 10, 0, 2, 4],
    "F# major": [6, 8, 10, 11, 1, 3, 5],
    "G major":  [7, 9, 11, 0, 2, 4, 6],
    "G# major": [8, 10, 0, 1, 3, 5, 7],
    "A major":  [9, 11, 1, 2, 4, 6, 8],
    "A# major": [10, 0, 2, 3, 5, 7, 9],
    "B major":  [11, 1, 3, 4, 6, 8, 10],

    "C minor":  [0, 2, 3, 5, 7, 8, 10],
    "C# minor": [1, 3, 4, 6, 8, 9, 11],
    "D minor":  [2, 4, 5, 7, 9, 10, 0],
    "D# minor": [3, 5, 6, 8, 10, 11, 1],
    "E minor":  [4, 6, 7, 9, 11, 0, 2],
    "F minor":  [5, 7, 8, 10, 0, 1, 3],
    "F# minor": [6, 8, 9, 11, 1, 2, 4],
    "G minor":  [7, 9, 10, 0, 2, 3, 5],
    "G# minor": [8, 10, 11, 1, 3, 4, 6],
    "A minor":  [9, 11, 0, 2, 4, 5, 7],
    "A# minor": [10, 0, 1, 3, 5, 6, 8],
    "B minor":  [11, 1, 2, 4, 6, 7, 9],
}

# ==============================
# CORE FUNCTIONS
# ==============================

def hz_to_pitch_class(freq):
    """
    Convert frequency (Hz) to pitch class [0–11]
    """
    if freq is None or freq <= 0 or np.isnan(freq):
        return None

    midi = int(round(69 + 12 * np.log2(freq / 440.0)))
    return midi % 12


def build_pitch_class_histogram(pitches_hz):
    """
    Build normalized pitch-class histogram from Hz values
    """
    histogram = np.zeros(12)

    for f in pitches_hz:
        pc = hz_to_pitch_class(f)
        if pc is not None:
            histogram[pc] += 1

    if histogram.sum() > 0:
        histogram /= histogram.sum()

    return histogram


def print_pitch_class_histogram(histogram):
    """
    Print histogram clearly for debugging / UI
    """
    print("\n[PITCH CLASS HISTOGRAM]")
    for i, v in enumerate(histogram):
        print(f"{NOTE_NAMES[i]:>2}: {v:.3f}")


def validate_key_with_histogram(histogram, detected_key):
    """
    Validate detected key by checking how much energy lies in-scale
    """
    if detected_key not in KEY_SCALES:
        raise ValueError(f"Unknown key: {detected_key}")

    scale_pcs = KEY_SCALES[detected_key]

    in_scale_energy = sum(histogram[pc] for pc in scale_pcs)
    out_scale_energy = 1.0 - in_scale_energy

    confidence = round(in_scale_energy, 3)

    return {
        "key": detected_key,
        "confidence": confidence,
        "in_scale_energy": round(in_scale_energy, 3),
        "out_of_scale_energy": round(out_scale_energy, 3),
        "status": "VALID" if confidence >= 0.6 else "WEAK"
    }



def validate_key(notes, key_detector=None):
    """
    Main callable function
    Args:
        notes: list of dicts {"pitch": Hz, ...}
        key_detector: optional callable that predicts key from notes
    Returns:
        dict with key validation info
    """
    # Extract pitches
    pitches = [n["pitch"] for n in notes if n["pitch"] is not None and n["pitch"] > 0]

    # Compute histogram
    hist = build_pitch_class_histogram(pitches)

    # Detect key using optional ML model or fallback to C major
    if key_detector is not None:
        key = key_detector(pitches)
    else:
        # Fallback: pick the key with max in-scale energy
        best_key = None
        best_energy = -1
        for k in KEY_SCALES.keys():
            energy = sum(hist[pc] for pc in KEY_SCALES[k])
            if energy > best_energy:
                best_energy = energy
                best_key = k
        key = best_key

    # Validate
    return validate_key_with_histogram(hist, key)
