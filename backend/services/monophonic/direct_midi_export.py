import pretty_midi
import numpy as np


def create_midi_from_quantized_notes(
    notes,
    tempo_bpm,
    output_file
):
    """
    Generate MIDI directly from quantized notes (NO XML).

    Uses original timing (start/end) + quantized pitch.
    """

    midi = pretty_midi.PrettyMIDI()

    instrument = pretty_midi.Instrument(
        program=pretty_midi.instrument_name_to_program("Acoustic Grand Piano")
    )

    for n in notes:
        midi_pitch = n.get("midi")

        # Skip rests or invalid notes
        if midi_pitch is None:
            continue

        start = float(n["start"])
        end = float(n["end"])

        if end <= start:
            continue

        note = pretty_midi.Note(
            velocity=80,
            pitch=int(midi_pitch),
            start=start,
            end=end
        )

        instrument.notes.append(note)

    midi.instruments.append(instrument)

    # Set tempo
    midi._PrettyMIDI__initial_tempo = float(tempo_bpm)

    midi.write(output_file)

    return output_file