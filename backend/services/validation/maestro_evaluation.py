import pretty_midi
import mir_eval
import numpy as np
from pathlib import Path

from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH


# ============================================================
# 1️⃣ MIDI → note arrays
# ============================================================
def midi_to_note_arrays(midi_path):
    midi = pretty_midi.PrettyMIDI(midi_path)

    intervals = []
    pitches = []

    for instrument in midi.instruments:
        for note in instrument.notes:
            intervals.append([note.start, note.end])
            pitches.append(note.pitch)

    return np.array(intervals), np.array(pitches)


# ============================================================
# 2️⃣ Evaluate one MIDI pair
# ============================================================
def evaluate_pair(reference_midi, estimated_midi):

    ref_intervals, ref_pitches = midi_to_note_arrays(reference_midi)
    est_intervals, est_pitches = midi_to_note_arrays(estimated_midi)

    if len(ref_intervals) == 0 or len(est_intervals) == 0:
        print("Skipping empty note file.")
        return None

    precision, recall, f1, overlap = mir_eval.transcription.precision_recall_f1_overlap(
        ref_intervals,
        ref_pitches,
        est_intervals,
        est_pitches,
        onset_tolerance=0.05
    )

    return precision, recall, f1


# ============================================================
# 3️⃣ BasicPitch Transcription
# ============================================================
def transcribe_wav_to_midi(wav_path, output_folder):

    output_folder.mkdir(parents=True, exist_ok=True)

    predict_and_save(
        audio_path_list=[wav_path],
        output_directory=str(output_folder),
        save_midi=True,
        sonify_midi=False,
        save_model_outputs=False,
        save_notes=False,
        model_or_model_path=ICASSP_2022_MODEL_PATH
    )

    # BasicPitch automatically saves as *_basic_pitch.mid
    generated_file = output_folder / (Path(wav_path).stem + "_basic_pitch.mid")

    return generated_file


# ============================================================
# 4️⃣ FULL DATASET EVALUATION
# ============================================================
def evaluate_dataset(dataset_root):

    dataset_root = Path(dataset_root).resolve()
    estimated_folder = dataset_root / "estimated_midis"
    estimated_folder.mkdir(parents=True, exist_ok=True)

    all_precisions = []
    all_recalls = []
    all_f1s = []

    print("\n========== MAESTRO DATASET EVALUATION ==========")

    for item in dataset_root.iterdir():

        if not item.is_dir():
            continue

        if item.name == "estimated_midis":
            continue

        print(f"\nProcessing folder: {item.name}")

        # Find mp3 inside folder
        mp3_files = list(item.glob("*.mp3"))

        if len(mp3_files) == 0:
            print("No mp3 file found.")
            continue

        wav_path = mp3_files[0]

        # Find reference MIDI in root
        midi_name = item.name.replace(".mp3", ".mid")
        reference_midi = dataset_root / midi_name

        if not reference_midi.exists():
            print("Matching MIDI not found in root.")
            continue

        # Transcribe
        estimated_midi = transcribe_wav_to_midi(wav_path, estimated_folder)

        if not estimated_midi.exists():
            print("Estimated MIDI not created.")
            continue

        # Evaluate
        result = evaluate_pair(reference_midi, estimated_midi)

        if result is None:
            continue

        precision, recall, f1 = result

        print(f"Precision: {precision:.3f}")
        print(f"Recall   : {recall:.3f}")
        print(f"F1 Score : {f1:.3f}")

        all_precisions.append(precision)
        all_recalls.append(recall)
        all_f1s.append(f1)

    print("\n========== FINAL RESULTS ==========")
    print(f"Songs evaluated: {len(all_f1s)}")

    if len(all_f1s) > 0:
        print(f"Average Precision: {np.mean(all_precisions):.3f}")
        print(f"Average Recall   : {np.mean(all_recalls):.3f}")
        print(f"Average F1 Score : {np.mean(all_f1s):.3f}")
    else:
        print("No valid songs evaluated.")


# ============================================================
# 5️⃣ RUN
# ============================================================
if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parents[3]
    dataset_root = BASE_DIR / "dataset_maestro"

    evaluate_dataset(dataset_root)