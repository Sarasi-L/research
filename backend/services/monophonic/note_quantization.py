# backend/services/monophonic/note_quantization.py

import math

# Supported musical durations (in beats)
NOTE_VALUES = {
    "whole": 4.0,
    "dotted_half": 3.0,
    "half": 2.0,
    "dotted_quarter": 1.5,
    "quarter": 1.0,
    "dotted_eighth": 0.75,
    "eighth": 0.5,
    "sixteenth": 0.25
}

def quantize_notes(notes, tempo, tolerance=0.3):
    """
    Convert note durations into musical note values

    Args:
        notes: list of {start, end, pitch}
        tempo: BPM (final accepted tempo)
        tolerance: allowed snapping error in beats

    Returns:
        Quantized notes with duration info
    """

    quantized = []

    for note in notes:
        duration_sec = note["end"] - note["start"]
        beats = (duration_sec * tempo) / 60.0

        # Find closest note value with tolerance
        best_match = None
        smallest_error = float("inf")

        for name, value in NOTE_VALUES.items():
            error = abs(beats - value)
            if error < smallest_error:
                smallest_error = error
                best_match = (name, value)

        # Snap to closest note if within tolerance, else unknown
        if smallest_error <= tolerance:
            duration_name, quantized_beats = best_match
        else:
            duration_name = "unknown"
            quantized_beats = round(beats, 2)

        quantized.append({
            "start": note["start"],
            "end": note["end"],
            "pitch": note["pitch"],
            "duration_beats": round(beats, 2),
            "quantized_beats": quantized_beats,
            "duration_name": duration_name
        })

    return quantized
