#backend/services/polyphonic/score_cleaner.py

import pretty_midi


def clean_midi_overlaps(midi_path, output_path):
    midi = pretty_midi.PrettyMIDI(midi_path)

    for inst in midi.instruments:
        inst.notes.sort(key=lambda x: (x.pitch, x.start))

        cleaned = []
        for note in inst.notes:
            if not cleaned:
                cleaned.append(note)
                continue

            last = cleaned[-1]

            if note.pitch == last.pitch and note.start < last.end:
                last.end = max(last.end, note.end)
            else:
                cleaned.append(note)

        inst.notes = cleaned

    midi.write(output_path)
    return output_path