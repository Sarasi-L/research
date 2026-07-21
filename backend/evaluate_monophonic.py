import csv
import numpy as np
import pretty_midi
from pathlib import Path



BASE = Path(r"D:\My Documents\SLIIT\DS4.1\Research Project\multi_notation_generator_\Essen Folksong Database")

GT_DIR = BASE
PRED_DIR = BASE / "generated_midis"

OUTPUT_CSV = BASE / "evaluation_results_direct.csv"



ONSET_TOL = 0.15
OFFSET_TOL = 0.20
PITCH_TOL = 1   # semitone tolerance



def load_notes(path):

    midi = pretty_midi.PrettyMIDI(str(path))
    notes = []

    for inst in midi.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            notes.append((n.start, n.end, n.pitch))

    return sorted(notes, key=lambda x: (x[0], x[2]))



def align_notes(gt, pred):

    if not gt or not pred:
        return pred

    shift = pred[0][0] - gt[0][0]

    aligned = []
    for s, e, p in pred:
        aligned.append((s - shift, e - shift, p))

    return aligned



def evaluate(gt_path, pred_path):

    gt = load_notes(gt_path)
    pred = load_notes(pred_path)

    pred = align_notes(gt, pred)

    if len(gt) == 0 or len(pred) == 0:
        return 0, 0, 0

    used = set()
    tp = 0

    for g_on, g_off, g_pitch in gt:

        for i, (p_on, p_off, p_pitch) in enumerate(pred):

            if i in used:
                continue

            if (
                abs(g_pitch - p_pitch) <= PITCH_TOL and
                abs(g_on - p_on) <= ONSET_TOL and
                abs(g_off - p_off) <= OFFSET_TOL
            ):
                tp += 1
                used.add(i)
                break

    precision = tp / len(pred)
    recall = tp / len(gt)

    f1 = 0
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)

    return precision, recall, f1



def run():

    pred_files = list(PRED_DIR.glob("*.mid"))

    results = []

    print(f"\n Files: {len(pred_files)}")

    for pred_file in pred_files:

        name = pred_file.stem
        gt_file = GT_DIR / f"{name}.mid"

        print(f"\n {name}")

        if not gt_file.exists():
            print(" Missing GT")
            continue

        try:
            p, r, f1 = evaluate(gt_file, pred_file)

            print(f"P: {p:.3f}  R: {r:.3f}  F1: {f1:.3f}")

            results.append({
                "song": name,
                "precision": p,
                "recall": r,
                "f1": f1
            })

        except Exception as e:
            print(" Error:", e)

    # ================= SAVE =================
    if results:

        with open(OUTPUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

        avg_p = np.mean([r["precision"] for r in results])
        avg_r = np.mean([r["recall"] for r in results])
        avg_f = np.mean([r["f1"] for r in results])

        print("\n=========== FINAL ===========")
        print(f"Precision: {avg_p:.3f}")
        print(f"Recall:    {avg_r:.3f}")
        print(f"F1 Score:  {avg_f:.3f}")

        print("Saved to:", OUTPUT_CSV)


if __name__ == "__main__":
    run()