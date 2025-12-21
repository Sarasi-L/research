#backend/services/monophonic/note_based_tempo.py

import numpy as np

def estimate_tempo_from_notes(notes):
    """
    Estimate tempo using detected note durations
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

    # Remove extremely short durations
    durations = durations[durations > 0.05]

    if len(durations) < 3:
        return {
            "tempo": None,
            "confidence": 0.0,
            "reason": "Unstable note durations"
        }

    median_duration = np.median(durations)

    tempo = 60.0 / median_duration

    # Regularity check
    std = np.std(durations)
    regularity = 1.0 - (std / median_duration)

    note_count = len(durations)

    count_factor = min(1.0, note_count / 8)
    confidence = max(0.0, min(1.0, regularity * count_factor))

    return {
        "tempo": round(float(tempo), 2),
        "confidence": round(float(confidence), 3),
        "median_note_duration": round(float(median_duration), 3),
        "note_count": note_count
    }

   
