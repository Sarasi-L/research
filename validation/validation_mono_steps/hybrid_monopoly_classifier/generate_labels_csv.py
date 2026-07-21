import csv
from pathlib import Path
from collections import Counter

# validation/hybrid_monopoly_classifier/dataset/test
BASE_DIR = Path(__file__).resolve().parent
DATASET_ROOT = BASE_DIR / "dataset" / "test"

OUTPUT_CSV = DATASET_ROOT / "labels.csv"

CLASSES = {
    "mono": "mono",
    "poly": "poly",
    "ambiguous": "ambiguous"
}

AUDIO_EXTS = (".wav", ".mp3", ".flac")

rows = []

for folder_name, label in CLASSES.items():
    folder = DATASET_ROOT / folder_name

    if not folder.exists():
        print(f"[WARNING] Folder not found: {folder}")
        continue

    for audio_file in sorted(folder.iterdir()):
        if audio_file.suffix.lower() in AUDIO_EXTS:
            rows.append([
                audio_file.name,
                label
            ])

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "label"])
    writer.writerows(rows)

print(" labels.csv created successfully")
print(f" Location: {OUTPUT_CSV}")
print(f" Total samples: {len(rows)}")

counts = Counter([r[1] for r in rows])
print(" Class distribution:")
for cls, count in counts.items():
    print(f"  {cls}: {count}")
