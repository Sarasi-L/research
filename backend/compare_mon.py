import csv
import numpy as np
import pretty_midi
from pathlib import Path




BASE = Path(r"D:\My Documents\SLIIT\DS4.1\Research Project\multi_notation_generator_\Essen Folksong Database")

GT_MIDI_DIR = BASE
GEN_MIDI_DIR = BASE / "generated_midis"

OUTPUT_CSV = BASE / "evaluation_results.csv"




ONSET_TOL = 0.05
OFFSET_TOL = 0.07




def load_notes(midi_path):

    midi = pretty_midi.PrettyMIDI(str(midi_path))

    notes = []

    for inst in midi.instruments:

        if inst.is_drum:
            continue

        for n in inst.notes:
            notes.append((n.start, n.end, n.pitch))

    return sorted(notes, key=lambda x: (x[0], x[2]))




def evaluate(gt_path, pred_path):

    gt = load_notes(gt_path)
    pred = load_notes(pred_path)

    if len(gt) == 0 or len(pred) == 0:
        return 0, 0, 0

    used = set()
    tp = 0

    for g_on, g_off, g_pitch in gt:

        for i, (p_on, p_off, p_pitch) in enumerate(pred):

            if i in used:
                continue

            # MATCH CONDITION (monophonic-friendly)
            if (
                g_pitch == p_pitch and
                abs(g_on - p_on) <= ONSET_TOL
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

    gen_files = list(GEN_MIDI_DIR.glob("*.mid"))

    results = []

    print(f"\n Generated files: {len(gen_files)}")

    for gen_file in gen_files:

        name = gen_file.stem
        gt_file = GT_MIDI_DIR / f"{name}.mid"

        print(f"\n Evaluating: {name}")

        if not gt_file.exists():
            print(" Missing GT:", gt_file)
            continue

        try:
            p, r, f1 = evaluate(gt_file, gen_file)

            print(f" Precision: {p:.3f}")
            print(f" Recall:    {r:.3f}")
            print(f" F1 Score:  {f1:.3f}")

            results.append({
                "song": name,
                "precision": p,
                "recall": r,
                "f1": f1
            })

        except Exception as e:
            print(f" Error: {e}")




    if len(results) > 0:

        with open(OUTPUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)



        avg_p = np.mean([r["precision"] for r in results])
        avg_r = np.mean([r["recall"] for r in results])
        avg_f = np.mean([r["f1"] for r in results])

        print("\n================ FINAL RESULTS ================")
        print(f"Songs evaluated: {len(results)}")
        print(f"Precision: {avg_p:.3f}")
        print(f"Recall:    {avg_r:.3f}")
        print(f"F1 Score:  {avg_f:.3f}")

        print("\n Saved to:", OUTPUT_CSV)

    else:
        print(" No valid comparisons found.")


# ============================================================

if __name__ == "__main__":
    run()