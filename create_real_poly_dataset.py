#create_real_poly_dataset.py
# -*- coding: utf-8 -*-
"""
Polyphonic Dataset Creator – 21k samples with RMS check and proper NSynth mixes
Combines real polyphonic audio + synthetic NSynth mixes
with exact bias-controlled proportions.
"""

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
TOTAL_SAMPLES = 22000

SPLITS = {
    "train": 15400,
    "val": 3300,
    "test": 3300
}

SYNTH_PERCENT = 0.05   # 5% synthetic NSynth mixes
IRMAS_PERCENT = 0.50   # 50% from IRMAS
OTHER_REAL_PERCENT = 0.45 # 45% from other datasets

DATA_ROOT = Path(r"D:\My Documents\SLIIT\DS4.1\Research Project\data")
REAL_DATASETS = {
    "irmas": DATA_ROOT / "IRMAS",
    "openmic": DATA_ROOT / "openmic",
    "urmp": DATA_ROOT / "URMP",
    "fma": DATA_ROOT / "fma_small",
    "mir1k": DATA_ROOT / "MIR-1K"
}
NSYNTH_PATH = DATA_ROOT / "nsynth"

OUT_BASE = DATA_ROOT / "poly_dataset"
META_DIR = OUT_BASE / "metadata"

# ==========================
# CREATE OUTPUT FOLDERS
# ==========================
for split in SPLITS:
    (OUT_BASE / split / "poly").mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

# ==========================
# UTILITY FUNCTIONS
# ==========================
def find_audio_files(path):
    """Recursively find all audio files (wav, mp3, flac)"""
    if not path.exists():
        print(f"WARNING: Path does not exist: {path}")
        return []
    exts = ['*.wav','*.WAV','*.mp3','*.MP3','*.flac','*.FLAC']
    files = []
    for ext in exts:
        files.extend(list(path.rglob(ext)))
    return files

def window_audio(y):
    win = int(SR * WINDOW_SEC)
    hop = int(SR * HOP_SEC)
    windows = []
    for i in range(0, len(y) - win + 1, hop):
        w = y[i:i+win]
        # Skip silent windows
        if np.mean(w**2) < 1e-5:
            continue
        windows.append(w)
    return windows

def save_audio(w, path):
    sf.write(path, w, SR)

def process_files(files, split, prefix, target_count):
    out_dir = OUT_BASE / split / "poly"
    sample_idx = 0
    file_idx = 0
    
    while sample_idx < target_count and file_idx < len(files):
        try:
            wav = files[file_idx]
            y, _ = librosa.load(wav, sr=SR, mono=False)
            if y.ndim > 1:
                y = np.mean(y, axis=0)
            
            if len(y) < int(SR * WINDOW_SEC):
                file_idx += 1
                continue
            
            windows = window_audio(y)
            for w in windows:
                if sample_idx >= target_count:
                    break
                fname = f"{prefix}_{split}_{sample_idx:05d}.wav"
                save_audio(w, out_dir / fname)
                sample_idx += 1
        except Exception as e:
            print(f"Error processing {files[file_idx]}: {e}")
        file_idx += 1
    print(f"  Generated {sample_idx} samples from {prefix} for {split}")
    return sample_idx

# ==========================
# STEP 1 — Prepare real polyphonic files recursively
# ==========================
print("Searching for audio files...")
real_files = {}
for name, path in REAL_DATASETS.items():
    files = find_audio_files(path)
    random.shuffle(files)
    real_files[name] = files
    print(f"{name}: {len(files)} files found recursively")

# ==========================
# STEP 2 — Calculate number of samples per category
# ==========================
def calc_split_counts(total, percent):
    return int(total * percent)

split_counts = {}
for split, total in SPLITS.items():
    split_counts[split] = {
        "synth": calc_split_counts(total, SYNTH_PERCENT),
        "irmas": calc_split_counts(total, IRMAS_PERCENT),
        "other_real": calc_split_counts(total, OTHER_REAL_PERCENT)
    }
    print(f"{split}: synth={split_counts[split]['synth']}, irmas={split_counts[split]['irmas']}, other={split_counts[split]['other_real']}")

# ==========================
# STEP 3 — Process real poly datasets
# ==========================
print("\nProcessing real polyphonic files...")
for split in SPLITS:
    print(f"\n{split.upper()} split:")
    
    # IRMAS - 50%
    target_irmas = split_counts[split]["irmas"]
    if len(real_files["irmas"]) > 0:
        process_files(real_files["irmas"], split, "irmas", target_irmas)
    else:
        print(f"  WARNING: No IRMAS files available!")
    
    # Other real datasets combined - 45%
    target_other = split_counts[split]["other_real"]
    other_files = []
    for key in ["openmic", "urmp", "fma", "mir1k"]:
        other_files.extend(real_files[key])
    
    if len(other_files) > 0:
        random.shuffle(other_files)
        process_files(other_files, split, "real", target_other)
    else:
        print(f"  WARNING: No other real files available!")

print("\n✓ Real polyphonic files processed.")

# ==========================
# STEP 4 — Generate synthetic NSynth mixes
# ==========================
print("\nGenerating synthetic NSynth mixes...")
nsynth_files = find_audio_files(NSYNTH_PATH)
if len(nsynth_files) == 0:
    print("WARNING: No NSynth files found!")
else:
    print(f"Found {len(nsynth_files)} NSynth files")
    random.shuffle(nsynth_files)
    
    def generate_synthetic(split, count):
        out_dir = OUT_BASE / split / "poly"
        sample_idx = 0
        while sample_idx < count:
            try:
                selected = random.sample(nsynth_files, 2)
                y_mix = []
                max_len = 0
                for s in selected:
                    y, _ = librosa.load(s, sr=SR, mono=True)
                    y_mix.append(y)
                    max_len = max(max_len, len(y))
                
                # Pad and mix
                mixed = np.zeros(max_len)
                for y in y_mix:
                    if len(y) < max_len:
                        y = np.pad(y, (0, max_len-len(y)))
                    mixed += y
                if np.max(np.abs(mixed)) > 0:
                    mixed = mixed / np.max(np.abs(mixed))  # normalize
                
                # Windowing
                windows = window_audio(mixed)
                for w in windows:
                    if sample_idx >= count:
                        break
                    fname = f"synth_{split}_{sample_idx:05d}.wav"
                    save_audio(w, out_dir / fname)
                    sample_idx += 1
                
            except Exception as e:
                print(f"Error generating synthetic mix: {e}")
                break
        print(f"  Generated {sample_idx} synthetic samples for {split}")
    
    for split in SPLITS:
        generate_synthetic(split, split_counts[split]["synth"])

print("\n✓ Synthetic NSynth mixes generated.")

# ==========================
# STEP 5 — Create metadata CSV
# ==========================
print("\nCreating metadata CSV...")
rows = []
for split in SPLITS:
    poly_dir = OUT_BASE / split / "poly"
    if poly_dir.exists():
        for f in sorted(poly_dir.glob("*.wav")):
            source = "irmas" if f.name.startswith("irmas") else \
                    "nsynth_mix" if f.name.startswith("synth") else "real_poly"
            rows.append([f.name, "poly", source, split, WINDOW_SEC])

csv_path = META_DIR / "poly_labels_21k.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "label", "source", "split", "duration"])
    writer.writerows(rows)

print(f"\n✓ Polyphonic metadata CSV created at: {csv_path}")
print(f"✓ Total samples created: {len(rows)}")
for split in SPLITS:
    count = len([r for r in rows if r[3] == split])
    print(f"  {split}: {count} samples")
