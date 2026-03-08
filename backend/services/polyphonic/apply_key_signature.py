# backend/services/polyphonic/apply_key_signature.py

import pretty_midi

# Mapping note names to MIDI key numbers
NOTE_TO_NUM = {
    "C": 0,
    "C#": 1,
    "D": 2,
    "D#": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "G": 7,
    "G#": 8,
    "A": 9,
    "A#": 10,
    "B": 11
}


def apply_key_to_midi(input_midi_path: str, key: str, mode: str, output_path: str):
    """
    Apply key signature meta event to a MIDI file.

    Parameters
    ----------
    input_midi_path : str
        Path to the input MIDI file
    key : str
        Root note (C, C#, D, etc.)
    mode : str
        'major' or 'minor'
    output_path : str
        Path where the updated MIDI will be saved
    """

    print(f"\n[KEY] Applying key signature: {key} {mode}")

    # Load MIDI
    midi = pretty_midi.PrettyMIDI(input_midi_path)

    # Convert note name to number
    base_key_number = NOTE_TO_NUM.get(key, 0)

    # Encode major/minor inside key_number
    if mode.lower() == "minor":
        key_number = base_key_number + 12
    else:
        key_number = base_key_number

    # Create key signature event
    key_signature = pretty_midi.KeySignature(
        key_number=key_number,
        time=0.0
    )

    # Add to MIDI
    midi.key_signature_changes.append(key_signature)

    # Save file
    midi.write(output_path)

    print(f"[KEY] ✓ Key signature applied and saved: {output_path}")

    return output_path