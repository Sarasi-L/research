# extract_logmel_features.py

import librosa
import numpy as np
from pathlib import Path
from tqdm import tqdm

# =========================
# CONFIG
# =========================
SR = 16000
N_FFT = 1024
HOP = 512
N_MELS = 128
WINDOW_SEC = 3.0

DATA_ROOT = Path(r"D:\My Documents\SLIIT\DS4.1\Research Project\data")

MONO_ROOT = DATA_ROOT / "mono_dataset"
POLY_ROOT = DATA_ROOT / "poly_dataset"

FEATURE_ROOT = DATA_ROOT / "features"

SPLITS = ["train", "val", "test"]
LABELS = ["mono", "poly"]

# =========================
# CREATE OUTPUT FOLDERS
# =========================
for split in SPLITS:
    for label in LABELS:
        (FEATURE_ROOT / split / label).mkdir(parents=True, exist_ok=True)

# =========================
# FEATURE FUNCTION
# =========================
def extract_logmel(wav_path):
    y, sr = librosa.load(wav_path, sr=SR, mono=True)

    # Safety trim / pad
    target_len = int(SR * WINDOW_SEC)
    if len(y) < target_len:
        y = np.pad(y, (0, target_len - len(y)))
    else:
        y = y[:target_len]

    mel = librosa.feature.melspectrogram(
        y=y,
        sr=SR,
        n_fft=N_FFT,
        hop_length=HOP,
        n_mels=N_MELS,
        power=2.0
    )

    logmel = librosa.power_to_db(mel, ref=np.max)

    # Normalize (important!)
    logmel = (logmel - np.mean(logmel)) / (np.std(logmel) + 1e-6)

    return logmel.astype(np.float32)

# =========================
# PROCESS DATASETS
# =========================
def process_dataset(dataset_root, label_name):
    for split in SPLITS:
        audio_dir = dataset_root / split / label_name
        out_dir = FEATURE_ROOT / split / label_name

        files = list(audio_dir.glob("*.wav"))
        print(f"{label_name.upper()} | {split}: {len(files)} files")

        for wav in tqdm(files, desc=f"{label_name}-{split}"):
            try:
                feature = extract_logmel(wav)
                out_file = out_dir / (wav.stem + ".npy")
                np.save(out_file, feature)
            except Exception as e:
                print(f"Error: {wav.name} → {e}")

# =========================
# RUN
# =========================
print("\nExtracting MONO features...")
process_dataset(MONO_ROOT, "mono")

print("\nExtracting POLY features...")
process_dataset(POLY_ROOT, "poly")

print("\n✓ Log-Mel feature extraction completed.")
