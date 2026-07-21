import os
import librosa
import matplotlib.pyplot as plt
from tqdm import tqdm

# -------------------------------
# Dataset paths (update if needed)
# -------------------------------
DATASET_PATHS = {
    "nsynth": r"D:\My Documents\SLIIT\DS4.1\Research Project\data\nsynth",
    "IRMAS": r"D:\My Documents\SLIIT\DS4.1\Research Project\data\IRMAS",
    "FMA": r"D:\My Documents\SLIIT\DS4.1\Research Project\data\fma_small",
    "GTZAN": r"D:\My Documents\SLIIT\DS4.1\Research Project\data\GTZAN"
} 

# -------------------------------
# Function to extract durations
# -------------------------------
def extract_durations(folder_path, dataset_name):
    durations = []

    audio_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(('.wav', '.mp3')):
                audio_files.append(os.path.join(root, file))

    print(f"\nProcessing {dataset_name}: {len(audio_files)} files")

    for file_path in tqdm(audio_files, desc=dataset_name):
        try:
            y, sr = librosa.load(file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            durations.append(duration)
        except:
            continue

    return durations

# -------------------------------
# Extract durations
# -------------------------------
all_durations = {}
for name, path in DATASET_PATHS.items():
    all_durations[name] = extract_durations(path, name)

# -------------------------------
# Plot: 4 datasets in 1 figure
# -------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for ax, (dataset, durations) in zip(axes, all_durations.items()):
    ax.hist(
        durations,
        bins=30,
        density=True,
        edgecolor="black",
        alpha=0.8
    )
    ax.set_title(f"{dataset} Duration Distribution")
    ax.set_xlabel("Audio Duration (seconds)")
    ax.set_ylabel("Density")
    ax.grid(alpha=0.3)

plt.suptitle("Audio Duration Distribution Across Music Datasets", fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()
