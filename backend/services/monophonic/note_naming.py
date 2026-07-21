# backend/services/monophonic/note_naming.py

import math

# Pitch class names
SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F",
               "F#", "G", "G#", "A", "A#", "B"]

FLAT_NAMES  = ["C", "Db", "D", "Eb", "E", "F",
               "Gb", "G", "Ab", "A", "Bb", "B"]

# Keys that prefer flats
FLAT_KEYS = {
    "F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb",
    "D minor", "G minor", "C minor", "F minor",
    "Bb minor", "Eb minor", "Ab minor"
}


def freq_to_midi(freq):
    """Convert frequency (Hz) to MIDI note number."""
    if freq <= 0:
        raise ValueError(f"freq_to_midi: invalid frequency {freq}")
    return int(round(69 + 12 * math.log2(freq / 440.0)))


def midi_to_note_name(midi, key):
    """Convert MIDI number to note name using key-aware spelling."""
    pitch_class = midi % 12
    octave = (midi // 12) - 1
    use_flats = key in FLAT_KEYS
    note_name = FLAT_NAMES[pitch_class] if use_flats else SHARP_NAMES[pitch_class]
    return f"{note_name}{octave}"


def apply_key_aware_naming(quantized_notes, key):
    """
    Add musical note names to quantized notes.

    FIX (CRITICAL): In the original code, `midi` was declared inside the
    `else` branch only. If `freq <= 0`, the variable `midi` from the
    PREVIOUS loop iteration was silently used, assigning a wrong MIDI
    number to rests/silent frames.

    Fix: always initialise `midi = None` at the top of each iteration,
    compute it only when freq > 0, and use it only then.
    """

    named_notes = []

    for note in quantized_notes:
        freq = note["pitch"]

        # FIX: always start with midi = None so it cannot leak between iterations
        midi = None
        note_name = "Rest"

        if freq > 0:
            try:
                midi = freq_to_midi(freq)
                note_name = midi_to_note_name(midi, key)
            except (ValueError, ZeroDivisionError):
                # Corrupted pitch value — treat as rest
                midi = None
                note_name = "Rest"

        named_notes.append({
            **note,
            "midi":      midi,       # None for rests; correct MIDI int for pitched notes
            "note_name": note_name
        })

    return named_notes