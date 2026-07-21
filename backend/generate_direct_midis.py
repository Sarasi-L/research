import os
import numpy as np
import pretty_midi
from pathlib import Path

from services.monophonic.run_monophonic_pipeline import run_monophonic_pipeline
from services.monophonic.note_segmentation import frames_to_notes, smooth_note_durations
from services.monophonic.note_quantization import quantize_notes
from services.monophonic.note_naming import apply_key_aware_naming
from services.monophonic.key_detection import detect_key
from services.monophonic.tempo_beat_estimation import estimate_tempo_and_beats
from services.monophonic.note_based_tempo import estimate_tempo_from_notes
from services.monophonic.tempo_selector import select_final_tempo



BASE = Path(r"D:\My Documents\SLIIT\DS4.1\Research Project\multi_notation_generator_\Essen Folksong Database")

AUDIO_FOLDER = BASE / "audios"
OUTPUT_FOLDER = BASE / "generated_midis"

OUTPUT_FOLDER.mkdir(exist_ok=True)



def create_direct_midi(notes, tempo_bpm, output_path):

    midi = pretty_midi.PrettyMIDI()

    instrument = pretty_midi.Instrument(
        program=pretty_midi.instrument_name_to_program("Violin")  # better than piano
    )

    for n in notes:
        pitch = n.get("midi")

        if pitch is None:
            continue

        start = float(n["start"])
        end = float(n["end"])

        if end <= start:
            continue

        # small sustain improvement
        end = end + 0.02

        note = pretty_midi.Note(
            velocity=80,
            pitch=int(pitch),
            start=start,
            end=end
        )

        instrument.notes.append(note)

    midi.instruments.append(instrument)
    midi._PrettyMIDI__initial_tempo = float(tempo_bpm)

    midi.write(str(output_path))



def process_audio(audio_path, output_midi_path):

    print(f" Processing: {audio_path.name}")

    pitch_result = run_monophonic_pipeline(str(audio_path), "voice")

    times = [p["time"] for p in pitch_result["pitch_points"]]
    freqs = [p["frequency"] for p in pitch_result["pitch_points"]]
    confs = [p["confidence"] for p in pitch_result["pitch_points"]]

    notes = frames_to_notes(times, freqs, confs)
    notes = smooth_note_durations(notes)

    audio_tempo = estimate_tempo_and_beats(str(audio_path))
    note_tempo = estimate_tempo_from_notes(notes)
    tempo = select_final_tempo(audio_tempo, note_tempo)

    quantized = quantize_notes(notes, tempo["tempo"])

    key = detect_key(quantized)
    if key is None:
        key = {"key": "C", "mode": "major"}

    named = apply_key_aware_naming(quantized, f"{key['key']} {key['mode']}")


    create_direct_midi(named, tempo["tempo"], output_midi_path)

    print(f" Saved: {output_midi_path.name}")



def run():

    wav_files = list(AUDIO_FOLDER.glob("*.wav"))

    print(f" Total files: {len(wav_files)}")

    for wav in wav_files:

        try:
            output_path = OUTPUT_FOLDER / f"{wav.stem}.mid"
            process_audio(wav, output_path)

        except Exception as e:
            print(f" Failed: {wav.name} → {e}")


if __name__ == "__main__":
    run()