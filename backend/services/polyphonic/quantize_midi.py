# backend/services/polyphonic/quantize_midi.py

import pretty_midi
import numpy as np
from pathlib import Path

def find_nearest(time, beat_times):
    """Return nearest beat time from beat grid."""
    idx = np.argmin(np.abs(beat_times - time))
    return float(beat_times[idx])

def quantize_midi(input_midi_path: str, beat_times, output_path: str):
    """
    Quantize all note on/off events to nearest beat.
    Saves quantized MIDI.
    """
    print(f"\n[Q] ===== Quantizing: {input_midi_path} =====")

    midi = pretty_midi.PrettyMIDI(input_midi_path)

    for instrument in midi.instruments:
        for note in instrument.notes:
            note.start = find_nearest(note.start, beat_times)
            note.end = find_nearest(note.end, beat_times)

            # Ensure end > start
            if note.end <= note.start:
                note.end = note.start + 0.1

    output_path = Path(output_path)
    midi.write(str(output_path))

    print(f"[Q] ✓ Quantized MIDI saved to: {output_path}")
    return str(output_path)