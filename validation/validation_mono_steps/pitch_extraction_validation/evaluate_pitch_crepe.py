import librosa
import numpy as np
import math
import os
from pathlib import Path
from backend.services.monophonic.pitch_extraction import extract_pitch

# -------------------------------
# CONFIG
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent
NSYNTH_DIR = BASE_DIR / "dataset"

SR = 22050
CONF_THRESH = 0.5

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def hz_to_midi(freq):
    return int(round(69 + 12 * math.log2(freq / 440.0)))

def estimate_gt_pitch(freq):
    """Median pitch = pseudo ground truth (NSynth single note)"""
    valid = freq[~np.isnan(freq)]
    if len(valid) == 0:
        return None
    return np.median(valid)

def cent_error(pred, gt):
    return 1200 * np.log2(pred / gt)

# -------------------------------
# EVALUATION
# -------------------------------
def evaluate_file(audio_path):
    y, sr = librosa.load(audio_path, sr=SR, mono=True)

    time, freq, conf = extract_pitch(y, sr)

    # Apply same confidence filter as pipeline
    valid_idx = (conf >= CONF_THRESH) & (~np.isnan(freq))
    freq = freq[valid_idx]

    if len(freq) == 0:
        return None

    gt_pitch = estimate_gt_pitch(freq)
    if gt_pitch is None:
        return None

    rpa_correct = 0
    rca_correct = 0
    total = 0

    for f in freq:
        if f <= 0:
            continue

        cent = abs(cent_error(f, gt_pitch))

        # RPA (±50 cents)
        if cent <= 50:
            rpa_correct += 1

        # RCA (pitch class only)
        if hz_to_midi(f) % 12 == hz_to_midi(gt_pitch) % 12:
            rca_correct += 1

        total += 1

    if total == 0:
        return None

    return {
        "RPA": rpa_correct / total,
        "RCA": rca_correct / total,
        "OA":  rpa_correct / total   # monophonic voiced audio
    }

# -------------------------------
# RUN ALL FILES
# -------------------------------
def main():
    results = []

    for file in os.listdir(NSYNTH_DIR):
        if not file.endswith(".wav"):
            continue

        path = os.path.join(NSYNTH_DIR, file)
        metrics = evaluate_file(path)

        if metrics:
            results.append(metrics)
            print(f"{file} -> RPA={metrics['RPA']:.3f}, RCA={metrics['RCA']:.3f}")

    if not results:
        print("No valid files evaluated.")
        return

    mean_rpa = np.mean([r["RPA"] for r in results])
    mean_rca = np.mean([r["RCA"] for r in results])
    mean_oa  = np.mean([r["OA"]  for r in results])

    print("\n===== FINAL CREPE PITCH EVALUATION =====")
    print(f"Files evaluated: {len(results)}")
    print(f"Mean RPA: {mean_rpa*100:.2f}%")
    print(f"Mean RCA: {mean_rca*100:.2f}%")
    print(f"Mean OA : {mean_oa*100:.2f}%")

if __name__ == "__main__":
    main()
