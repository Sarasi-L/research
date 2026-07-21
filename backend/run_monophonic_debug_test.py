import os
from pathlib import Path

# ----------------------------
# IMPORT YOUR PIPELINE MODULES
# ----------------------------
from services.monophonic.preprocess_monophonic_audio import preprocess_audio
from services.monophonic.pitch_extraction import extract_pitch
from services.monophonic.note_segmentation import frames_to_notes, smooth_note_durations
from services.monophonic.note_quantization import quantize_notes
from services.monophonic.note_naming import apply_key_aware_naming
from services.monophonic.note_based_tempo import estimate_tempo_from_notes
from services.monophonic.key_detection import detect_key
from services.monophonic.western_notation.measure_grouping import group_notes_into_measures
from services.monophonic.western_notation.musicxml_export import generate_musicxml

from music21 import stream, note

import pretty_midi
import numpy as np


# ============================
# CONFIG
# ============================
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================
# STEP 1: AUDIO → PITCH
# ============================
def step_extract(audio_path):
    print("\n[STEP 1] Preprocessing audio...")
    y, sr = preprocess_audio(audio_path)

    print("[STEP 2] Extracting pitch (CREPE)...")
    time, freq, conf = extract_pitch(y, sr)

    return time, freq, conf


# ============================
# STEP 2: SEGMENT NOTES
# ============================
def step_segment(time, freq, conf):
    print("\n[STEP 3] Converting frames → notes...")
    raw_notes = frames_to_notes(time, freq, conf)

    print("[STEP 4] Smoothing notes...")
    smooth = smooth_note_durations(raw_notes)

    return smooth


# ============================
# STEP 3: QUANTIZE
# ============================
def step_quantize(notes, tempo):
    print("\n[STEP 5] Quantizing notes...")
    return quantize_notes(notes, tempo)


# ============================
# STEP 4: KEY + NAMING
# ============================
def step_key_and_name(notes, key_name):
    print("\n[STEP 6] Applying note naming...")
    return apply_key_aware_naming(notes, key_name)


# ============================
# STEP 5: TEMPO ESTIMATION
# ============================
def step_tempo(notes):
    print("\n[STEP 7] Estimating tempo...")
    tempo_info = estimate_tempo_from_notes(notes)
    print("Tempo detected:", tempo_info)
    return tempo_info


# ============================
# STEP 6: KEY DETECTION
# ============================
def step_key(notes):
    print("\n[STEP 8] Detecting key...")
    return detect_key(notes)


# ============================
# STEP 7: GROUP MEASURES
# ============================
def step_measures(notes, beats_per_measure=4):
    print("\n[STEP 9] Grouping into measures...")
    return group_notes_into_measures(notes, beats_per_measure)


# ============================
# STEP 8: MUSICXML
# ============================
def step_musicxml(measures, tempo, key_name, bpm, file_name):
    print("\n[STEP 10] Generating MusicXML...")
    path = os.path.join(OUTPUT_DIR, file_name)
    return generate_musicxml(measures, bpm, key_name, 4, path)


# ============================
# STEP 9: MIDI EXPORT
# ============================
def step_midi(measures, file_name):
    print("\n[STEP 11] Generating MIDI...")

    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    start_time = 0

    for measure in measures:
        for n in measure:

            dur = float(n.get("quantized_beats", 1.0))

            name = n.get("note_name")

            if name in ["Rest", None, "", "R"]:
                start_time += dur
                continue

            try:
                midi_note = pretty_midi.note_name_to_number(name)
            except:
                continue

            note_obj = pretty_midi.Note(
                velocity=100,
                pitch=midi_note,
                start=start_time,
                end=start_time + dur
            )

            instrument.notes.append(note_obj)
            start_time += dur

    midi.instruments.append(instrument)

    path = os.path.join(OUTPUT_DIR, file_name)
    midi.write(path)

    print("MIDI saved:", path)
    return path


# ============================
# STEP 10: SARGAM
# ============================
NOTE_TO_SARGAM = {
    "C": "Sa", "C#": "Re♭", "D": "Re", "D#": "Ga♭",
    "E": "Ga", "F": "Ma", "F#": "Ma#", "G": "Pa",
    "G#": "Dha♭", "A": "Dha", "A#": "Ni♭", "B": "Ni"
}

def step_sargam(notes, file_name):
    print("\n[STEP 12] Generating Sargam...")

    out = []

    for n in notes:
        name = n.get("note_name", "Rest")

        if name in ["Rest", None]:
            out.append("Rest")
            continue

        base = name[:-1] if name[-1].isdigit() else name
        out.append(NOTE_TO_SARGAM.get(base, base))

    path = os.path.join(OUTPUT_DIR, file_name)

    with open(path, "w", encoding="utf-8") as f:
        f.write(" ".join(out))

    print("Sargam saved:", path)
    return path


# ============================
# FULL PIPELINE RUNNER
# ============================
def run_pipeline(audio_path):

    print("\n==============================")
    print(" MONOPHONIC DEBUG PIPELINE")
    print("==============================")

    # 1. Pitch extraction
    time, freq, conf = step_extract(audio_path)

    # 2. Notes
    raw_notes = step_segment(time, freq, conf)

    # 3. Tempo
    tempo_info = step_tempo(raw_notes)
    tempo = tempo_info["tempo"] or 120

    # 4. Key
    key_info = step_key(raw_notes)
    key_name = key_info["key"]

    print("\nDetected Key:", key_info)

    # 5. Quantize
    quantized = step_quantize(raw_notes, tempo)

    # 6. Naming
    named = step_key_and_name(quantized, key_name)

    # 7. Measures
    measures = step_measures(named)

    # 8. MusicXML
    xml_path = step_musicxml(
        measures,
        tempo,
        key_name,
        tempo,
        "output.xml"
    )

    # 9. MIDI
    midi_path = step_midi(measures, "output.mid")

    # 10. Sargam
    sargam_path = step_sargam(named, "output_sargam.txt")

    # ============================
    print("\n==============================")
    print(" DONE")
    print("==============================")
    print("MIDI   :", midi_path)
    print("XML    :", xml_path)
    print("SARGAM :", sargam_path)


# ============================
# RUN FROM TERMINAL
# ============================
if __name__ == "__main__":

    audio_file = input("\nEnter path to audio file: ").strip()

    if not os.path.exists(audio_file):
        print("File not found!")
        exit()

    run_pipeline(audio_file)