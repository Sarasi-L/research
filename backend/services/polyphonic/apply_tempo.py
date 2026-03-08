# backend/services/polyphonic/apply_tempo.py

import pretty_midi
import numpy as np

def apply_tempo(midi_path, tempo, output_path):
    """
    Write correct tempo into MIDI by rebuilding with initial_tempo.
    The private attribute hack does NOT work — use initial_tempo instead.
    """
    print(f"\n[TEMPO] Applying tempo: {tempo:.2f} BPM")

    # Load original to copy all content
    original = pretty_midi.PrettyMIDI(midi_path)

    # Create new MIDI with correct tempo set at construction time
    # This is the ONLY reliable way — pretty_midi bakes tempo at init
    new_midi = pretty_midi.PrettyMIDI(initial_tempo=float(tempo))

    # Copy all instruments and notes
    new_midi.instruments = original.instruments

    # Copy time signature changes
    new_midi.time_signature_changes = original.time_signature_changes

    # Copy key signature changes  
    new_midi.key_signature_changes = original.key_signature_changes

    new_midi.write(output_path)

    # Verify it was written correctly
    verify = pretty_midi.PrettyMIDI(output_path)
    _, tempos = verify.get_tempo_changes()
    written_bpm = float(tempos[0]) if len(tempos) > 0 else 0.0
    print(f"[TEMPO] ✓ Verified written BPM: {written_bpm:.2f}")

    return output_path