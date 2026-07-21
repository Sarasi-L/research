#create_nsynth_mono_with_mir1k

import librosa
import numpy as np
import soundfile as sf
from pathlib import Path
import random
import csv

# ==========================
# CONFIGURATION
# ==========================
SR = 16000
WINDOW_SEC = 3.0
HOP_SEC = 1.5

NSYNTH_TARGET = 21000
MIR1K_TARGET  = 1000

MIR1K_SPLIT = {
    "train": 700,
    "val": 150,
    "test": 150
}

RAW_NSYNTH = Path(r"D:\My Documents\SLIIT\DS4.1\Research Project\data\nsynth")
RAW_MIR1K  = Path(r"D:\My Documents\SLIIT\DS4.1\Research Project\data\MIR-1K\LyricsWav")

OUT_BASE = Path(r"D:\My Documents\SLIIT\DS4.1\Research Project\data\mono_dataset")
META_DIR = OUT_BASE / "metadata"

CATEGORIES = [
    "bass_acoustic", "bass_electronic", "bass_synthetic",
    "brass_acoustic",
    "flute_acoustic", "flute_electronic", "flute_synthetic",
    "guitar_acoustic", "guitar_electronic", "guitar_synthetic",
    "keyboard_acoustic", "keyboard_electronic", "keyboard_synthetic",
    "mallet_acoustic", "mallet_electronic", "mallet_synthetic",
    "organ_electronic",
    "reed_acoustic",
    "string_acoustic",
    "synth_lead_synthetic",
    "vocal_acoustic", "vocal_electronic", "vocal_synthetic"
]

# ==========================
# UTILITIES
# ==========================
def window_audio(y):
    win = int(SR * WINDOW_SEC)
    hop = int(SR * HOP_SEC)
    return [y[i:i+win] for i in range(0, len(y)-win, hop)]

# ==========================
# CREATE FOLDERS
# ==========================
for split in ["train", "val", "test"]:
    (OUT_BASE / split / "mono").mkdir(parents=True, exist_ok=True)

META_DIR.mkdir(parents=True, exist_ok=True)

# ==========================
# NSYNTH MONO GENERATION (FIXED)
# ==========================
print("Generating NSynth mono samples...")

all_nsynth = list(RAW_NSYNTH.glob("*.wav"))
random.shuffle(all_nsynth)

nsynth_files = []
sample_id = 0

for wav in all_nsynth:
    if sample_id >= NSYNTH_TARGET:
        break

    y, _ = librosa.load(wav, sr=SR, mono=True)

    for w in window_audio(y):
        if sample_id >= NSYNTH_TARGET:
            break

        fname = f"nsynth_{sample_id:05d}.wav"
        sf.write(OUT_BASE / "train" / "mono" / fname, w, SR)
        nsynth_files.append(fname)
        sample_id += 1

print(f"NSynth generated: {len(nsynth_files)} samples")

# ==========================
# MIR-1K MONO ADDITION (UNCHANGED)
# ==========================
print("Adding MIR-1K mono vocal samples...")

mir_wavs = list(RAW_MIR1K.glob("*.wav"))
random.shuffle(mir_wavs)

mir_counts = {"train": 0, "val": 0, "test": 0}

for wav in mir_wavs:
    y, _ = librosa.load(wav, sr=SR, mono=True)
    windows = window_audio(y)
    random.shuffle(windows)

    for w in windows:
        for split in ["train", "val", "test"]:
            if mir_counts[split] < MIR1K_SPLIT[split]:
                fname = f"mir1k_vocal_{split}_{mir_counts[split]:04d}.wav"
                sf.write(OUT_BASE / split / "mono" / fname, w, SR)
                mir_counts[split] += 1
                break

        if sum(mir_counts.values()) >= MIR1K_TARGET:
            break

    if sum(mir_counts.values()) >= MIR1K_TARGET:
        break

print("MIR-1K distribution:", mir_counts)

# ==========================
# TRAIN / VAL / TEST SPLIT (NSYNTH)
# ==========================
random.shuffle(nsynth_files)

train = nsynth_files[:14700]
val   = nsynth_files[14700:17850]
test  = nsynth_files[17850:21000]

def move(files, split):
    for f in files:
        src = OUT_BASE / "train" / "mono" / f
        dst = OUT_BASE / split / "mono" / f
        src.rename(dst)

move(val, "val")
move(test, "test")

# ==========================
# METADATA CSV
# ==========================
rows = []

for split in ["train", "val", "test"]:
    for f in (OUT_BASE / split / "mono").glob("*.wav"):
        source = "mir1k" if f.name.startswith("mir1k") else "nsynth"
        rows.append([f.name, "mono", source, split, WINDOW_SEC])

with open(META_DIR / "mono_labels.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "label", "source", "split", "duration"])
    writer.writerows(rows)

print("Metadata written successfully.")
