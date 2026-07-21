# validation/ hybrid_monopoly_classifier/evaluate_crnn_results.py

import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PRED_CSV = BASE_DIR / "predictions_crnn.csv"

LABEL_MAP = {
    "monophonic": "mono",
    "polyphonic": "poly",
    "mono": "mono",
    "poly": "poly",
    "ambiguous": "ambiguous"
}

correct = 0
total = 0
ambiguous_conf = []

with open(PRED_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        
        true_label = LABEL_MAP[row["true_label"].strip()]
        pred_label = LABEL_MAP[row["predicted_label"].strip()]
        conf = float(row["confidence"])

        if true_label == "ambiguous":
            ambiguous_conf.append(conf)
            continue

        total += 1
        if true_label == pred_label:
            correct += 1


accuracy = (correct / total * 100) if total > 0 else 0.0

print("===== CRNN CLASSIFIER RESULTS =====")
print(f"Evaluated samples (mono + poly): {total}")
print(f"Correct predictions: {correct}")
print(f"Accuracy: {accuracy:.2f}%")

if ambiguous_conf:
    print("\n----- Ambiguous confidence -----")
    print(f"Mean confidence: {sum(ambiguous_conf)/len(ambiguous_conf):.3f}")
    print(f"Min confidence: {min(ambiguous_conf):.3f}")
    print(f"Max confidence: {max(ambiguous_conf):.3f}")
