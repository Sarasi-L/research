# backend/services/polyphonic/apply_key_signature.py

import pretty_midi

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
    Apply key signature meta event to MIDI.
    """

    print(f"\n[KEY] Applying key signature: {key} {mode}")

    midi = pretty_midi.PrettyMIDI(input_midi_path)

    base_key_number = NOTE_TO_NUM.get(key, 0)

    # 🔧 FIX: encode mode inside key_number
    if mode.lower() == "minor":
        key_number = base_key_number + 12
    else:
        key_number = base_key_number

    key_sig = pretty_midi.KeySignature(key_number, time=0.0)

    midi.key_signature_changes.append(key_sig)

    midi.write(output_path)

    print(f"[KEY] ✓ Key signature applied and saved: {output_path}")

    return output_path