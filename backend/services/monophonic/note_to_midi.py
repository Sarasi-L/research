import pretty_midi


def generate_midi_from_notes(notes, output_path, tempo=120):
    """
    Convert final processed notes directly into MIDI
    """

    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    instrument = pretty_midi.Instrument(program=0)  # piano

    for n in notes:
        pitch = n.get("pitch", 0)

        # skip invalid / rest
        if pitch is None or pitch <= 0:
            continue

        start = float(n["start"])
        end = float(n["end"])

        # safety check
        if end <= start:
            continue

        midi_note = pretty_midi.Note(
            velocity=100,
            pitch=int(round(pitch)),
            start=start,
            end=end
        )

        instrument.notes.append(midi_note)

    midi.instruments.append(instrument)
    midi.write(output_path)

    return output_path