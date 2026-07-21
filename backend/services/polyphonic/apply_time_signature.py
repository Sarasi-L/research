# backend/services/polyphonic/apply_time_signature.py

import pretty_midi

def apply_time_signature(midi_path: str, numerator: int, denominator: int, output_path: str):
   
    midi = pretty_midi.PrettyMIDI(midi_path)

    ts = pretty_midi.TimeSignature(numerator=numerator,
                                   denominator=denominator,
                                   time=0.0)

    midi.time_signature_changes.append(ts)
    midi.write(output_path)

    print(f"[TIME] ✓ Time Signature {numerator}/{denominator} added → {output_path}")
    return output_path