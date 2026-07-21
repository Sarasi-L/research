# backend/services/monophonic/note_based_tempo.py

import numpy as np


def estimate_tempo_from_notes(notes):
    """
    Estimate tempo using detected note durations.

    FIX (CRITICAL): The old code used median(all_durations) as the beat unit.
    This is wrong — a melody with mostly eighth notes would estimate a tempo
    2× too fast because the median duration is an eighth note, not a quarter.

    Correct approach:
    1. Collect all durations.
    2. Find the shortest stable cluster — this is the base subdivision (e.g. eighth note).
    3. Determine what musical value it most likely represents (eighth or quarter).
    4. Derive BPM from the quarter-note duration.
    """

    if not notes or len(notes) < 3:
        return {
            "tempo": None,
            "confidence": 0.0,
            "reason": "Insufficient notes"
        }

    durations = np.array([
        n["end"] - n["start"]
        for n in notes
        if n["end"] > n["start"]
    ])

    # Remove extremely short (noise) and extremely long (held notes) durations
    durations = durations[durations > 0.05]
    durations = durations[durations < 8.0]

    if len(durations) < 3:
        return {
            "tempo": None,
            "confidence": 0.0,
            "reason": "Unstable note durations"
        }

    # -----------------------------------------------------------------
    # FIX: Find base subdivision duration
    # Take the lower 40th percentile of durations → these are the short
    # notes that represent the subdivision (eighth or quarter note).
    # The median of this cluster is more stable than global median.
    # -----------------------------------------------------------------
    p40 = np.percentile(durations, 40)
    short_durs = durations[durations <= p40]

    if len(short_durs) < 2:
        short_durs = durations  # fallback if all notes are similar length

    subdivision_dur = float(np.median(short_durs))

    # -----------------------------------------------------------------
    # FIX: Determine if the subdivision is an eighth or quarter note.
    # Strategy: compute hypothetical BPM for both interpretations.
    #   - If subdivision = quarter note  → tempo = 60 / subdivision_dur
    #   - If subdivision = eighth note   → tempo = 60 / (subdivision_dur * 2)
    #
    # A quarter-note tempo should fall in the musical range 50–200 BPM.
    # Pick the interpretation that lands in that range.
    # -----------------------------------------------------------------
    tempo_if_quarter = 60.0 / subdivision_dur
    tempo_if_eighth = 60.0 / (subdivision_dur * 2.0)

    MUSICAL_RANGE = (50.0, 220.0)

    quarter_valid = MUSICAL_RANGE[0] <= tempo_if_quarter <= MUSICAL_RANGE[1]
    eighth_valid = MUSICAL_RANGE[0] <= tempo_if_eighth <= MUSICAL_RANGE[1]

    if quarter_valid and not eighth_valid:
        tempo = tempo_if_quarter
        beat_interpretation = "quarter"
    elif eighth_valid and not quarter_valid:
        tempo = tempo_if_eighth
        beat_interpretation = "eighth"
    elif quarter_valid and eighth_valid:
        # Both valid — prefer quarter if tempo is in common range (60–160)
        if MUSICAL_RANGE[0] <= tempo_if_quarter <= 160:
            tempo = tempo_if_quarter
            beat_interpretation = "quarter"
        else:
            tempo = tempo_if_eighth
            beat_interpretation = "eighth"
    else:
        # Neither valid — fall back to global median
        tempo = 60.0 / float(np.median(durations))
        beat_interpretation = "fallback"

    # -----------------------------------------------------------------
    # Confidence: based on consistency of durations
    # -----------------------------------------------------------------
    std = np.std(durations)
    median_dur = np.median(durations)
    regularity = 1.0 - min(1.0, std / (median_dur + 1e-6))
    count_factor = min(1.0, len(durations) / 8)
    confidence = max(0.0, min(1.0, regularity * count_factor))

    return {
        "tempo": round(float(tempo), 2),
        "confidence": round(float(confidence), 3),
        "subdivision_duration": round(subdivision_dur, 3),
        "beat_interpretation": beat_interpretation,
        "note_count": len(durations)
    }