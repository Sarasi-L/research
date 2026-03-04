import os
import random
import librosa
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

# --------------------------------
# Dataset paths (your actual paths)
# --------------------------------
DATASET_PATHS = {
    "Mono (NSynth)": r"D:\My Documents\SLIIT\DS4.1\Research Project\data\nsynth",
    "Poly (IRMAS)": r"D:\My Documents\SLIIT\DS4.1\Research Project\data\IRMAS"
}

SAMPLE_SIZE = 80   # 50–100 is ideal for t-SNE

# --------------------------------
# Feature extraction (MFCC stats)
# --------------------------------
def extract_mfcc_features(file_path):
    y, sr = librosa.load(file_path, sr=22050, mono=True, duration=10)

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    mfcc_mean = np.mean(mfcc, axis=1)
    mfcc_std = np.std(mfcc, axis=1)

    return np.concatenate([mfcc_mean, mfcc_std])


# --------------------------------
# Load and sample dataset
# --------------------------------
features = []
labels = []

for label, folder in DATASET_PATHS.items():
    audio_files = []

    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(('.wav', '.mp3')):
                audio_files.append(os.path.join(root, file))

    random.shuffle(audio_files)
    sampled_files = audio_files[:SAMPLE_SIZE]

    print(f"{label}: using {len(sampled_files)} files")

    for file_path in tqdm(sampled_files, desc=label):
        try:
            feat = extract_mfcc_features(file_path)
            features.append(feat)
            labels.append(label)
        except:
            continue

X = np.array(features)
y = np.array(labels)

# --------------------------------
# Feature scaling
# --------------------------------
X = StandardScaler().fit_transform(X)

# --------------------------------
# t-SNE
# --------------------------------
tsne = TSNE(
    n_components=2,
    perplexity=30,
    learning_rate=200,
    random_state=42
)

X_tsne = tsne.fit_transform(X)

# --------------------------------
# Plot
# --------------------------------
plt.figure(figsize=(8, 6))

for label in np.unique(y):
    idx = y == label
    plt.scatter(
        X_tsne[idx, 0],
        X_tsne[idx, 1],
        label=label,
        alpha=0.75
    )

plt.title("t-SNE Embedding of Audio Features (Mono vs Polyphonic)")
plt.xlabel("t-SNE Dimension 1")
plt.ylabel("t-SNE Dimension 2")
plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()
plt.show()
