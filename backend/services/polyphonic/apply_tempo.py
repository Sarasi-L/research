# backend/services/polyphonic/apply_tempo.py

import pretty_midi
import numpy as np

def apply_tempo(midi_path, tempo, output_path):
    
    print(f"\n[TEMPO] Applying tempo: {tempo:.2f} BPM")

    
    original = pretty_midi.PrettyMIDI(midi_path)

    
    new_midi = pretty_midi.PrettyMIDI(initial_tempo=float(tempo))

   
    new_midi.instruments = original.instruments

    
    new_midi.time_signature_changes = original.time_signature_changes

    
    new_midi.key_signature_changes = original.key_signature_changes

    new_midi.write(output_path)

   
    verify = pretty_midi.PrettyMIDI(output_path)
    _, tempos = verify.get_tempo_changes()
    written_bpm = float(tempos[0]) if len(tempos) > 0 else 0.0
    print(f"[TEMPO] ✓ Verified written BPM: {written_bpm:.2f}")

    return output_path