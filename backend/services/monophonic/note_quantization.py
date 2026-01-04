# backend/services/monophonic/note_quantization.py

import math

# Supported musical durations (in beats), ordered large → small
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

ALLOWED_DURATIONS = sorted(NOTE_VALUES.values(), reverse=True)


def split_into_tied_durations(duration, tolerance=0.08):
    """
    Split a duration into standard note values using ties.
    Example: 2.23 → [2.0, 0.25]
    """
    remaining = duration
    parts = []

    for d in ALLOWED_DURATIONS:
        while remaining >= d - tolerance:
            parts.append(d)
            remaining -= d

    return parts


def quantize_notes(notes, tempo, tolerance=0.15):
    """
    Convert note durations into musical note values.
    Uses tie-splitting when duration does not match exactly.

    Args:
        notes: list of {start, end, pitch}
        tempo: BPM
        tolerance: snapping tolerance in beats

    Returns:
        Quantized notes with tie-aware duration info
    """

    quantized = []

    for note in notes:
        duration_sec = note["end"] - note["start"]
        beats = (duration_sec * tempo) / 60.0
        beats = round(beats, 2)

        # Try exact snapping first
        best_match = None
        smallest_error = float("inf")

        for name, value in NOTE_VALUES.items():
            error = abs(beats - value)
            if error < smallest_error:
                smallest_error = error
                best_match = (name, value)

        if smallest_error <= tolerance:
            # Clean match
            duration_name, quantized_beats = best_match
            quantized.append({
                "start": note["start"],
                "end": note["end"],
                "pitch": note["pitch"],
                "duration_beats": beats,
                "quantized_beats": quantized_beats,
                "duration_name": duration_name
            })

        else:
            # ---- TIE SPLITTING (FIX) ----
            parts = split_into_tied_durations(beats)

            if len(parts) == 1:
                # Still cannot express cleanly
                quantized.append({
                    "start": note["start"],
                    "end": note["end"],
                    "pitch": note["pitch"],
                    "duration_beats": beats,
                    "quantized_beats": beats,
                    "duration_name": "unknown"
                })
            else:
                quantized.append({
                    "start": note["start"],
                    "end": note["end"],
                    "pitch": note["pitch"],
                    "duration_beats": beats,
                    "quantized_beats": beats,
                    "duration_name": "tied",
                    "tied_parts": parts
                })

    return quantized

def quantize_duration(duration_beats, tolerance=0.15):
    """
    Validation helper:
    Quantize a duration (in beats) into a musical note name.
    """

    best_match = None
    smallest_error = float("inf")

    for name, value in NOTE_VALUES.items():
        error = abs(duration_beats - value)
        if error < smallest_error:
            smallest_error = error
            best_match = name

    if smallest_error <= tolerance:
        return best_match

    return "unknown"
