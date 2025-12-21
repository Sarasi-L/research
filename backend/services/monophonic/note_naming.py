import math

# Pitch class names
SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F",
               "F#", "G", "G#", "A", "A#", "B"]

FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F",
              "Gb", "G", "Ab", "A", "Bb", "B"]

# Keys that prefer flats
FLAT_KEYS = {
    "F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb",
    "D minor", "G minor", "C minor", "F minor",
    "Bb minor", "Eb minor", "Ab minor"
}


def freq_to_midi(freq):
    """Convert frequency (Hz) to MIDI note number"""
    return int(round(69 + 12 * math.log2(freq / 440.0)))


def midi_to_note_name(midi, key):
    """
    Convert MIDI number to note name using key-aware spelling
    """
    pitch_class = midi % 12
    octave = (midi // 12) - 1

    use_flats = key in FLAT_KEYS

    note_name = (
        FLAT_NAMES[pitch_class]
        if use_flats
        else SHARP_NAMES[pitch_class]
    )

    return f"{note_name}{octave}"


def apply_key_aware_naming(quantized_notes, key):
    """
    Add musical note names to quantized notes
    """

    named_notes = []

    for note in quantized_notes:
        freq = note["pitch"]

        # Ignore invalid pitches
        if freq <= 0:
            note_name = "Rest"
        else:
            midi = freq_to_midi(freq)
            note_name = midi_to_note_name(midi, key)

        named_notes.append({
            **note,
            "midi": midi if freq > 0 else None,
            "note_name": note_name
        })

    return named_notes
