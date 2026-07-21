# validation/hybrid_monopoly_classifer/run_hybrid_eval.py

import csv
from pathlib import Path
from collections import defaultdict

from backend.services.hybrid_detect_type import detect_type  

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset" / "test"
LABELS_CSV = DATASET_DIR / "labels.csv"

OUTPUT_CSV = BASE_DIR / "predictions_hybrid.csv"

labels = {}
with open(LABELS_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        labels[row["filename"]] = row["label"]

results = []

for filename, true_label in labels.items():
    audio_path = (
        DATASET_DIR / true_label / filename
        if true_label != "ambiguous"
        else DATASET_DIR / "ambiguous" / filename
    )

    pred_label, confidence = detect_type(str(audio_path))

    results.append([
        filename,
        true_label,
        pred_label,
        round(confidence, 3)
    ])

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "filename",
        "true_label",
        "predicted_label",
        "confidence"
    ])
    writer.writerows(results)

print("Hybrid predictions saved:", OUTPUT_CSV)
