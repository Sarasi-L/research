# backend/services/polyphonic/midi_note_filter.py

import pretty_midi


MIN_VELOCITY = 20
MIN_DURATION = 0.12   # seconds
MAX_DURATION = 3.0


def filter_midi_notes(input_midi, output_midi):

    print("\n[FILTER] ===== MIDI Noise Filtering =====")

    midi = pretty_midi.PrettyMIDI(input_midi)

    removed_short = 0
    removed_velocity = 0
    trimmed_long = 0

    for inst in midi.instruments:

        filtered_notes = []

        for note in inst.notes:

            duration = note.end - note.start

            # Remove low velocity noise
            if note.velocity < MIN_VELOCITY:
                removed_velocity += 1
                continue

            # Remove extremely short notes
            if duration < MIN_DURATION:
                removed_short += 1
                continue

            # Trim extremely long notes
            if duration > MAX_DURATION:
                note.end = note.start + MAX_DURATION
                trimmed_long += 1

            filtered_notes.append(note)

        inst.notes = filtered_notes

    midi.write(output_midi)

    print(f"[FILTER] Removed low velocity notes: {removed_velocity}")
    print(f"[FILTER] Removed short notes: {removed_short}")
    print(f"[FILTER] Trimmed long notes: {trimmed_long}")
    print(f"[FILTER] ✓ Filtered MIDI saved: {output_midi}")

    return output_midi