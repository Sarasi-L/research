# validate/note_segmentation_validation/note_segmentation_internal/internal_metrics.py

import numpy as np

def hz_to_cents(f, ref):
    return 1200 * np.log2(f / ref)

def compute_note_metrics(note, time, freq):
    """
    Compute pitch stability & purity for a single note
    """
    idx = np.where((time >= note["start"]) & (time <= note["end"]))[0]

    pitch_vals = freq[idx]
    pitch_vals = pitch_vals[~np.isnan(pitch_vals)]

    if len(pitch_vals) < 3:
        return None

    median_pitch = np.median(pitch_vals)

    # Pitch stability
    pitch_std = np.std(pitch_vals)

    # Purity (±50 cents)
    cents_diff = np.abs(hz_to_cents(pitch_vals, median_pitch))
    purity = np.mean(cents_diff < 50)

    duration = note["end"] - note["start"]

    return {
        "pitch_std": pitch_std,
        "purity": purity,
        "duration": duration
    }
