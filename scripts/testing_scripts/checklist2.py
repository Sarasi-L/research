import os
import random
import librosa
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

from backend.services.monophonic.pitch_extraction import extract_pitch


# -------------------------------
# Dataset paths
# -------------------------------
DATASET_PATHS = {
    "NSynth (Monophonic)": r"D:\My Documents\SLIIT\DS4.1\Research Project\data\nsynth",
    "IRMAS (Polyphonic)": r"D:\My Documents\SLIIT\DS4.1\Research Project\data\IRMAS"
}

# -------------------------------
# Sampling size
# -------------------------------
SAMPLE_SIZE = 500   # change to 1000 if you want


# -------------------------------
# Extract pitch from sampled dataset
# -------------------------------
def extract_sampled_pitch(folder_path, dataset_name, sample_size):
    all_pitches = []

    # Collect all audio files (recursive)
    audio_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(('.wav', '.mp3')):
                audio_files.append(os.path.join(root, file))

    print(f"\n{dataset_name}: {len(audio_files)} total files found")

    # Random sampling
    random.shuffle(audio_files)
    sampled_files = audio_files[:sample_size]

    print(f"{dataset_name}: Using {len(sampled_files)} sampled files")

    for file_path in tqdm(sampled_files, desc=f"{dataset_name} (sampled)"):
        try:
            y, sr = librosa.load(file_path, sr=None, mono=True)

            _, frequency, confidence = extract_pitch(y, sr)

            valid_pitches = frequency[~np.isnan(frequency)]
            valid_pitches = valid_pitches[
                (valid_pitches > 50) & (valid_pitches < 2000)
            ]

            all_pitches.extend(valid_pitches.tolist())

        except Exception:
            continue

    return np.array(all_pitches)


# -------------------------------
# Run extraction
# -------------------------------
pitch_data = {}

for name, path in DATASET_PATHS.items():
    pitch_data[name] = extract_sampled_pitch(path, name, SAMPLE_SIZE)


# -------------------------------
# Plot: Pitch Distribution
# -------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for ax, (dataset, pitches) in zip(axes, pitch_data.items()):
    ax.hist(
        pitches,
        bins=60,
        density=True,
        edgecolor="black",
        alpha=0.85
    )
    ax.set_title(f"{dataset} Pitch Distribution")
    ax.set_xlabel("Pitch Frequency (Hz)")
    ax.set_ylabel("Density")
    ax.grid(alpha=0.3)

plt.suptitle(
    "Pitch Distribution Comparison Using Randomly Sampled Audio Files",
    fontsize=15
)
plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.show()
