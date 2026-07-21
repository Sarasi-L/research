# backend/services/polyphonic/merge_midi.py

from pathlib import Path
import pretty_midi

def merge_midi_tracks(midi_files: dict, output_path: str):
    
    print("\n[MERGE] ===== Merging Quantized MIDI Tracks =====")

    merged_midi = pretty_midi.PrettyMIDI()

    instrument_map = {
        "vocals": 53,   
        "bass": 33,     
        "other": 0,     
    }

    for name, midi_path in midi_files.items():
        print(f"[MERGE] Adding {name} track...")

        stem_midi = pretty_midi.PrettyMIDI(midi_path)

        for inst in stem_midi.instruments:
            if name == "drums":
                inst.is_drum = True
            else:
                inst.is_drum = False
                inst.program = instrument_map.get(name, 0)

            merged_midi.instruments.append(inst)

        print(f"[MERGE] ✓ Added {name}")

    output_path = Path(output_path)
    merged_midi.write(str(output_path))

    print(f"[MERGE] 🎵 Final quantized MIDI saved: {output_path}")

    return str(output_path)