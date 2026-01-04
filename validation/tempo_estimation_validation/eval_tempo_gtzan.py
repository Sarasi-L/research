import os
import pandas as pd
import numpy as np
from pathlib import Path

# -------------------------------------------------
# IMPORT YOUR TEMPO FUNCTION
# -------------------------------------------------
from backend.services.monophonic.tempo_beat_estimation import (
    estimate_tempo_and_beats
)

# -------------------------------------------------
# CONFIG (CHANGE ONLY IF NEEDED)
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

GTZAN_DIR = Path(
    r"D:\My Documents\SLIIT\DS4.1\Research Project\data\GTZAN"
)

GT_TEMPO_CSV = GTZAN_DIR / "features_30_sec.csv"

ALLOWED_GENRES = {
    "blues",
    "classical",
    "jazz",
    "country",
    "pop",
    "rock"
}

RESULTS_DIR = BASE_DIR / "validation" / "tempo_estimation_validation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def correct_tempo_octave(pred_tempo, gt_tempo):
    """
    Correct octave (double / half tempo) ambiguity
    by choosing the closest candidate to GT.
    """
    candidates = [
        pred_tempo,
        pred_tempo * 2,
        pred_tempo / 2
    ]
    return min(candidates, key=lambda x: abs(x - gt_tempo))


# BPM tolerances
TOL_4 = 4.0
TOL_8 = 8.0

# -------------------------------------------------
# LOAD GROUND-TRUTH TEMPO
# -------------------------------------------------
gt_df = pd.read_csv(GT_TEMPO_CSV)

# Map: filename -> tempo
gt_tempo_map = {
    row["filename"]: float(row["tempo"])
    for _, row in gt_df.iterrows()
}

# -------------------------------------------------
# EVALUATION
# -------------------------------------------------
results = []

print("\n===== GTZAN TEMPO EVALUATION =====\n")

for genre in sorted(ALLOWED_GENRES):
    genre_dir = GTZAN_DIR / genre

    if not genre_dir.exists():
        print(f"[WARN] Missing folder: {genre_dir}")
        continue

    print(f"[INFO] Processing genre: {genre}")

    for wav_path in sorted(genre_dir.glob("*.wav")):
        filename = wav_path.name

        if filename not in gt_tempo_map:
            print(f"[WARN] No GT tempo for {filename}")
            continue

        gt_tempo = gt_tempo_map[filename]

        try:
            tempo_data = estimate_tempo_and_beats(str(wav_path))
            raw_pred_tempo = float(tempo_data["tempo"])

            pred_tempo = correct_tempo_octave(raw_pred_tempo, gt_tempo)

            abs_error = abs(pred_tempo - gt_tempo)

            results.append({
                "filename": filename,
                "genre": genre,
                "gt_tempo": gt_tempo,
                "raw_pred_tempo": raw_pred_tempo,
                "corrected_pred_tempo": pred_tempo,
                "abs_error": abs_error,
                "correct_4bpm": abs_error <= TOL_4,
                "correct_8bpm": abs_error <= TOL_8
            })


            print(
                f"{filename:15s} | "
                f"GT={gt_tempo:6.1f} | "
                f"PRED={pred_tempo:6.1f} | "
                f"ERR={abs_error:5.1f}"
            )

        except Exception as e:
            print(f"[ERROR] {filename}: {e}")

# -------------------------------------------------
# AGGREGATE RESULTS
# -------------------------------------------------
df = pd.DataFrame(results)
df.to_csv(RESULTS_DIR / "tempo_results.csv", index=False)

mean_error = df["abs_error"].mean()
median_error = df["abs_error"].median()
acc_4 = df["correct_4bpm"].mean() * 100
acc_8 = df["correct_8bpm"].mean() * 100

print("\n===== FINAL RESULTS =====")
print(f"Tracks evaluated : {len(df)}")
print(f"Mean Abs Error   : {mean_error:.2f} BPM")
print(f"Median Abs Error : {median_error:.2f} BPM")
print(f"Accuracy ±4 BPM  : {acc_4:.2f}%")
print(f"Accuracy ±8 BPM  : {acc_8:.2f}%")

print(f"\nDetailed results saved to:")
print(RESULTS_DIR / "tempo_results.csv")
