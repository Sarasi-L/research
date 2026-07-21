import os
import numpy as np

from music21 import converter

from services.monophonic.run_monophonic_pipeline import run_monophonic_pipeline
from services.monophonic.note_segmentation import frames_to_notes, smooth_note_durations
from services.monophonic.note_quantization import quantize_notes
from services.monophonic.note_naming import apply_key_aware_naming
from services.monophonic.key_detection import detect_key
from services.monophonic.tempo_beat_estimation import estimate_tempo_and_beats
from services.monophonic.note_based_tempo import estimate_tempo_from_notes
from services.monophonic.tempo_selector import select_final_tempo

from services.monophonic.western_notation.measure_grouping import group_notes_into_measures
from services.monophonic.western_notation.ties_rests import apply_ties_and_rests
from services.monophonic.western_notation.musicxml_export import generate_musicxml


# ---------------- PATHS ----------------
BASE_FOLDER = r"D:\My Documents\SLIIT\DS4.1\Research Project\multi_notation_generator_\Essen Folksong Database"

AUDIO_FOLDER = os.path.join(BASE_FOLDER, "audio_output")
OUTPUT_MIDI_FOLDER = os.path.join(BASE_FOLDER, "generated_midis")

os.makedirs(OUTPUT_MIDI_FOLDER, exist_ok=True)


# ---------------- HELPER ----------------
def xml_to_midi(xml_path, midi_path):
    score = converter.parse(xml_path)
    score.write("midi", fp=midi_path)


# ---------------- PIPELINE ----------------
def process_audio(audio_path, output_midi_path):

    print(f"🎵 Processing: {os.path.basename(audio_path)}")

    # ---------- PIPELINE ----------
    pitch_result = run_monophonic_pipeline(audio_path, "voice")

    times = [p["time"] for p in pitch_result["pitch_points"]]
    freqs = [p["frequency"] for p in pitch_result["pitch_points"]]
    confs = [p["confidence"] for p in pitch_result["pitch_points"]]

    notes = frames_to_notes(times, freqs, confs)
    notes = smooth_note_durations(notes)

    audio_tempo = estimate_tempo_and_beats(audio_path)
    note_tempo = estimate_tempo_from_notes(notes)
    tempo = select_final_tempo(audio_tempo, note_tempo)

    quantized = quantize_notes(notes, tempo["tempo"])

    key = detect_key(quantized)
    if key is None:
        key = {"key": "C", "mode": "major"}

    named = apply_key_aware_naming(quantized, f"{key['key']} {key['mode']}")

    measures = group_notes_into_measures(named, 4)
    measures = apply_ties_and_rests(measures, 4)

    xml_path = output_midi_path.replace(".mid", ".musicxml")

    generate_musicxml(
        western_measures=measures,
        tempo_bpm=tempo["tempo"],
        key_name=f"{key['key']} {key['mode']}",
        beats_per_measure=4,
        output_file=xml_path
    )

    # ---------- XML → MIDI ----------
    xml_to_midi(xml_path, output_midi_path)

    print(f"✅ Saved MIDI: {output_midi_path}")


# ---------------- MAIN LOOP ----------------
wav_files = [f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".wav")]

print(f"🎧 Total WAV files found: {len(wav_files)}")

success = 0
failed = 0

for file in wav_files:

    try:
        name = os.path.splitext(file)[0]

        audio_path = os.path.join(AUDIO_FOLDER, file)
        output_midi_path = os.path.join(OUTPUT_MIDI_FOLDER, name + ".mid")

        process_audio(audio_path, output_midi_path)

        success += 1

    except Exception as e:
        print(f"❌ Failed on {file}: {str(e)}")
        failed += 1


# ---------------- SUMMARY ----------------
print("\n================ SUMMARY ================")
print(f"Total files  : {len(wav_files)}")
print(f"Successful   : {success}")
print(f"Failed       : {failed}")
print("Output folder:", OUTPUT_MIDI_FOLDER)