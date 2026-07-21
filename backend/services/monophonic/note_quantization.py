# backend/services/monophonic/note_quantization.py

import math

# Supported musical durations (in beats), ordered large → small
NOTE_VALUES = {
    "whole":          4.0,
    "dotted_half":    3.0,
    "half":           2.0,
    "dotted_quarter": 1.5,
    "quarter":        1.0,
    "dotted_eighth":  0.75,
    "eighth":         0.5,
    "sixteenth":      0.25
}

ALLOWED_DURATIONS = sorted(NOTE_VALUES.values(), reverse=True)

# FIX: Tightened tolerance from 0.15 → 0.07 beats.
# At 120 BPM a sixteenth note = 0.25 beats.
# Old tolerance of 0.15 meant anything between 0.10–0.40 beats
# could snap to a sixteenth, swallowing eighth notes.
# 0.07 beats ≈ 35ms at 120 BPM — still forgiving for timing imprecision.
DEFAULT_QUANTIZE_TOLERANCE = 0.07


def split_into_tied_durations(duration, tolerance=0.06):
    """
    Split a duration into standard note values using ties.
    Example: 2.23 → [2.0, 0.25]

    FIX: Tightened inner tolerance to 0.06 to match tighter quantization.
    """
    remaining = duration
    parts = []

    for d in ALLOWED_DURATIONS:
        while remaining >= d - tolerance:
            parts.append(d)
            remaining -= d
            if remaining < 0.01:
                break

    return parts if parts else [duration]


def quantize_notes(notes, tempo, tolerance=DEFAULT_QUANTIZE_TOLERANCE):
    """
    Convert note durations into musical note values.

    FIX: Tightened tolerance to 0.07 beats (was 0.15).
    FIX: Duration clamped to minimum of sixteenth note (0.25 beats)
         to prevent zero-length or near-zero notes in output.

    Args:
        notes: list of {start, end, pitch}
        tempo: BPM
        tolerance: snapping tolerance in beats

    Returns:
        Quantized notes with tie-aware duration info
    """

    quantized = []
    beats_per_second = tempo / 60.0

    for note in notes:
        duration_sec = note["end"] - note["start"]
        beats = duration_sec * beats_per_second
        beats = round(beats, 3)

        # FIX: clamp minimum to sixteenth note — avoids 0-beat ghost notes
        beats = max(beats, 0.25)

        # Try exact snapping first
        best_match = None
        smallest_error = float("inf")

        for name, value in NOTE_VALUES.items():
            error = abs(beats - value)
            if error < smallest_error:
                smallest_error = error
                best_match = (name, value)

        if smallest_error <= tolerance:
            duration_name, quantized_beats = best_match
            quantized.append({
                "start":           note["start"],
                "end":             note["end"],
                "pitch":           note["pitch"],
                "duration_beats":  beats,
                "quantized_beats": quantized_beats,
                "duration_name":   duration_name
            })

        else:
            # Tie splitting for irregular durations
            parts = split_into_tied_durations(beats)

            if len(parts) == 1:
                # Cannot express cleanly — snap to nearest anyway
                # rather than emitting "unknown" (which breaks MusicXML)
                duration_name, quantized_beats = best_match
                quantized.append({
                    "start":           note["start"],
                    "end":             note["end"],
                    "pitch":           note["pitch"],
                    "duration_beats":  beats,
                    "quantized_beats": quantized_beats,
                    "duration_name":   duration_name  # FIX: no more "unknown"
                })
            else:
                quantized.append({
                    "start":           note["start"],
                    "end":             note["end"],
                    "pitch":           note["pitch"],
                    "duration_beats":  beats,
                    "quantized_beats": beats,
                    "duration_name":   "tied",
                    "tied_parts":      parts
                })

    return quantized


def quantize_duration(duration_beats, tolerance=DEFAULT_QUANTIZE_TOLERANCE):
    """
    Validation helper: Quantize a duration (in beats) into a musical note name.
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